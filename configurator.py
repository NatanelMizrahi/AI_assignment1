import argparse
from random import sample
from datetime import datetime
from utils.data_structures import Edge
from environment import Environment, ShelterNode, EvacuateNode, SmartGraph


class Configurator:
    """static configurator class"""
    @staticmethod
    def get_user_config():
        parser = argparse.ArgumentParser(description='''
        Environment simulator for the Hurricane Evacuation Problem
        example: python3 test.py -V 1 -K 5 -g tests/23-11__18-08-25.config -a AStar Vandal''')
        parser.add_argument('-g', '--graph_path',    default='random',                       help='path to graph initial configuration file')
        parser.add_argument('-V', '--v_no_ops',      default='1',       type=int,            help='number of vandal agent\'s no-ops before taking action')
        parser.add_argument('-K', '--base_penalty',  default='2',       type=int,            help='base penalty for losing an evacuation vehicle')
        parser.add_argument('-L', '--limit',         default='5',       type=int,            help='Real-time A* agent expansions limit')
        parser.add_argument('-T',                    default='0',       type=float,          help='search tree expansions time unit')
        parser.add_argument('-a', '--agents',        default=['AStar'], nargs='+',           help='active agent types')
        # debug command line arguments
        parser.add_argument('-d', '--debug',         default=True,      action='store_true', help='run in debug mode')
        parser.add_argument('-i', '--interactive',   default=True,      action='store_true', help='run interactively (with graph displays)')
        parser.add_argument('-s', '--view_strategy', default=True,      action='store_true', help='plot search agents strategy trees')

        args = vars(parser.parse_args())
        for k, v in args.items():
            setattr(Configurator, k, v)
        print("Environment Configured.")

    @staticmethod
    def randomize_config():
        def legal_config(G):
            inf = float('inf')
            V = G.get_vertices()
            if not V:
                return False  # Graph cannot be empty
            # must have at least one shelter node
            has_shelter = any([isinstance(v, ShelterNode) for v in V])
            if not has_shelter:
                return False
            s = list([v for v in V if v.is_shelter()])[0]
            # all nodes must be initially connected
            G.dijkstra(s)
            all_reachable = all([v.d < inf for v in V])
            n_doomed_initial = sum([v.n_people for v in V if 2*v.d > v.deadline or 2*v.d > s.deadline])
            return has_shelter and all_reachable and n_doomed_initial == 0

        def rand_bool(prob=2):
            return sample(range(60), 1)[0] < 60 / prob

        def rand_weight(u, v):
            return sample(range(1, min(u.deadline, v.deadline)+1), 1)[0]

        G = SmartGraph()
        while not legal_config(G):
            V = []
            E = []
            N = sample(range(4, 8), 1)[0]
            L = ['V{}'.format(i) for i in range(N)]
            D = sample(range(1, 2 * N), N)
            P = sample(range(0, 20), N)

            for node_args in zip(L, D, P):
                node_type = ShelterNode if rand_bool(5) else EvacuateNode
                u = node_type(*node_args)
                V.append(u)
                for v in V[:-1]:
                    if rand_bool(3):
                        E.append(Edge(u, v, rand_weight(u, v), 'E0'))
            G = SmartGraph(V, E, Environment(G))
        Configurator.v_no_ops, Configurator.base_penalty = sample(range(5), 2)
        print('base penalty: {}; # vandal no ops: {}'.format(Configurator.base_penalty, Configurator.v_no_ops))
        filename = 'tests/{:%d-%m__%H-%M-%S}.config'.format(datetime.now())
        lines = []
        # save new configuration in file for review
        with open(filename, 'w') as config_file:
            lines.append('#N {}'.format(N))
            for v in V:
                if (isinstance(v,ShelterNode)):
                    lines.append('#{} D{} S'.format(v.label, v.deadline))
                else:
                    lines.append('#{} D{} P{}'.format(v.label, v.deadline, v.n_people))
            for e in E:
                lines.append('#{} {} {} W{}'.format(e.name, e.v1.label[1:], e.v2.label[1:], e.w))
            config_file.write('\n'.join(lines))

        return G


def debug(s):
    if Configurator.debug:
        print(s)

