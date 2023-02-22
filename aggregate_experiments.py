
import argparse
import pickle
import os
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument('--exp_dir', type=str)

args = parser.parse_args()

# read the dictionaries with statistics from every iteration directory
i = 0
iteration_path = os.path.join(args.exp_dir, str(i))
all_statistics = []

while os.path.isdir(iteration_path):
	dict_path = os.path.join(iteration_path, "experiment_statistics.pickle")
	with open(dict_path, 'rb') as file:
		stat_dict = pickle.load(dict_path)
		all_statistics.append(stat_dict)

	i += 1
	iteration_path = os.path.join(args.exp_dir, str(i))

num_of_iterations = i

# aggregate statistics (calculate means and stds)






