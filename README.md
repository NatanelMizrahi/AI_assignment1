# AI_assignment1
Hurricane evacuation simulator with AI search agents.
The first assignment in Intro to Aritificial Intelligence.
## Instructions:
usage: test.py [-h] [-g GRAPH_PATH] [-V V_NO_OPS] [-K BASE_PENALTY] [-L LIMIT]
               [-T T] [-a AGENTS [AGENTS ...]] [-d] [-i] [-s]

Environment simulator for the Hurricane Evacuation Problem 

optional arguments:
  -h, --help            show this help message and exit
  -g GRAPH_PATH, --graph_path GRAPH_PATH
                        path to graph initial configuration file
  -V V_NO_OPS, --v_no_ops V_NO_OPS
                        number of vandal agent's no-ops before taking action
  -K BASE_PENALTY, --base_penalty BASE_PENALTY
                        base penalty for losing an evacuation vehicle
  -L LIMIT, --limit LIMIT
                        Real-time A* agent expansions limit
  -T T                  search tree expansions time unit
  -a AGENTS [AGENTS ...], --agents AGENTS [AGENTS ...]
                        active agent types
  -d, --debug           run in debug mode
  -i, --interactive     run interactively (with graph displays)
  -s, --view_strategy   plot search agents strategy trees
  
example: 
python3 test.py -V 1 -K 5 -g tests/23-11__18-08-25.config -a RTAStar Vandal -T 0.01 -L 7
