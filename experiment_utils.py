from agent import *

def	write_average_query_performance_to_tensorboard(tensorboard_writer, output_dict_step_wise, max_steps, step_size, other_dictionary_to_append=None):
	num_successful_experiments = max(len(output_dict_step_wise[key][step_size]) for key in output_dict_step_wise)

	average_values_per_step = defaultdict(dict)
	for key in output_dict_step_wise:
		step = step_size
		while step <= max_steps:
			average_value = sum(output_dict_step_wise[key][step]) / num_successful_experiments
			average_values_per_step[key][step] = average_value
			tensorboard_writer.add_scalar("Av_" + key, average_value, step)
			if other_dictionary_to_append is not None:
				other_dictionary_to_append[key][step] += output_dict_step_wise[key][step]
			step += step_size

	return average_values_per_step, other_dictionary_to_append


def format_average_query_performance_in_str(av_stats_dict, std_stats_dict=None, is_single_query=False):

	# simply using new variables for "avoiding" visual overload, using all the dictionaries
	av_precision = av_stats_dict["precision"]
	av_recall = av_stats_dict["recall"]
	av_total_steps = av_stats_dict["total_steps"]
	av_query_result_size = av_stats_dict["query_result_size"]
	av_episode_generation_deadend = av_stats_dict["episode_generation_deadend"]
	av_perfect_score = av_stats_dict["perfect_score"]

	av_teacher_ep_mem = av_stats_dict["teachers_ep_mem_size"]
	av_student_ep_mem = av_stats_dict["students_ep_mem_size"]
	av_teacher_sem_mem = av_stats_dict["teachers_sem_mem_size"]
	av_student_sem_mem = av_stats_dict["students_sem_mem_size"]

	# Query performance description string starts with how many query experiments where completed successfully (in case of more than one queries)
	if not is_single_query:
		output_str = f"Completed: {av_stats_dict['completed']:04.2}, "
	else:
		output_str = ""

	# Then we report how many experiments resulted to perfect performance and how many reached a deadend.
	output_str += f"Perf:{av_perfect_score:04.2}, Died: {av_episode_generation_deadend:04.2}, "

	# finally, we report more detailed performance measures, and we also add their standard deviations in parenthesis, if they are provided
	if std_stats_dict is None:
		output_str += f"Pre: {av_precision:04.2}, Rec: {av_recall:04.2}, #Steps: {av_total_steps:06.2}, #Results: {av_query_result_size:07.2}, "
		output_str += f"T_E_M: {av_teacher_ep_mem:04.2}, T_S_M: {av_teacher_sem_mem:04.2}, St_E_M {av_student_ep_mem:04.2}, St_S_M {av_student_sem_mem:04.2}"

	else:
		std_precision = std_stats_dict["precision"]
		std_recall = std_stats_dict["recall"]
		std_total_steps = std_stats_dict["total_steps"]
		std_query_result_size = std_stats_dict["query_result_size"]

		std_teacher_ep_mem = std_stats_dict["teachers_ep_mem_size"]
		std_student_ep_mem = std_stats_dict["students_ep_mem_size"]
		std_teacher_sem_mem = std_stats_dict["teachers_sem_mem_size"]
		std_student_sem_mem = std_stats_dict["students_sem_mem_size"]

		output_str += f"Pre: {av_precision:04.2} ({std_precision:04.2}), Rec: {av_recall:04.2} ({std_recall:04.2}), "
		output_str += f"#Steps: {av_total_steps:08.2} ({std_total_steps:08.2}), #Results: {av_query_result_size:07.2} ({std_query_result_size:07.2}), "
		output_str += f"T_E_M: {av_teacher_ep_mem:04.2} ({std_teacher_ep_mem:04.2}), T_S_M: {av_teacher_sem_mem:04.2} ({std_teacher_sem_mem:04.2}), "
		output_str += f"St_E_M {av_student_ep_mem:04.2} ({std_student_ep_mem:04.2}), St_S_M {av_student_sem_mem:04.2} ({std_student_sem_mem:04.2})"

	return output_str



def read_gt_alignments(prefix1, prefix2, alignments_directory):
	'''
	:param prefix1: ontology refix as writen in the filename
	:param prefix2: ontology refix as writen in the filename
	:param alignments_directory:
	:return: a dictionary of lists, where each term is related to all its equivalent terms.
	'''
	pair_name = prefix1 + "-" + prefix2
	filepath = os.path.join(alignments_directory, pair_name + ".txt")

	# GT alignment files are written in pairs of ontologies, but we need to check which ontology comes first on the name and content of the file
	if not os.path.exists(filepath):
		pair_name = prefix2 + "-" + prefix1
		filepath = os.path.join(alignments_directory, pair_name + ".txt")

	alignments = defaultdict(list)

	with open(filepath, 'r') as file:
		lines = file.readlines()

		# Strips the newline character
		for line in lines:
			term_1, term_2 = line.split(" ")
			term_1, term_2 = term_1.strip(), term_2.strip()
			alignments[term_1].append(term_2)
			alignments[term_2].append(term_1)
	return dict(alignments)


def get_common_objects(agents):
	# get common set of shareable objects across all agents
	common_objects = agents[0].get_all_named_individuals()
	for i in range(1, len(agents)):
		common_objects = common_objects.intersection(agents[i].get_all_named_individuals())
	return common_objects


# def evaluate_and_report_pdm_evaluation(agents, tensorboard_writer, step, experiment_metrics):
# 	evaluation_dictionaries = []
# 	for i, agent1 in enumerate(agents):
# 		for j, agent2 in enumerate(agents):
# 			if i != j:
# 				evaluation_dictionary = agent1.evaluate_alignments_with_other_pdm(agent2)
# 				evaluation_dictionaries.append(evaluation_dictionary)
#
# 	# initialize
# 	aggregated_dictionary = defaultdict(int)
# 	# sum
# 	for dictionary in evaluation_dictionaries:
# 		for key in dictionary:
# 			value = dictionary[key]
# 			aggregated_dictionary[key] += value
# 	# average
# 	num_of_dictionaries = len(evaluation_dictionaries)
# 	for key in aggregated_dictionary:
# 		aggregated_dictionary[key] /= num_of_dictionaries
#
# 		tensorboard_writer.add_scalar(key, aggregated_dictionary[key], step)
# 		experiment_metrics[key][step] = aggregated_dictionary[key]
