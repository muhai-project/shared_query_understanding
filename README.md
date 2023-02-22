This repository contains the code for reproducing the experimental results presented in the paper

"Establishing Shared Query Understanding in an Open Multi-Agent System" Kondylidis et al. AAMAS 2023.

To replicate the experiment results you need to first clone this repository and then "move" to that directory, by executing:

    git clone https://github.com/kondilidisn/shared_query_understanding
    cd shared_query_understanding

You can create a new python environment and isntall all libraries mentioned in requirements.txt by executing:

    python3 -m venv venv/
    source venv/bin/activate
    pip3 install -r requirements.txt

You can then directly run the 8 experiments presented in the paper by executing:

    python3 main.py --exp_dir experiments --repetitions 10 --max_steps 100 --eval_every 1 --common_instances simple --teacher_policy random --student_policy frequency-based
    python3 main.py --exp_dir experiments --repetitions 10 --max_steps 100 --eval_every 1 --common_instances simple --teacher_policy random --student_policy logic-based
    python3 main.py --exp_dir experiments --repetitions 10 --max_steps 100 --eval_every 1 --common_instances simple --teacher_policy property-based --student_policy frequency-based
    python3 main.py --exp_dir experiments --repetitions 10 --max_steps 100 --eval_every 1 --common_instances simple --teacher_policy property-based --student_policy logic-based
    python3 main.py --exp_dir experiments --repetitions 10 --max_steps 100 --eval_every 1 --common_instances extended --teacher_policy property-based --student_policy frequency-based
    python3 main.py --exp_dir experiments --repetitions 10 --max_steps 100 --eval_every 1 --common_instances extended --teacher_policy property-based --student_policy logic-based
    python3 main.py --exp_dir experiments --repetitions 10 --max_steps 100 --eval_every 1 --common_instances extended --teacher_policy random --student_policy frequency-based
    python3 main.py --exp_dir experiments --repetitions 10 --max_steps 100 --eval_every 1 --common_instances extended --teacher_policy random --student_policy logic-based
    

[Optional] Replicating the data pre-processing:

The directory "dataset" already contains all preprocessed data needed to run the experiments. In case you want to replicate that process as well, you need to follow the next steps before running the experiments:

i) Create the dataset directory:

    mkdir dataset
 
ii) Download and unzip the original OA4QA track dataset (http://oaei.ontologymatching.org/2015/oa4qa/index.html):
 
    wget http://oaei.ontologymatching.org/2015/oa4qa/oaei2015_oa4qa_bundle.zip
    mv oaei2015_oa4qa_bundle.zip data_preparation/oaei2015_oa4qa_bundle.zip
    unzip data_preparation/oaei2015_oa4qa_bundle.zip -d data_preparation/
    
iii) Translate their provided concept alignemnts to RDF OWL

    python3 translate_alignments.py
    
iv) Save ontologies that include reasoner infered acioms about isntance information (super-class membership etc.)

We do this because we RDFLib for our experiments which does not provide reasoning tools.
We performed this step manually using Protégé, (https://protege.stanford.edu/), and unfortunately we do not provide some straightforwrad command lines to replicate it.
You can by-pass this step by using our provided outputby executing:

    mkdir dataset/reasoned_ontologies
    cp -r data_preparation/reasoned_ontologies/ dataset/reasoned_ontologies/
    
v) Create Instance Alignments for extended dataset experiments.

We need to create more instance alignments across pairs of ontologiesm in order to perform more experiments using more provided concept alignments. To do so, please execute:

    python3 generate_instance_alignments_for_extended_dataset.py

    

