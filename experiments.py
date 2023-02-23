from experiment_utils import *
import datetime
from tensorboardX import SummaryWriter
import pickle
import os
# from agents import Agent
import shutil

def evaluate_students_understanding(student_agent, gt_results):
	query_results = student_agent.get_student_query_results()

	query_results_set = set(query_results)
	# evaluate results with GT results
	if len(query_results_set) != 0:
		precision = len(gt_results.intersection(query_results_set)) / len(query_results_set)
	else:
		precision = 0
	recall = len(gt_results.intersection(query_results_set)) / len(gt_results)
	return precision, recall, len(query_results_set)

def teacher_student_one_query_one_interaction_cycle(teacher_agent, student_agent, gt_results_set, steps):
	episode_generation_deadend = False
	for step in range(steps):
		teachers_output = teacher_agent.select_next_teaching_example()
		if teachers_output is None:
			episode_generation_deadend = True
			break
		example = teachers_output
		example_was_clear = student_agent.learn_from_example(example)
		teacher_agent.comprehend_students_response_on_example(example_was_clear)

	precision, recall, query_result_size = evaluate_students_understanding(student_agent, gt_results_set)

	return step+1, precision, recall, query_result_size, episode_generation_deadend


def teacher_student_one_query_experiment(teacher_agent, student_agent, teacher_policy, student_policy,
										 teacher_property, student_property, max_steps, eval_every, output_dict_step_wise):
	'''
	Here, one selected agent is trying to query something specific (one query) from another agent.
	The evaluation should take place on the query results in traditional IR terms.
	'''

	# get Ground Truth results, by querying the student with the correct translation
	gt_student_query_results = set()
	for correct_result in student_agent.graph.subjects(RDF.type, URIRef(student_property)):
		gt_student_query_results.add(correct_result)
	num_gt_results = len(gt_student_query_results)

	teacher_query_results = set()
	for correct_result in teacher_agent.graph.subjects(RDF.type, URIRef(teacher_property)):
		teacher_query_results.add(correct_result)
	num_teacher_results = len(teacher_query_results)

	teacher_translated_answer_URIs = teacher_agent.translate_URIs_for_other_agent(teacher_query_results)

	common_results = teacher_translated_answer_URIs.intersection(gt_student_query_results)
	num_joint_results = len(common_results)

	# init teacher and student
	successful_setup = teacher_agent.reset_as_teacher(query_property=teacher_property,
													  teacher_policy=teacher_policy)

	if successful_setup and num_gt_results == 0:
		# print("Query:", teacher_property, "was captured by teacher's concepts, but student has not results!", student_property)
		outcome_dict = {"completed": False, "fail_reason": "Student has no GT query results."}
		outcome_dict["num_gt_results"] = num_gt_results
		outcome_dict["num_teacher_results"] = num_teacher_results
		outcome_dict["num_joint_results"] = num_joint_results
		return outcome_dict, output_dict_step_wise
	elif not successful_setup:
		outcome_dict = {"completed": False, "fail_reason": "Teacher failed to find relevant examples."}
		outcome_dict["num_gt_results"] = num_gt_results
		outcome_dict["num_teacher_results"] = num_teacher_results
		outcome_dict["num_joint_results"] = num_joint_results
		return outcome_dict, output_dict_step_wise

	student_agent.reset_as_student(student_policy=student_policy)

	# query_symbol = teacher_agent.characteristic_to_symbol[teacher_property]

	total_steps = 0
	precision = 0
	recall = 0
	tensorboard_recording_step = 0
	episode_generation_deadend = False

	query_result_size = 0
	teachers_ep_mem_size = 0
	students_ep_mem_size = 0
	teachers_sem_mem_size = 0
	students_sem_mem_size = 0

	while(tensorboard_recording_step < max_steps):
		tensorboard_recording_step += eval_every

		# if the experiment still goes on, we continue to execute it normally
		if not((precision == 1 and recall == 1) or episode_generation_deadend):
			step, precision, recall, query_result_size, episode_generation_deadend = \
				teacher_student_one_query_one_interaction_cycle(teacher_agent, student_agent,
																gt_student_query_results, steps=eval_every)
			teachers_ep_mem_size = teacher_agent.get_episodic_memory_size()
			students_ep_mem_size = student_agent.get_episodic_memory_size()
			teachers_sem_mem_size = teacher_agent.get_semantic_memory_size()
			students_sem_mem_size = student_agent.get_semantic_memory_size()
			output_dict_step_wise["0.running"][tensorboard_recording_step].append(True)
			total_steps += step
		else:
			output_dict_step_wise["0.running"][tensorboard_recording_step].append(False)


		# either if the experiment still goes on, or simply if we have the last recorded values, we still record them for tensorboard.
		output_dict_step_wise["1.precision"][tensorboard_recording_step].append(precision)
		output_dict_step_wise["2.recall"][tensorboard_recording_step].append(recall)
		output_dict_step_wise["3.query_result_size"][tensorboard_recording_step].append(query_result_size)
		output_dict_step_wise["4.teachers_ep_mem_size"][tensorboard_recording_step].append(teachers_ep_mem_size)
		output_dict_step_wise["5.students_ep_mem_size"][tensorboard_recording_step].append(students_ep_mem_size)
		output_dict_step_wise["6.teachers_sem_mem_size"][tensorboard_recording_step].append(teachers_sem_mem_size)
		output_dict_step_wise["7.students_sem_mem_size"][tensorboard_recording_step].append(students_sem_mem_size)


	outcome_dict={}
	outcome_dict["completed"] = True
	outcome_dict["precision"] = precision
	outcome_dict["recall"] = recall
	outcome_dict["total_steps"] = total_steps
	outcome_dict["episode_generation_deadend"] = int(episode_generation_deadend)
	outcome_dict["query_result_size"] = query_result_size
	outcome_dict["num_gt_results"] = num_gt_results
	outcome_dict["num_teacher_results"] = num_teacher_results
	outcome_dict["num_joint_results"] = num_joint_results
	outcome_dict["teachers_ep_mem_size"] = teacher_agent.get_episodic_memory_size()
	outcome_dict["students_ep_mem_size"] = student_agent.get_episodic_memory_size()
	outcome_dict["teachers_sem_mem_size"] = teacher_agent.get_semantic_memory_size()
	outcome_dict["students_sem_mem_size"] = student_agent.get_semantic_memory_size()

	return outcome_dict, output_dict_step_wise




def try_many_queries_separately_among_two_agents(args, ont_prefixes, query_mappings, teacher_policy, student_policy, exp_dir, complete_experiment_output_dict_step_wise):
	statistics = defaultdict(dict)
	agent_1_prefix = ont_prefixes[0]
	agent_2_prefix = ont_prefixes[1]
	agent_1_teacher_key = "teacher_" + agent_1_prefix
	agent_2_teacher_key = "teacher_" + agent_2_prefix

	ontology_pair_start_t = datetime.datetime.now()

	# preprocess and initialize agents
	agent_1 = Agent(agent_1_prefix, os.path.join(args.dataset_dir + "/" + args.data_directory, agent_1_prefix + ".owl"))
	agent_2 = Agent(agent_2_prefix, os.path.join(args.dataset_dir + "/" + args.data_directory, agent_2_prefix + ".owl"))

	# read common instance alignments
	if args.common_instances == "simple":
		common_URIs = get_common_objects([agent_1, agent_2])
		ontology_1_to_ontology_2_instance_mapping_dict = {URI: URI for URI in common_URIs}
		ontology_2_to_ontology_1_instance_mapping_dict = ontology_1_to_ontology_2_instance_mapping_dict
	elif args.common_instances == "extended":
		ontology_1_to_ontology_2_instance_mapping_dict = dict()
		ontology_2_to_ontology_1_instance_mapping_dict = dict()
		for line in open(args.dataset_dir + "/" + args.instance_alignments_dir + "/" + agent_1_prefix + "-" + agent_2_prefix + ".csv", "r"):
			URI_1, URI_2 = line[:-1].split(",")
			URI_1, URI_2 = URIRef(URI_1), URIRef(URI_2)
			ontology_1_to_ontology_2_instance_mapping_dict[URI_1] = URI_2
			ontology_2_to_ontology_1_instance_mapping_dict[URI_2] = URI_1
	else:
		raise ValueError("argument --common_instances, got wrong value:" + args.common_instances)

	# save instance mapping dictionary, initialize groups and concept vocabulary
	agent_1.prepare_for_understanding_games(ontology_1_to_ontology_2_instance_mapping_dict)
	agent_2.prepare_for_understanding_games(ontology_2_to_ontology_1_instance_mapping_dict)

	ontology_pair_output_dict_step_wise = defaultdict(lambda: defaultdict(list))

	# execute query experiments:
	for q in range(len(query_mappings)):
		agents = [agent_1, agent_2]
		agent_teacher_keys = [agent_1_teacher_key, agent_2_teacher_key]
		query_mapping = query_mappings[q]

		for i in range(len(agents)):
			teacher_index = i
			student_index = (i + 1) % 2
			teacher_agent = agents[teacher_index]
			student_agent = agents[student_index]
			query = query_mapping[teacher_index]
			query_translation = query_mapping[student_index]
			query_pair = (query,query_translation)
			agent_teacher_key = agent_teacher_keys[teacher_index]

			statistics[agent_teacher_key][query_pair] = defaultdict(list)

			for iteration in range(args.repetitions):
				outcome_dict, ontology_pair_output_dict_step_wise = teacher_student_one_query_experiment(teacher_agent, student_agent,
																										 teacher_policy, student_policy, URIRef(query),
																										 URIRef(query_translation), args.max_steps,
																										 args.eval_every, ontology_pair_output_dict_step_wise)

				statistics[agent_teacher_key][query_pair]["completed"].append(outcome_dict["completed"])
				statistics[agent_teacher_key][query_pair]["num_gt_results"] = outcome_dict["num_gt_results"]
				statistics[agent_teacher_key][query_pair]["num_teacher_results"] = outcome_dict["num_teacher_results"]
				statistics[agent_teacher_key][query_pair]["num_joint_results"] = outcome_dict["num_joint_results"]

				if outcome_dict["completed"]:
					keys_to_append_list = ["precision", "recall", "total_steps", "episode_generation_deadend", "query_result_size",
										   "teachers_ep_mem_size", "students_ep_mem_size", "teachers_sem_mem_size", "students_sem_mem_size"]
					append_to_list_from_one_dictionary_to_other(source_dict=outcome_dict, target_dict=statistics[agent_teacher_key][query_pair],
														keys_to_append_list=keys_to_append_list)
					prefect_score = int((outcome_dict["precision"] == 1) and (outcome_dict["recall"] == 1))
					statistics[agent_teacher_key][query_pair]["perfect_score"].append(prefect_score)
				else:
					statistics[agent_teacher_key][query_pair]["fail_reason"].append(outcome_dict["fail_reason"])

	# aggregate and structure query results
	ont_pair_statistics = defaultdict(list)
	detailed_statistics_str_descriptions = []
	# we save all unsuccessful queries (where the teacher couldn't come up with not even one example) in a list to print them all together at the end
	unsuccessful_queries = []
	for (query_1, query_1_translation) in query_mappings:
		agent_teacher_keys = [agent_1_teacher_key, agent_2_teacher_key]
		queries = [query_1, query_1_translation]

		for i in range(len(agent_teacher_keys)):
			teacher_index = i
			student_index = (i + 1) % 2
			agent_teacher_key = agent_teacher_keys[teacher_index]
			query = queries[teacher_index]
			query_translation = queries[student_index]
			query_pair = (query, query_translation)

			av_stats_dict, std_stats_dict = aggregate_statistics_of_dictionary_of_list_of_values(statistics[agent_teacher_key][query_pair])

			query_description_str = "Query: " + query + " (" + str(av_stats_dict["num_teacher_results"])\
									+ "), -> " + query_translation +"(" + str(av_stats_dict["num_gt_results"]) \
									+ "), Common Results: " + str(av_stats_dict["num_joint_results"])

			# in case for some reason, the game was not successfully initiated for any of the iterations:
			# (if no experiment was executed successfully, then no statistics were appended for this teacher-query combination)
			if sum(statistics[agent_teacher_key][query_pair]["completed"]) == 0:
				unsuccessful_queries.append((query_description_str, av_stats_dict["fail_reason"][0]))
				ont_pair_statistics["completed"] += statistics[agent_teacher_key][query_pair]["completed"]
			else:
				keys_to_append_list = ["completed", "precision", "recall", "total_steps", "query_result_size", "episode_generation_deadend",
									   "perfect_score", "teachers_ep_mem_size", "students_ep_mem_size", "teachers_sem_mem_size", "students_sem_mem_size"]
				append_to_list_from_one_dictionary_to_other(source_dict=statistics[agent_teacher_key][query_pair], target_dict=ont_pair_statistics,
															keys_to_append_list=keys_to_append_list)
				detailed_statistics_str_descriptions.append(query_description_str)
				detailed_statistics_str_descriptions.append(format_average_query_performance_in_str(av_stats_dict, std_stats_dict, is_single_query=True))

	tensorboard_writer_ontology_pair_experiment_dir = os.path.join(exp_dir, "-".join(ont_prefixes))
	os.mkdir(tensorboard_writer_ontology_pair_experiment_dir)
	ontology_pair_tensorboard_writer = SummaryWriter(log_dir=tensorboard_writer_ontology_pair_experiment_dir)

	# write to tensorboard while also update  complete_experiment_output_dict_step_wise  according to ontology_pair_output_dict_step_wise 9append values per key and per step.
	_, complete_experiment_output_dict_step_wise = write_average_query_performance_to_tensorboard(
		ontology_pair_tensorboard_writer, ontology_pair_output_dict_step_wise, args.max_steps, args.eval_every,
	other_dictionary_to_append=complete_experiment_output_dict_step_wise)

	# write results to file
	# aggregate and report results per agent-teacher_role and per query
	with open(os.path.join(exp_dir, "-".join(ont_prefixes) + ".txt"), "w") as ontology_pair_file:

		num_completed_query_experiments = int(len(detailed_statistics_str_descriptions)/2)

		text_for_ontology_pair_file = "Agent: " + agent_1_prefix +" (" + str(len(agent_1.get_all_named_individuals()))
		text_for_ontology_pair_file += "), Agent: " + agent_2_prefix +" (" + str(len(agent_2.get_all_named_individuals()))
		text_for_ontology_pair_file += "), Common: " + str(len(ontology_1_to_ontology_2_instance_mapping_dict)) + ", Query Pairs: " + str(len(query_mappings))
		text_for_ontology_pair_file += f" Completed Queries: {num_completed_query_experiments}, Unsuccessful Queries: {len(unsuccessful_queries)}"

		ontology_pair_file.write(text_for_ontology_pair_file + "\n")

		av_ont_pair_stats_dict, std_ont_pair_stats_dict = aggregate_statistics_of_dictionary_of_list_of_values(ont_pair_statistics)

		ontology_pair_file.write("Overall ontology pair performance over the completed query experiments:\n")
		ontology_pair_overall_performance_str = format_average_query_performance_in_str(av_ont_pair_stats_dict, std_ont_pair_stats_dict, is_single_query=False)
		ontology_pair_file.write(ontology_pair_overall_performance_str + "\n")

		with open(os.path.join(exp_dir, "0_Comparisons_Summary.txt"), "a") as complete_experiments_comparisons_file:
			complete_experiments_comparisons_file.write(text_for_ontology_pair_file + "\n" + ontology_pair_overall_performance_str + "\n\n")

		ontology_pair_end_t = datetime.datetime.now()
		ontology_pair_time_delta = ontology_pair_end_t - ontology_pair_start_t
		ontology_pair_minutes = ontology_pair_time_delta.total_seconds() / 60
		ontology_pair_file.write(f"Experiment duration: {ontology_pair_minutes:05.2} minutes.\n\n\n")

		# then report for each completed query experiment
		for i in range(num_completed_query_experiments):
			query_description_str = detailed_statistics_str_descriptions[i*2]
			query_results_str = detailed_statistics_str_descriptions[i*2 + 1]
			ontology_pair_file.write(query_description_str + "\n" + query_results_str + "\n\n")
			# print(query_description_str + "\n" + query_results_str + "\n")

		# finally, report for each unsuccessful experiment
		ontology_pair_file.write("\nUnsuccessful Queries:\n")
		for (query_description_str, fail_reason) in unsuccessful_queries:
			ontology_pair_file.write(query_description_str + "| Reason:" + fail_reason + "\n\n")
			# print(query_description_str + "| Reason:" + fail_reason + "\n")

	return ont_pair_statistics, complete_experiment_output_dict_step_wise

def run_all_teacher_student_combinations_using_gold_alignments(args):
	all_prefix_pairs = get_all_prefix_pairs()

	# prepare experiment directories and filenames
	if not os.path.isdir(args.exp_dir):
		os.mkdir(args.exp_dir)
	if len(all_prefix_pairs) == 21:
		experiment_name = "all_ontology_pairs__"
	else:
		experiment_name = "_".join(all_prefix_pairs) + "__"

	teacher_policy = args.teacher_policy
	student_policy = args.student_policy

	experiment_name += "TP=" + teacher_policy + "__SP=" + student_policy + "__"
	experiment_name += "reps=" + str(args.repetitions) + "__"
	experiment_name += "instances=" + args.common_instances + "__"
	experiment_name += "max_steps=" + str(args.max_steps)

	exp_dir = os.path.join(args.exp_dir, experiment_name)
	# 	if the directory exists already then we empty it
	if os.path.isdir(exp_dir):
		for file in os.listdir(exp_dir):
			path = os.path.join(exp_dir, file)
			if os.path.isfile(path):
				os.remove(path)
			else:
				shutil.rmtree(path)
	# otherwise, we just create it
	else:
		os.mkdir(exp_dir)


	print("Running experiment. Output will be saved in directory:", exp_dir)

	tensorboard_writer_average_experiment_dir = os.path.join(exp_dir, "average")
	os.mkdir(tensorboard_writer_average_experiment_dir)
	experiment_average_tensorboard_writer = SummaryWriter(log_dir=tensorboard_writer_average_experiment_dir)

	ontology_pair_performances_dict = defaultdict(list)
	# monitor experiment execution time per ontology pair.
	start_t = datetime.datetime.now()

	complete_experiment_output_dict_step_wise = defaultdict(lambda: defaultdict(list))

	for prefix_pair in all_prefix_pairs:
		prefix_pair_tuple = prefix_pair.split("-")
		equivalent_classes, equivalent_properties = load_ontology_alignments(ont_1_prefix=prefix_pair_tuple[0],
						 ont_2_prefix=prefix_pair_tuple[1], dir_path=args.dataset_dir + "/" + args.reference_alignments_dir)

		pair_ontology_performance, complete_experiment_output_dict_step_wise = try_many_queries_separately_among_two_agents(args, ont_prefixes=prefix_pair_tuple,
					query_mappings=equivalent_classes, teacher_policy=teacher_policy,	student_policy=student_policy,
										exp_dir=exp_dir, complete_experiment_output_dict_step_wise=complete_experiment_output_dict_step_wise)

		keys_to_append_list = ["completed", "precision", "recall", "total_steps", "query_result_size", "episode_generation_deadend",
							   "perfect_score", "teachers_ep_mem_size", "students_ep_mem_size", "teachers_sem_mem_size", "students_sem_mem_size"]
		append_to_list_from_one_dictionary_to_other(source_dict=pair_ontology_performance, target_dict=ontology_pair_performances_dict,
													keys_to_append_list=keys_to_append_list)


	end_t = datetime.datetime.now()
	time_delta = end_t - start_t
	minutes = time_delta.total_seconds() / 60

	av_performance_stats_dict, std_performance_stats_dict = aggregate_statistics_of_dictionary_of_list_of_values(ontology_pair_performances_dict)

	performance_summary_str = format_average_query_performance_in_str(av_performance_stats_dict, std_performance_stats_dict, is_single_query=False)

	average_values_per_step, _ = write_average_query_performance_to_tensorboard(experiment_average_tensorboard_writer, complete_experiment_output_dict_step_wise, args.max_steps, args.eval_every)

	with open(os.path.join(exp_dir, "0_Summary.txt"), "w") as complete_experiments_file:
		complete_experiments_file.write(performance_summary_str)
		complete_experiments_file.write(f"Experiment duration: {minutes:06.2} minutes.\n\n\n")

	with open(os.path.join(exp_dir,'av_stats_per_step_dict.pickle'), 'wb') as handle:
		pickle.dump(average_values_per_step, handle, protocol=pickle.HIGHEST_PROTOCOL)

	av_precision = av_performance_stats_dict["precision"]
	av_recall = av_performance_stats_dict["recall"]
	av_total_steps = av_performance_stats_dict["total_steps"]
	av_teacher_ep_mem = av_performance_stats_dict["teachers_ep_mem_size"]
	av_student_ep_mem = av_performance_stats_dict["students_ep_mem_size"]
	av_student_sem_mem = av_performance_stats_dict["students_sem_mem_size"]


	print(f"Task (Query) Performance Metrics:\nPrecision: {av_precision:04.2}, Recall: {av_recall:04.2}")
	print(f"Efficiency Metrics:\nInteraction time (#Examples): {av_total_steps:04.2}, Teacher Episodic Memory: {av_teacher_ep_mem:04.2}, Student Episodic Memory: {av_student_ep_mem:04.2}, Student Working Memory: {av_student_sem_mem:04.2}")


