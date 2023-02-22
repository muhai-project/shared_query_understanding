import os
import numpy as np
import pickle
from rdflib import Graph, RDF, URIRef, OWL
from collections import defaultdict
from itertools import chain, combinations
import concepts as fca




def ontology_prefix_to_namespace_str(prefix):
	if prefix == "cmt":
		return "http://cmt"
	elif prefix == "conference":
		return "http://conference"
	elif prefix == "edas":
		return "http://edas"
	elif prefix == "ekaw":
		return "http://ekaw"
	elif prefix == "iasted":
		return "http://iasted"
	elif prefix == "sigkdd":
		return "http://sigkdd"
	elif prefix == "confof":
		return "http://confOf"
	else:
		raise ValueError("Prefix is not mapped to a known namespace!")

def get_all_ontology_prefixes():
	return ["cmt", "conference", "edas", "ekaw", "iasted", "sigkdd", "confof"]

def concepts_library_symmetric_relations():
	return {"equivalent", "orthogonal", "incompatible", "subcontrary", "complement"}

def get_all_prefix_pairs():
	return ["cmt-conference", "cmt-confof", "cmt-edas", "cmt-ekaw", "cmt-iasted",
			 "cmt-sigkdd", "conference-confof", "conference-edas", "conference-ekaw",
			 "conference-iasted", "conference-sigkdd", "confof-edas", "confof-ekaw",
			 "confof-iasted", "confof-sigkdd", "edas-ekaw", "edas-iasted", "edas-sigkdd",
			 "ekaw-iasted", "ekaw-sigkdd", "iasted-sigkdd"]


def aggregate_statistics_of_dictionary_of_list_of_values(input_dict):
	av_dict = {}
	std_dict = {}
	for key in input_dict:
		object = input_dict[key]
		if isinstance(object, list) and isinstance(object[0], (int, float)):
			np_object = np.asarray(object)
			av_dict[key] = np.mean(np_object)
			std_dict[key] = np.std(np_object)
		else:
			av_dict[key] = object
	return av_dict, std_dict


def append_to_list_from_one_dictionary_to_other(source_dict, target_dict, keys_to_append_list=[]):
	for key in keys_to_append_list:
		# we make sure that we don't have lists of lists, but everything is kept in the same original 1-d list
		if isinstance(source_dict[key], list):
			target_dict[key] += source_dict[key]
		else:
			target_dict[key].append(source_dict[key])

def powerset(iterable):
	# this function is from https://stackoverflow.com/questions/1482308/how-to-get-all-subsets-of-a-set-powerset
	"powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"
	s = list(iterable)
	return chain.from_iterable(combinations(s, r) for r in range(len(s) + 1))


def create_fca_structure(objects_characteristics_dict, is_list=False, object_prefix=""):
	'''
	:param objects_characteristics_dict: a dictionary of objects (keys) and their characteristics (value is an iterable instance)
	:param is_list: A boolean indicating if objects_characteristics_dict is a list instead of a dictionary,
			in which case we don't cate about the object's names
	:return: a generated concepts (fca) instance
	'''
	# gather all existing characteristics to a set
	all_characteristics = set()
	for object in objects_characteristics_dict:
		if is_list:
			object_properties = object
		else:
			object_properties = objects_characteristics_dict[object]
			if isinstance(object_properties, frozenset):
				object_properties = set(object_properties)
		all_characteristics = all_characteristics.union(object_properties)

	# create property to index lookup table
	characteristic_to_index = {}
	characteristic_labels = []
	for i, characteristic in enumerate(all_characteristics):
		characteristic_to_index[characteristic] = i
		characteristic_labels.append(characteristic)

	# create final object's list and the boolean table
	bools = []
	objects = []
	false_boolean_characteristics_template = [False for _ in range(len(all_characteristics))]

	for i, object in enumerate(objects_characteristics_dict):
		if is_list:
			object_name = object_prefix + str(i)
			characteristics = object
		else:
			object_name = object_prefix + str(object)
			characteristics = objects_characteristics_dict[object]
		objects.append(object_name)

		if isinstance(characteristics, frozenset):
			characteristics = set(characteristics)

		boolean_characteristics = false_boolean_characteristics_template[:]
		for characteristic in characteristics:
			characteristic_index = characteristic_to_index[characteristic]
			boolean_characteristics[characteristic_index] = True
		bools.append(tuple(boolean_characteristics))

	fca_structure = fca.Context(objects, characteristic_labels, bools)

	return fca_structure

def get_fca_induced_relations(fca_structure, padded_property=None):
	'''
	This function get a fca structure, computes the relations between the attributes and returns them
	:param fca_structure: the provided fca structure
	:return:
	dictionary 1: same_namespace_relations. The dictionary keys are the relation type, values are lists that contains lists of 2 concepts
	dictionary 2: cross_namespace_relations. The dictionary keys are the relation type, values are lists that contains lists of 2 concepts
	set: all concepts that appear in the relations
	'''
	cross_namespace_relations = defaultdict(list)
	same_namespace_relations = defaultdict(list)
	all_involved_attributes = set()

	symbol_translation_dict = defaultdict(lambda: defaultdict(set))
	symmetric_relations = concepts_library_symmetric_relations()

	for i, relation in enumerate(fca_structure.relations()):
		attribute_A, relation_type, attribute_B = str(relation).split()
		# In some cases we have added an artificial property named padded_property, which we want to ignore
		# This is needed for inferring relations between object properties
		if padded_property is not None and (attribute_A == "padded_property" or attribute_B == "padded_property"):
			continue
		namespace_A = attribute_A.split("#")[0]
		namespace_B = attribute_B.split("#")[0]
		relation_tuple = (attribute_A, attribute_B)
		all_involved_attributes.update([attribute_A, attribute_B])
		symbol_translation_dict[attribute_A][relation_type].add(attribute_B)
		if relation_type in symmetric_relations:
			symbol_translation_dict[attribute_B][relation_type].add(attribute_A)
		# cross namespaces relations
		if namespace_A != namespace_B:
			cross_namespace_relations[relation_type].append(relation_tuple)
		else:
			same_namespace_relations[relation_type].append(relation_tuple)
	return same_namespace_relations, cross_namespace_relations, all_involved_attributes, symbol_translation_dict



def retrieve_all_related_symbols_recursively(symbol_translation_dict, current_symbol, relation_type, searched_symbols, symbols_to_further_search, related_symbols):
	searched_symbols.add(current_symbol)

	if relation_type not in symbol_translation_dict[current_symbol]:
		return related_symbols

	related_symbols.update(symbol_translation_dict[current_symbol][relation_type])
	symbols_to_further_search.update( symbol_translation_dict[current_symbol][relation_type] - searched_symbols )

	if len(symbols_to_further_search) == 0:
		return related_symbols

	next_symbol = symbols_to_further_search.pop()
	return retrieve_all_related_symbols_recursively(symbol_translation_dict, next_symbol, relation_type, searched_symbols, symbols_to_further_search, related_symbols)

def utilise_fca_induced_relations_to_query_representation(fca_structure, query_pseudo_symbol, padded_property=None):
	'''
	This function applies FCA on the episodic memory, in order to infer which characteristics are related to this query.
	Then, it provides a weight or score to each property, according to their relation with the query symbol.
	Finally, it returns a dictionary of property-weight values.
	'''

	# let's start by seeing in which relations the communication symbol is involved
	_, _, _, symbol_translation_dict = get_fca_induced_relations(fca_structure, padded_property=padded_property)

	# keys we will use: 	"incompatible", "implication", "subcontrary", "orthogonal", "equivalent"
	query_related_chars={}

	query_related_chars["equivalent"] = retrieve_all_related_symbols_recursively(symbol_translation_dict, current_symbol=query_pseudo_symbol,
				relation_type="equivalent", searched_symbols=set(), symbols_to_further_search=set(), related_symbols=set())

	query_related_chars["implication"] = retrieve_all_related_symbols_recursively(symbol_translation_dict, current_symbol=query_pseudo_symbol,
				relation_type="implication", searched_symbols=set(), symbols_to_further_search=query_related_chars["equivalent"], related_symbols=set())

	# if something looks like both equivalent and implied, then we keep the equivalent relationship
	query_related_chars["implication"] = query_related_chars["implication"] - query_related_chars["equivalent"]

	# provide scores to each interpreted property according to their relation type
	scores = {"equivalent": 10, "implication": 5}

	query_interpretation_char_weights = {}
	for relation_type in ["equivalent", "implication"]:
		if relation_type in query_related_chars:
			for related_property in query_related_chars[relation_type]:
				query_interpretation_char_weights[related_property] = scores[relation_type]

	return query_interpretation_char_weights

def load_ontology_alignments(ont_1_prefix, ont_2_prefix, dir_path):
	'''
	This function reads turtle files of GOLD aligned concepts across two ontologies, and returns two lists of tuples.
	The first one is with corresponding classes and the second one with corresponding properties.
	The first concept of each tuple, is from the ontology prefix that was provided as first argument when calling this function 'ont_1_prefix'
	'''
	alignments_rdflib_graph = Graph()
	file_path = os.path.join(dir_path, ont_1_prefix + "-" + ont_2_prefix + ".ttl")

	if not os.path.exists(file_path):
		file_path = os.path.join(dir_path, ont_2_prefix + "-" + ont_1_prefix + ".ttl")
		if not os.path.exists(file_path):
			raise ValueError("File containing alignments could not be found in:\n" + dir_path)

	alignments_rdflib_graph.parse(file_path, format="turtle")

	ont_1_namespace = ontology_prefix_to_namespace_str(ont_1_prefix)

	equivalent_classes = []
	equivalent_properties = []

	for subject, predicate, object in alignments_rdflib_graph:
		if predicate == OWL.equivalentClass:
			# if subject belongs to namespace of ontology 1
			if subject[:len(ont_1_namespace)] == ont_1_namespace:
				ont_1_class = str(subject)
				ont_2_class = str(object)
			else:
				ont_1_class = str(object)
				ont_2_class = str(subject)
			equivalent_classes.append((ont_1_class, ont_2_class))

		elif predicate == OWL.equivalentProperty:
			# if subject belongs to namespace of ontology 1
			if subject[:len(ont_1_namespace)] == ont_1_namespace:
				ont_1_property = str(subject)
				ont_2_property = str(object)
			else:
				ont_1_property = str(object)
				ont_2_property = str(subject)
			equivalent_properties.append((ont_1_property, ont_2_property))

	return equivalent_classes, equivalent_properties
