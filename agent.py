from data_utils import *
from rdflib import Graph, RDF, OWL

import random

class Agent:
	def __init__(self, ID, graph_path, namespace=None):

		self.properties_frequency = None
		self.graph = Graph()
		self.graph.parse(graph_path)

		self.agent_ID = ID
		self.namespace = namespace

	def reset_fca_datastructures(self):
		self.concept_fca_structure = None
		self.used_characteristics_FCA_relations = None
		self.concept_FCA_relations = None

	def get_positive_property_set_IDs_that_include_property(self, property, exact_match=True):
		'''
		this function returns all concept IDs that contain at least this characteristic
		:param property:
		:return: set of concept IDs
		'''
		filtered_concept_IDs = set()
		characteristic_frozenset = frozenset({property})
		for concept in self.positive_property_set_to_its_ID:
			if (exact_match and characteristic_frozenset == concept) or (exact_match == False and property in set(concept)):
				filtered_concept_IDs.add(self.positive_property_set_to_its_ID[concept])
		return filtered_concept_IDs


	def get_all_named_individuals(self):
		return set(self.graph.subjects(RDF.type, OWL.NamedIndividual))


# -------------------- Agent Introspection Functions (Preparing groups of objects and Concepts, etc.)

	def prepare_groups_and_concepts(self, common_objects=None):
		# Characteristics are a set of Boolean (True) properties that describe an object
		# We want to know, and be able to identify, existing combinations of characteristics (in objects)
		self.object_group_ID_to_object_properties = {}
		self.object_properties_to_object_group_ID = {}
		# a dictionary mapping object symbols with the group ID that they fall under, w.r.t. the characteristics
		self.object_to_object_group_ID = {}
		# Objects are grouped together if they have exactly the same characteristics
		self.object_properties_to_objects = defaultdict(set)
		# The above 4 dictionaries are filled by the next function
		if common_objects is None:
			common_objects = self.get_all_named_individuals()
		self.calculate_groups_of_objects(common_objects)

		# concepts are composed using the same characteristics
		# concepts are more abstract than objects, and can be perceived as "Classes"
		self.positive_property_set_to_its_ID = {}
		self.ID_of_a_positive_property_set = {}
		# it is important to remember the comparison, of which groups' characteristics generated this concept
		# the following dictionary, has as values sets of tupples of group ID "(ID1, ID2)" ...
		# resembling the set operator : Set_of_characteristics_of_Group_1 - Set_of_characteristics_of_Group_2
		self.positive_property_set_ID_to_group_comparisons = defaultdict(set)
		self.comparison_to_concept_ID = {}
		self.calculate_all_positive_property_sets()


	def get_all_used_properties(self, return_set=False):
		all_used_characteristics = list()
		for group_ID in self.object_group_ID_to_object_properties:
			group_characteristics = self.object_group_ID_to_object_properties[group_ID]
			all_used_characteristics.append(group_characteristics)
		if return_set:
			all_used_characteristics = set(all_used_characteristics)
		return all_used_characteristics

	def get_object_properties(self, object, return_frozen_set=True):
		'''
		We calculate the object's characteristics and return the characteristics in a frozenset form
		The characteristics of an object are the classes that it is member of.
		:param object: the URI of an object
		:param return_frozen_set: whether to return a set or type cast it to frozen set
		:return: a (frozen)set with the boolean characteristics of the object
		'''
		object_properties = set()
		for _, _, class_URI in self.graph.triples((object, RDF.type, None)):
			object_properties.add(class_URI)
		if return_frozen_set:
			# typecasting from "set" to hashable type "frozenset"
			return frozenset(object_properties)
		else:
			return object_properties

	def calculate_groups_of_objects(self, objects=None):
		# if not specified, divide all sharable objects into groups
		if objects is None:
			objects = self.get_all_named_individuals()

		self.properties_frequency = defaultdict(int)

		# we "read" the properties of every object and then group objects according to their properties
		for object in objects:
			# retrieve its properties
			objects_properties = self.get_object_properties(object)
			for object_property in set(objects_properties):
				self.properties_frequency[object_property] += 1
			# retrieve the group ID of this set
			if objects_properties in self.object_properties_to_object_group_ID:
				object_group_ID = self.object_properties_to_object_group_ID[objects_properties]
			else:
				object_group_ID = len(self.object_properties_to_object_group_ID)
				# register the new set, and its ID
				self.object_properties_to_object_group_ID[objects_properties] = object_group_ID
				self.object_group_ID_to_object_properties[object_group_ID] = objects_properties

			self.object_properties_to_objects[objects_properties].add(object)
			self.object_to_object_group_ID[object] = object_group_ID


	def calculate_all_positive_property_sets(self):
		'''
			positive property sets are defined based on comparing properties of the objects from different object groups
			Therefore, positive property sets are expected to be more than groups
			(since they are calculated based on their combinations)
		'''

		object_group_IDs = self.object_group_ID_to_object_properties.keys()
		# For all pairwise combinations of groups
		for object_group_ID_A in object_group_IDs:
			for object_group_ID_B in object_group_IDs:

				# we do not want to compare the same group with itself (as it will always produce an empty set)
				if object_group_ID_A == object_group_ID_B:
					continue

				properties_of_group_A = self.object_group_ID_to_object_properties[object_group_ID_A]
				properties_of_group_B = self.object_group_ID_to_object_properties[object_group_ID_B]

				# typecasting from "frozenset" to "set", so that Set operators can be applied
				properties_of_group_A = set(properties_of_group_A)
				properties_of_group_B = set(properties_of_group_B)

				positive_property_set_of_object_group_comparison = properties_of_group_A - properties_of_group_B

				# we don't care about concepts without any characteristics
				if len(positive_property_set_of_object_group_comparison) == 0:
					continue

				# typecasting from "set" to hashable type "frozenset"
				positive_property_set_of_object_group_comparison = frozenset(positive_property_set_of_object_group_comparison)

				# retrieve the ID of this concept
				if positive_property_set_of_object_group_comparison in self.positive_property_set_to_its_ID:
					positive_property_set_ID = self.positive_property_set_to_its_ID[positive_property_set_of_object_group_comparison]
				else:
					positive_property_set_ID = len(self.positive_property_set_to_its_ID)
					# register the new set, and its ID
					self.positive_property_set_to_its_ID[positive_property_set_of_object_group_comparison] = positive_property_set_ID
					self.ID_of_a_positive_property_set[positive_property_set_ID] = positive_property_set_of_object_group_comparison

				# adding the comparison that can lead to this positive property set ID ...
				# in a set with other comparisons of object groups that result to the same positive property set
				self.positive_property_set_ID_to_group_comparisons[positive_property_set_ID].add((object_group_ID_A, object_group_ID_B))
				# and vise versa
				self.comparison_to_concept_ID[(object_group_ID_A, object_group_ID_B)] = positive_property_set_ID

	def get_positive_property_set_IDs_from_powerset_of_positive_property_set(self, positive_property_set_ID):
		positive_property_set = set(self.ID_of_a_positive_property_set[positive_property_set_ID])
		powerset_of_positive_property_set = powerset(positive_property_set)
		positive_property_powerset_IDs = set()
		for properties_set in powerset_of_positive_property_set:
			frozen_properties_set = frozenset(properties_set)
			if frozen_properties_set in self.positive_property_set_to_its_ID:
				positive_powerset_element_ID = self.positive_property_set_to_its_ID[frozen_properties_set]
				positive_property_powerset_IDs.add(positive_powerset_element_ID)
		return positive_property_powerset_IDs

# -------- Teacher Student experiments

# --------  Initialization Functions

	def prepare_for_understanding_games(self, instance_mapping_dict):
		self.instance_mapping_dict = instance_mapping_dict
		common_instance_set = set(instance_mapping_dict.keys())
		self.prepare_groups_and_concepts(common_objects=common_instance_set)

# --------- Util Functions
	def translate_URIs_for_other_agent(self, URI_set):
		'''
		:param URI_set: a set of URIs as they appear in this agent's ontology
		:return: and URI (sub) set with the translated URIs of the same instances as they appear on the other agent's ontology
		'''
		translated_URIs = set()
		for URI in URI_set:
			if URI in self.instance_mapping_dict:
				translated_URIs.add(self.instance_mapping_dict[URI])
		return translated_URIs

# --------- Teacher Functions

	def reset_as_teacher(self, query_property, teacher_policy):
		teacher_policy_accepted_values = ["random", "property-based"]

		if teacher_policy.lower() not in teacher_policy_accepted_values:
			raise ValueError("Wrong teacher policy provided: " + teacher_policy)

		self.teacher_policy = teacher_policy
		self.unclear_episodes = set()

		self.related_positive_property_set_IDs = self.get_positive_property_set_IDs_that_include_property(query_property, exact_match=False)

		self.example_pool = list()
		self.example_probabilities = list()
		# self.example_indices = list()

		self.semantic_memory_variables = []
		self.episodic_memory_variables = []

		# prepare data structure to save unclear examples
		self.episodic_memory_variables.append(self.unclear_episodes)

		# populate the example pool for this particular query / property
		for positive_property_set_ID in self.related_positive_property_set_IDs:

			for (relevant_object_group_ID, irrelevant_object_group_ID) in self.positive_property_set_ID_to_group_comparisons[positive_property_set_ID]:

				relevant_objects = self.object_properties_to_objects[self.object_group_ID_to_object_properties[relevant_object_group_ID]]
				irrelevant_objects = self.object_properties_to_objects[self.object_group_ID_to_object_properties[irrelevant_object_group_ID]]

				if self.teacher_policy == "property-based":

					# retrieving characteristics of group objects
					relevant_object_properties = set(self.object_group_ID_to_object_properties[relevant_object_group_ID])
					irrelevant_object_properties = set(self.object_group_ID_to_object_properties[irrelevant_object_group_ID])
					# calculating the overlap between the query property and the positive characteristics of the examples that these groups can generate
					positive_property_set = relevant_object_properties - irrelevant_object_properties

					# misguiding properties of an example are the ones that are in its positive property set, but are not the query property
					misguiding_positive_properties = positive_property_set - {query_property}
					example_misinterpretation_prob_sum = 0
					for misguiding_property in misguiding_positive_properties:
						# probability of each property is equal to the number of objects that have it, against all objects (referring to common objects in both cases)
						example_misinterpretation_prob_sum += self.properties_frequency[misguiding_property] / len(self.instance_mapping_dict)

					# calculating the sum of probabilities of the negative
					negative_property_set = irrelevant_object_properties - relevant_object_properties
					common_property_set = irrelevant_object_properties.intersection(relevant_object_properties)
					
					concept_excluding_characteristics = negative_property_set.union(common_property_set)
					example_excluding_char_prob_sum = 0
					for misguiding_property in concept_excluding_characteristics:
						# probability of each property is equal to the number of objects that have it, against all objects (referring to common objects in both cases)
						example_excluding_char_prob_sum += self.properties_frequency[misguiding_property] / len(self.instance_mapping_dict)

					# the scores of all these examples that have consist of an
					example_scores = example_excluding_char_prob_sum - example_misinterpretation_prob_sum

					# all instances with negative score, are treated equally in terms of query result order
					if example_scores <= 0:
						example_scores = 0.01
				else:
					example_scores = 1

				for relevant_object in relevant_objects:
					for irrelevant_object in irrelevant_objects:
						example = (relevant_object, irrelevant_object)
						self.example_pool.append(example)
						self.example_probabilities.append(example_scores)

		# if we cannot construct any examples for this query, then we report that the teacher cannot initiate this experiment
		total_examples = len(self.example_pool)
		if total_examples == 0:
			return False
		# normalise example probabilities
		weighted_sum = sum(self.example_probabilities)
		self.example_probabilities = [weight / weighted_sum for weight in self.example_probabilities]
		return True

	def select_next_teaching_example(self):
		# if there are no more examples the Teacher can give, we return None to signal it
		if len(self.example_pool) == 0:
			return None

		example_indices = list(range(len(self.example_pool)))
		example_index = random.choices(population=example_indices, weights=self.example_probabilities)[0]

		example = self.example_pool[example_index]

		self.teaching_example_episode_memory = dict()
		self.teaching_example_episode_memory["example_index"] = example_index
		self.teaching_example_episode_memory["example"] = example

		# translating the example by using the URIs of the other agent to refer to the same instances - world objects.
		translated_example = (self.instance_mapping_dict[example[0]], self.instance_mapping_dict[example[1]])

		return translated_example

	# 	run the example by the student
	def comprehend_students_response_on_example(self, successfully_comprehended):
		# The teacher's policy dictates the agent to memorise failed examples so that they are not used in the future,
		# So, we save then in the memory, (increasing the episodic memory size)
		if successfully_comprehended == False:
			example = self.teaching_example_episode_memory["example"]
			example_index = self.teaching_example_episode_memory["example_index"]
			# remove this example and its score from the pool of examples
			del self.example_pool[example_index]
			del self.example_probabilities[example_index]
			# "memorize" the unclear example
			self.unclear_episodes.add(example)

			# re-normalising probabilities
			weighted_sum = sum(self.example_probabilities)
			self.example_probabilities = [weight / weighted_sum for weight in self.example_probabilities]

	# -------- Student Functions :
	def reset_as_student(self, student_policy):
		self.student_policy = student_policy.lower()

		if self.student_policy == "frequency-based":
			self.property_scores = defaultdict(int)
			self.episodic_memory_variables = []
			self.semantic_memory_variables = [self.property_scores]
		elif self.student_policy == "logic-based":
			self.query_pseudo_symbol = "fca_property_pseudo_symbol"
			self.memorised_example_properties = set()
			self.episodic_memory_variables = [self.memorised_example_properties]
			self.semantic_memory_variables = []
		else:
			raise ValueError("Wrong 'student_policy' provided: " + student_policy)

	def learn_from_example(self, example):
		'''
		:param example: (relevant_object, irrelevant_object)
		:return: (Boolean) unclear example
		'''
		relevant_object, irrelevant_object = example

		relevant_object_properties = set(self.object_group_ID_to_object_properties[self.object_to_object_group_ID[relevant_object]])
		irrelevant_object_properties = set(self.object_group_ID_to_object_properties[self.object_to_object_group_ID[irrelevant_object]])

		example_positive_property_set = relevant_object_properties - irrelevant_object_properties
		example_common_property_set = irrelevant_object_properties.intersection(relevant_object_properties)

		examples_is_unclear = len(example_positive_property_set) == 0

		if examples_is_unclear:
			return False

		if self.student_policy == "logic-based":
			self.memorised_example_properties.add(frozenset(example_positive_property_set))

		elif self.student_policy == "frequency-based":
			# increase the score of each property in the properties to reinforce (positive property set of example)
			for property_to_reinforce in example_positive_property_set:
				self.property_scores[property_to_reinforce] += 1
			# decrease the score of each property in the properties to weaken (common property set of example)
			for property_to_weaken in example_common_property_set:
				self.property_scores[property_to_weaken] -= 1

		return True


	def get_student_query_results(self):

		if self.student_policy == "logic-based":
			query_interpretation_char_weights = self.infer_query_interpretation_from_episodes_using_fca()
		else:
			query_interpretation_char_weights = self.get_current_freq_query_interpretation()

		query_results = self.execute_query(query_interpretation_char_weights)

		return query_results

	def execute_query(self, query_interpretation_char_weights):
		'''
		:param query_interpretation_char_weights: a dictionary of property-weight pairs.
		:return: an ordered list of query results
		'''

		query_interpretation_properties_with_positive_weights = set()
		for group_property in query_interpretation_char_weights:
			if query_interpretation_char_weights[group_property] > 0:
				query_interpretation_properties_with_positive_weights.add(group_property)

		query_interpretation_properties_with_positive_weights = {URIRef(some_property) for some_property in query_interpretation_properties_with_positive_weights}

		#  we gather all object groups, the properties of which are a subset of the interpretation properties,
		#  and then we rank groups' objects according to the scores.
		object_group_IDs_and_scores = []
		for object_group_ID in self.object_group_ID_to_object_properties:
			group_properties = set(self.object_group_ID_to_object_properties[object_group_ID])

			if len(query_interpretation_properties_with_positive_weights.intersection(group_properties)) != 0:
				object_group_score = 0
				for group_property in group_properties:
					if group_property in query_interpretation_char_weights:
						object_group_score += query_interpretation_char_weights[group_property]
				# return objects from all related groups
				object_group_IDs_and_scores.append((object_group_ID, object_group_score))

		# get candidate groups in ranked descending order, according to matching score with interpretation
		ranked_candidate_groups = sorted(object_group_IDs_and_scores, key=lambda x: x[1], reverse=True)
		ranked_candidate_objects = []
		for object_group_ID, _ in ranked_candidate_groups:
			group_properties = self.object_group_ID_to_object_properties[object_group_ID]
			ranked_candidate_objects += self.object_properties_to_objects[group_properties]

		return ranked_candidate_objects

# ------------------------ Using frequency of properties method to infer symbol interpretation
	def get_current_freq_query_interpretation(self):
		query_interpretation_char_weights = dict()
		for some_property in self.property_scores:
			property_weight = self.property_scores[some_property]
			query_interpretation_char_weights[some_property] = property_weight

		return query_interpretation_char_weights

# ------------------------ Using FCA to infer symbol interpretation
	def infer_query_interpretation_from_episodes_using_fca(self):

		if len(self.memorised_example_properties) == 0:
			return {}

		memorized_properties_per_example = []
		memorized_properties_per_example.append({"padded_property"})
		for example_properties_frozen_set in self.memorised_example_properties:
			example_properties_set = set(example_properties_frozen_set).copy()
			example_properties_set.add(self.query_pseudo_symbol)
			memorized_properties_per_example.append(example_properties_set)

		episodic_fca_structure_of_chars = create_fca_structure(memorized_properties_per_example, is_list=True)

		query_interpretation_char_weights = utilise_fca_induced_relations_to_query_representation(
			episodic_fca_structure_of_chars, query_pseudo_symbol=self.query_pseudo_symbol, padded_property="padded_property")

		if self.query_pseudo_symbol in query_interpretation_char_weights:
			del query_interpretation_char_weights[self.query_pseudo_symbol]

		return query_interpretation_char_weights

	# ------------------ Memory Use Evaluation Functions :

	def get_semantic_memory_size(self):
		semantic_memory_variables = 0
		for var in self.semantic_memory_variables:
			if isinstance(var, dict):
				for key in var:
					if isinstance(var[key], (dict, list)):
						semantic_memory_variables += len(var[key])
					else:
						semantic_memory_variables += 1
			elif isinstance(var, (list, set)):
				semantic_memory_variables += len(var)
			else:
				semantic_memory_variables += 1
		return semantic_memory_variables

	def get_episodic_memory_size(self):
		num_memorised_episodes = 0
		for var in self.episodic_memory_variables:
			if isinstance(var, (list, set)):
				num_memorised_episodes += len(var)
			elif isinstance(var, dict):
				for key in var:
					if isinstance(var[key], (dict, list, set)):
						num_memorised_episodes += len(var[key])
					else:
						num_memorised_episodes += 1
		return num_memorised_episodes
