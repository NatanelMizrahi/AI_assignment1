from environment import Environment, SimpleNode
from utils.data_structures import Edge
from configurator import Configurator
from random import choice as rand_choice
from enum import Enum
DEBUG = True

class ActionType(Enum):
    NO_OP     = 0
    GOTO      = 1
    BLOCK     = 2
    TERMINATE = 3


class Agent:
    def __init__(self, name, start_loc: SimpleNode):
        self.loc: SimpleNode = start_loc
        self.actions_seq = []
        self.name = name
        self.n_saved = 0
        self.penalty = 0
        self.n_carrying = 0
        self.terminated = False
        self.action: Action = None
        self.time_to_action = 0
        print("{}({}) created in {}".format(self.name, self.__class__.__name__, start_loc))

    def act(self, env: Environment): # TODO: narrow down to state
        if self.terminated:
            return
        self.action = Action(self, self.loc)

    def get_score(self):
        return self.n_saved - self.penalty

    def get_possible_steps(self, env: Environment, verbose=0):
        possible_steps = env.G.neigbours(self.loc)
        if verbose:
            for i, v in enumerate(possible_steps):
                print('{}. {} -> {}'.format(i, self.loc.label, v.summary()))
            print('{}. NO_OP'.format(len(possible_steps)))
        return list(possible_steps)

    def goto(self, env: Environment, v: SimpleNode):
        self.action.action_type = ActionType.GOTO
        self.action.dest = v
        self.loc.agents.remove(self)
        self.loc = v
        v.agents.add(self)

    def try_evacuate(self, v: SimpleNode):
        if v.is_shelter():
            self.action.saved = self.n_carrying
            self.n_saved += self.n_carrying
            self.n_carrying = 0
        elif not v.evacuated:
            self.action.evacuated = v.n_people
            self.n_carrying += v.n_people
            v.evacuated = True
            v.n_people  = 0

    def terminate(self):
        self.action.action_type = ActionType.TERMINATE
        self.penalty = self.n_carrying + Configurator.base_penalty
        self.action.terminated = True
        self.terminated = True

    def register_action(self, verbose=True):
        self.actions_seq.append(self.action)
        if verbose:
            print(self.action.describe())

    def describe(self):
        print('{}: saved:{}; penalty:{}; loc:{}'.format(self.name, self.n_saved, self.penalty, self.loc.label))

    def summary(self):
        return '{}:S{};C{}{}'.format(self.name,
                                     self.n_saved,
                                     self.n_carrying,
                                     '\n[T:Score={}]'.format(self.get_score()) if self.terminated else '')

    def __hash__(self):
        return hash(self.name)


class Greedy(Agent):
    def act(self, env: Environment):
        super().act(env)
        s = self.loc
        env.G.dijkstra(s)
        V = env.G.get_vertices()
        shelters  = [v for v in V if (v != s and v.is_shelter()) ]
        need_evac = [v for v in V if (v != s and not v.is_shelter() and not v.evacuated)]
        targets = need_evac if self.n_carrying == 0 else shelters
        targets_by_priority = sorted(targets, key=lambda v: (v.d, v.label), reverse=True)
        if targets_by_priority:
            target = targets_by_priority.pop()
            next_node = env.G.shortest_path_successor(s, target)
            self.goto(env, next_node)
        else:
            self.terminate()
        self.register_action()

    def goto(self, env: Environment, v: SimpleNode):
        super().goto(env, v)
        self.try_evacuate(v)


class Human(Agent):
    @staticmethod
    def get_user_input(n_choices):
        if DEBUG:
            return rand_choice(range(n_choices))
        while True:
            try:
                choice = int(input('$ '))
                if choice < 0 or choice >= n_choices:
                    raise ValueError
                return choice
            except ValueError:
                print("Invalid choice, must be between 0 - {} please try again".format(max))

    def act(self, env: Environment):
        super().act(env)
        print('Choose your next step:')
        neighbours = self.get_possible_steps(env, verbose=not DEBUG)
        choice = self.get_user_input(len(neighbours)+1)
        if choice < len(neighbours):
            self.goto(env, neighbours[choice])
        self.register_action()

    def goto(self, env: Environment, v: SimpleNode):
        super().goto(env, v)
        self.try_evacuate(v)


class Vandal(Agent):
    def __init__(self, name, start_loc:SimpleNode):
        super().__init__(name, start_loc)
        self.reset_noop_counter()

    def act(self, env: Environment): # TODO: env sent by ref, easier to make a class member, is it legal?
        super().act(env)
        if self.noop_counter != 0:
            self.noop_counter -= 1
            self.no_op()
            return

        u = self.loc
        print('Possible steps:')
        neighbours = self.get_possible_steps(env,verbose=1)
        edges = [env.G.get_edge(u, v) for v in neighbours]
        sorted_edges = sorted(edges, key=lambda e: (e.w, e.v2.label), reverse=True)

        #TODO: moves twice in same turn? e.g. block road and traverse? No - two seperate actions
        # block the accessible road with the lowest weight, i.e remove it from graph
        if sorted_edges:
            e_to_block = sorted_edges.pop()
            self.block(env, e_to_block)
        else:
            self.terminate()
        # traverse road with lowest weight, i.e move to second vertex of respective edge
        if sorted_edges:
            e = sorted_edges.pop()
            self.goto(env, e.v2)
        else:
            self.terminate()
        self.reset_noop_counter()
        self.register_action()

    def goto(self, env: Environment, v: SimpleNode):
        self.loc.agents.remove(self)
        self.loc = v
        v.agents.add(self)

    def block(self, env: Environment, e: Edge):
        """ block the accessible road with the lowest weight, i.e remove it from graph """
        env.G.remove_edge(e.v1, e.v2)
        self.action.blocked = e

    def reset_noop_counter(self):
        self.noop_counter = Configurator.v_no_ops

    def no_op(self):
        '''agent does nothing'''
        self.action.action_type = ActionType.NO_OP
        self.register_action()


class Action:
    """Data structure for describing an agent's action"""
    def __init__(self,
                 agent: Agent,
                 src:  SimpleNode,
                 # optional arguments
                 dest: SimpleNode=None,
                 action_type: ActionType=None,
                 blocked: Edge=None,
                 saved=0,
                 evacuated=0):
        self.agent = agent
        self.action_type = action_type
        self.src = src
        self.dest = dest
        self.evacuated = evacuated
        self.saved = saved
        self.blocked = blocked
        self.terminated = action_type == ActionType.TERMINATE

    def describe(self):
        substrings = {
            'agent_name' : self.agent.name,
            'agent_type' : self.agent.__class__.__name__,
            'action_type': self.action_type,
            'evacuated'  : 'Evacuated: {}\n'.format(self.dest.n_people_initial) if self.evacuated else '',
            'saved'      : 'Saved:     {}\n'.format(self.saved) if self.saved else '',
            'blocked'    : 'Blocked:   {}\n'.format(self.blocked) if self.blocked else '',
            'move'       : 'Moved:     {} --> {}\n'.format(self.src, self.dest) if (self.src and self.dest) else '',
            'terminated' : 'Agent terminated.' if self.agent.terminated else ''
        }
        return \
'''
Agent:     {agent_name}({agent_type})
Action:    {action_type}
{blocked}{move}{evacuated}{saved}{terminated}'''.format(**substrings)
