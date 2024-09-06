This repository contains the code for reproducing the experimental results presented in the paper

"Establishing Shared Query Understanding in an Open Multi-Agent System" Kondylidis et al. AAMAS 2023.

To replicate the experiment results you need to first clone this repository and then "move" to that directory, by executing:

    git clone https://github.com/kondilidisn/shared_query_understanding
    cd shared_query_understanding

You can create a new python environment and install all libraries mentioned in requirements.txt by executing:

    python3 -m venv venv/
    source venv/bin/activate
    pip3 install -r requirements.txt

You can then directly run the 8 experiments presented in the paper by executing:

    python3 main.py --common_instances simple --teacher_policy random --student_policy frequency-based
    python3 main.py --common_instances simple --teacher_policy random --student_policy logic-based
    python3 main.py --common_instances simple --teacher_policy property-based --student_policy frequency-based
    python3 main.py --common_instances simple --teacher_policy property-based --student_policy logic-based
    python3 main.py --common_instances extended --teacher_policy property-based --student_policy frequency-based
    python3 main.py --common_instances extended --teacher_policy property-based --student_policy logic-based
    python3 main.py --common_instances extended --teacher_policy random --student_policy frequency-based
    python3 main.py --common_instances extended --teacher_policy random --student_policy logic-based
    

[Optional] Replicating the data pre-processing:

The directory "dataset" already contains all preprocessed data needed to run the experiments. In case you want to replicate that process as well, you need to follow the next steps before running the experiments:

i) Create the dataset directory:

    mkdir dataset
 
ii) Download and unzip the original OA4QA track dataset (http://oaei.ontologymatching.org/2015/oa4qa/index.html):
 
    wget http://oaei.ontologymatching.org/2015/oa4qa/oaei2015_oa4qa_bundle.zip
    mv oaei2015_oa4qa_bundle.zip data_preparation/oaei2015_oa4qa_bundle.zip
    unzip data_preparation/oaei2015_oa4qa_bundle.zip -d data_preparation/
    
iii) Translate their provided concept alignments to RDF OWL

    python3 translate_alignments.py
    
iv) Save ontologies that include reasoner inferred axioms about instance information (super-class membership etc.)

We do this because we RDFLib for our experiments which does not provide reasoning tools.
We performed this step manually using Protégé, (https://protege.stanford.edu/), and unfortunately we do not provide some straightforward command lines to replicate it.
You can by-pass this step by copying our provided and execute:

    mkdir dataset/reasoned_ontologies
    cp -r data_preparation/reasoned_ontologies/ dataset/reasoned_ontologies/
    
v) Create Instance Alignments for extended dataset experiments.

We need to create more instance alignments across pairs of ontologies in order to perform more experiments using more provided concept alignments. To do so, please execute:

    python3 generate_instance_alignments_for_extended_dataset.py

AAMAS readme

# Acknowledgement: 
This work was funded by the European MUHAI project (Horizon 2020 research and innovation program) under grant agreement number 951846, the Vrije Universiteit Amsterdam. We want to thank Frank van Harmelen for his continuous support and guidance.
# Application domain: 
Semantc web
# Citation: 
@inproceedings{10.5555/3545946.3598649,
author = {Kondylidis, Nikolaos and Tiddi, Ilaria and ten Teije, Annette},
title = {Establishing Shared Query Understanding in an Open Multi-Agent System},
year = {2023},
isbn = {9781450394321},
publisher = {International Foundation for Autonomous Agents and Multiagent Systems},
address = {Richland, SC},
booktitle = {Proceedings of the 2023 International Conference on Autonomous Agents and Multiagent Systems},
pages = {281–289},
numpages = {9},
keywords = {collaborative query answering, open multi-agent systems, task-oriented communication establishment},
location = {London, United Kingdom},
series = {AAMAS '23}
}
# Code of Conduct: 

# Code repository: 
https://github.com/muhai-project/shared_query_understanding
# Contact: 
Nikolaos Kondylidis
# Contribution guidelines: 

# Contributors: 
Nikolaos Kondylidis
# Creation date: 
22-02-2023
# Description: 
This is the code for the paper accepted for publication to AAMAS 2023: "Establishing Shared Query Understanding in an Open Multi-Agent System".
The experimental setup allows the development and evaluation of agent policies, that attempt to explain a query term to each other, over grounded communication.
# DockerFile: 

# Documentation: 

# Download URL: 

# DOI: 

# Executable examples: 

# FAQ: 

# Forks count: 
0
# Forks url: 

# Full name: 

# Full title: 
shared_query_understanding
# Images: 

# Installation instructions: 

# Invocation: 

# Issue tracker: 

# Keywords: 

# License: 
https://creativecommons.org/licenses/by/4.0/legalcode
# Logo: 

# Name: 

# Ontologies: 

# Owner: 
MUHAI Project
# Owner type: 
organization
# Package distribution: 

# Programming languages: 
Python
# Related papers: 
https://arxiv.org/abs/2305.09349, https://dl-acm-org.vu-nl.idm.oclc.org/doi/10.5555/3545946.3598649
# Releases (GitHub only): 

# Repository Status: 
Inactive
# Requirements: 

# Support: 

# Stargazers count: 

# Scripts: Snippets of code contained in the repository
# Support channels: 
# Usage examples: 

# Workflows: 

