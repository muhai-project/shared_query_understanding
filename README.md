(WIP) The code is being cleaned, and will soon be uploaded here, alongside with clear experiment replication steps.




python3 main.py --teacher_policy random --exp_dir experiments --repetitions 10 --max_steps 50 --eval_every 1 --common_instances simple --student_policy frequency-based

python3 main.py --teacher_policy random --exp_dir experiments --repetitions 10 --max_steps 50 --eval_every 1 --common_instances simple --student_policy logic-based

python3 main.py --teacher_policy property-based --exp_dir experiments --repetitions 10 --max_steps 50 --eval_every 1 --common_instances simple --student_policy frequency-based

python3 main.py --teacher_policy property-based --exp_dir experiments --repetitions 10 --max_steps 50 --eval_every 1 --common_instances simple --student_policy logic-based

python3 main.py --teacher_policy property-based --exp_dir experiments --repetitions 10 --max_steps 50 --eval_every 1 --common_instances extended --student_policy frequency-based

python3 main.py --teacher_policy property-based --exp_dir experiments --repetitions 10 --max_steps 50 --eval_every 1 --common_instances extended --student_policy logic-based

python3 main.py --teacher_policy random --exp_dir experiments --repetitions 10 --max_steps 50 --eval_every 1 --common_instances extended --student_policy frequency-based

python3 main.py --teacher_policy random --exp_dir experiments --repetitions 10 --max_steps 50 --eval_every 1 --common_instances extended --student_policy logic-based
