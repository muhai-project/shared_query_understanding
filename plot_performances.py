from collections import defaultdict
import pickle
import matplotlib.pyplot as plt
import os

extended_dataset_legend_2_exp_dir = {
"Rand-Freq": "experiments/all_ontology_pairs__TP=random__SP=frequency-based__reps=10__instances=extended__max_steps=100",
"Rand-Logic": "experiments/all_ontology_pairs__TP=random__SP=logic-based__reps=10__instances=extended__max_steps=100",
"Prop-Freq": "experiments/all_ontology_pairs__TP=property-based__SP=frequency-based__reps=10__instances=extended__max_steps=100",
"Prop-Logic": "experiments/all_ontology_pairs__TP=property-based__SP=logic-based__reps=10__instances=extended__max_steps=100"}

simple_dataset_legend_2_exp_dir = {
"Rand-Freq": "experiments/all_ontology_pairs__TP=random__SP=frequency-based__reps=10__instances=simple__max_steps=100",
"Rand-Logic": "experiments/all_ontology_pairs__TP=random__SP=logic-based__reps=10__instances=simple__max_steps=100",
"Prop-Freq": "experiments/all_ontology_pairs__TP=property-based__SP=frequency-based__reps=10__instances=simple__max_steps=100",
"Prop-Logic": "experiments/all_ontology_pairs__TP=property-based__SP=logic-based__reps=10__instances=simple__max_steps=100"}

max_steps = 50
steps = [i+1 for i in list(range(max_steps))]

simple_exp_results = dict()
for exp_legend in simple_dataset_legend_2_exp_dir:
	simple_exp_results[exp_legend] = defaultdict(list)
	with open(os.path.join(simple_dataset_legend_2_exp_dir[exp_legend], "av_stats_per_step_dict.pickle"), 'rb') as handle:
		exp_performance = pickle.load(handle)
	for metric in exp_performance:
		for step in steps:
			simple_exp_results[exp_legend][metric].append(exp_performance[metric][step])

extended_exp_results = dict()
for exp_legend in extended_dataset_legend_2_exp_dir:
	extended_exp_results[exp_legend] = defaultdict(list)
	with open(os.path.join(extended_dataset_legend_2_exp_dir[exp_legend], "av_stats_per_step_dict.pickle"),
			  'rb') as handle:
		exp_performance = pickle.load(handle)
	for metric in exp_performance:
		for step in steps:
			extended_exp_results[exp_legend][metric].append(exp_performance[metric][step])

		print()

legends = ["Random-Frequency", "Random-Logic", "Property-Frequency", "Property-Logic"]

fig, axs = plt.subplots(2, 2, sharey="row")
axs[0, 0].plot(steps, simple_exp_results["Rand-Freq"]["1.precision"], '-')
axs[0, 0].plot(steps, simple_exp_results["Rand-Logic"]["1.precision"], ':')
axs[0, 0].plot(steps, simple_exp_results["Prop-Freq"]["1.precision"], '--')
axs[0, 0].plot(steps, simple_exp_results["Prop-Logic"]["1.precision"], '-.')

axs[0, 0].set_title('Simple Dataset', fontsize=12)
axs[0, 1].plot(steps, extended_exp_results["Rand-Freq"]["1.precision"], '-')
axs[0, 1].plot(steps, extended_exp_results["Rand-Logic"]["1.precision"], ':')
axs[0, 1].plot(steps, extended_exp_results["Prop-Freq"]["1.precision"], '--')
axs[0, 1].plot(steps, extended_exp_results["Prop-Logic"]["1.precision"], '-.')
axs[0, 1].set_title('Extended Dataset', fontsize=12)
axs[1, 0].plot(steps, simple_exp_results["Rand-Freq"]["2.recall"], '-')
axs[1, 0].plot(steps, simple_exp_results["Rand-Logic"]["2.recall"], ':')
axs[1, 0].plot(steps, simple_exp_results["Prop-Freq"]["2.recall"], '--')
axs[1, 0].plot(steps, simple_exp_results["Prop-Logic"]["2.recall"], '-.')
# axs[1, 0].set_title('Simple Dataset Recall')
axs[1, 1].plot(steps, extended_exp_results["Rand-Freq"]["2.recall"], '-')
axs[1, 1].plot(steps, extended_exp_results["Rand-Logic"]["2.recall"], ':')
axs[1, 1].plot(steps, extended_exp_results["Prop-Freq"]["2.recall"], '--')
axs[1, 1].plot(steps, extended_exp_results["Prop-Logic"]["2.recall"], '-.')

axs[0, 0].legend(legends, loc=0)

axs[0,1].get_xaxis().set_visible(False)
axs[0,0].get_xaxis().set_visible(False)

fig.tight_layout()

axs[0, 0].set_ylabel('Precision', fontsize=12) # Y label

axs[1, 0].set_ylabel('Recall', fontsize=12)
axs[1, 0].set_xlabel('# Examples', fontsize=12)

axs[1, 1].set_xlabel('# Examples', fontsize = 12) # X label

plt.show()
