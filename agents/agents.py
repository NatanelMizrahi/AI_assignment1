from environment import Environment, State, EvacuateNode, SearchTree
from utils.data_structures import Edge, Stack
from configurator import Configurator
from random import choice as rand_choice
from typing import Dict, List #TODO
from action import Action, ActionType
from copy import copy as shallow_copy

def debug(s):
    if Configurator.debug: print(s)

class Agent:
    def __init__(self, name, start_loc: EvacuateNode):
        self.loc: EvacuateNode = start_loc
        self.actions_seq = []
        self.name = name
        self.n_saved = 0
        self.penalty = 0
        self.n_carrying = 0
        self.terminated = False
        self.time = 0
        self.goto_str = '' # used for debug
        print("{}({}) created in {}".format(self.name, self.__class__.__name__, start_loc))

    def get_strategy(self):
        """non-SearchAgent instances do not have a strategy. SearchAgent instances override this method"""
        pass

    def is_available(self, env: Environment):
        return (not self.terminated) and self.time <= env.time

    def act(self, env: Environment):
        pass

    def get_score(self):
        return self.n_saved - self.penalty

    def get_possible_steps(self, env: Environment, verbose=False):
        possible_steps = [v for v in env.G.neighbours(self.loc) if self.is_reachable(env, v)]
        if verbose:
            for i, v in enumerate(possible_steps):
                print('{}. {} -> {}'.format(i, self.loc.label, v.summary()))
            print('{}. TERMINATE\n'.format(len(possible_steps)))
        return list(possible_steps)

    def is_reachable(self, env: Environment, v: EvacuateNode, verbose=False):
        """returns True iff transit to node v can be finished within v's deadline AND (u,v) is not blocked"""
        e = env.G.get_edge(self.loc, v)
        if e.is_blocked():
            if verbose:
                print('edge ({},{}) is blocked.'.format(e.v1, e.v2))
            return False
        if self.time + e.w > v.deadline:
            if verbose:
                print('cannot reach {} from {} before deadline. time={} e.w={} deadline={}'
                      .format(v.label, self.loc, self.time, e.w, v.deadline))
            return False
        return True

    def goto_duration(self, env, v):
        return self.time + env.G.get_edge(self.loc, v).w

    def goto2(self, env: Environment, v: EvacuateNode): #TODO: refactor: rename
        """Move agent, taking transit time into account"""
        self.register_goto_callback(env, v)

    def goto(self, env: Environment, v: EvacuateNode):
        if not self.is_reachable(env, v, verbose=True):
            self.terminate(env)
            return
        self.loc.agents.remove(self)
        self.loc = v
        v.agents.add(self)
        self.goto_str = ''

    def local_goto(self, env: Environment, v: EvacuateNode): #TODO: fix/remove
        """simulates a goto operation locally for an agent- without updating the environment's entire state"""
        self.time = self.goto_duration(env, v)
        self.loc = v
        self.try_evacuate(env, v)

    def local_terminate(self):
        """simulates a terminate operation locally for an agent- without updating the environment's entire state"""
        self.penalty = self.n_carrying + Configurator.base_penalty
        self.terminated = True

    ## callback implementation
    def register_goto_callback(self, env: Environment, v):
        if not self.is_reachable(env, v, verbose=True):
            self.terminate(env)
            return
        def goto_node(): self.goto(env, v)
        end_time = self.goto_duration(env, v)
        goto_action = Action(
            agent=self,
            action_type=ActionType.GOTO,
            description='{}: Go from {} to {} (end_time: {})'.format(self.name, self.loc, v.label, end_time),
            callback=goto_node,
            end_time=end_time
        )
        self.goto_str = '->{}'.format(v)
        self.register_action(env, goto_action)

    def get_targets(self, env:Environment, src):
        V = env.G.get_vertices()
        shelters = [v for v in V if (v != src  and v.is_shelter())]
        need_evac = [v for v in V if (v != src and not v.is_shelter() and not v.evacuated)]
        targets = need_evac if self.n_carrying == 0 else shelters
        return targets

    def try_evacuate(self, env: Environment, v: EvacuateNode):
        if self.terminated:
            return
        if v.is_shelter():
            if self.n_carrying > 0:
                debug('Dropped off {.n_carrying} people'.format(self))
                self.n_saved += self.n_carrying
                self.n_carrying = 0
        elif not v.evacuated:
            debug('Picked up {} people'.format(v.n_people))
            self.n_carrying += v.n_people
            v.evacuated = True
            v.n_people = 0
            env.require_evac_nodes.remove(v)

    def terminate(self, env: Environment):
        terminate_action = Action(
            agent=self,
            action_type=ActionType.TERMINATE,
            description='Terminating {}. Score = {}'.format(self.name, self.get_score())
        )
        self.register_action(env, terminate_action)
        self.penalty = self.n_carrying + Configurator.base_penalty
        self.terminated = True

    def last_action_type(self):
        return self.actions_seq[-1].action_type

    def register_action(self, env: Environment, action: Action, verbose=True):
        if action.action_type not in [ActionType.TERMINATE, ActionType.NO_OP]: # immediate actions - no delay
            env.add_agent_actions([action])
        self.actions_seq.append(action)
        self.time = max(self.time, action.end_time)
        if verbose:
            print('[START]' + action.description)

    def describe(self):
        print("{0.name}: V={0.loc.label}; S={0.n_saved}; C={0.n_carrying}; T={0.terminated};".format(self))

    def summary(self):
        return '{0.name}:S{0.n_saved};C{0.n_carrying}{0.goto_str}({0.time}){1}'\
            .format(self, '\n[T:Score={}]'.format(self.get_score()) if self.terminated else '')

    def get_agent_state(self):
        return shallow_copy(self)

    def update(self, other):
        for k, v in other.__dict__.items():
            setattr(self, k, v)

    def __hash__(self):
        return hash(repr(self))


class Greedy(Agent):
    def act(self, env: Environment):
        if not self.is_available(env):
            return
        s = self.loc
        env.G.dijkstra(s)
        targets = self.get_targets(env, s)
        targets_by_priority = sorted(targets, key=lambda v: (v.d, v.label), reverse=True)
        if targets_by_priority:
            target = targets_by_priority.pop()
            next_node = env.G.shortest_path_successor(s, target)
            self.goto2(env, next_node)
        else:
            self.terminate(env)

    def goto(self, env: Environment, v: EvacuateNode):
        super().goto(env, v)
        self.try_evacuate(env, v)


class Human(Agent):
    @staticmethod
    def get_user_input(n_choices):
        if Configurator.debug:
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
        if not self.is_available(env):
            return
        print('Choose your next step:')
        neighbours = self.get_possible_steps(env, verbose=not Configurator.debug)
        choice = self.get_user_input(len(neighbours)+1)
        if choice < len(neighbours):
            self.goto2(env, neighbours[choice])
        else:
            self.terminate(env)

    def goto(self, env: Environment, v: EvacuateNode):
        super().goto(env, v)
        self.try_evacuate(env, v)


class Vandal(Agent):
    def __init__(self, name, start_loc: EvacuateNode):
        super().__init__(name, start_loc)
        self.noop_counter = 0
        self.n_blocked = 0
        self.reset_noop_counter()

    def act(self, env: Environment):
        if not self.is_available(env):
            return
        debug("#NOOPS left: {}".format(self.noop_counter))
        if self.noop_counter != 0:
            self.noop_counter -= 1
            self.no_op(env)
            return

        u = self.loc
        neighbours = self.get_possible_steps(env, verbose=0)
        edges = [env.G.get_edge(u, v) for v in neighbours]
        if not edges:
            self.terminate(env)
            return

        def comp(e: Edge): return e.w, e.v2.label  # sort by weight, tie-breaker is destination node's name
        e_min = min(edges, key=comp)
        if self.last_action_type() == ActionType.BLOCK:
            # traverse road with lowest weight, i.e move to second vertex of respective edge
            self.goto2(env, e_min.v2)
        else:
            # block the accessible road with the lowest weight, i.e remove it from graph
            self.block2(env, e_min)

    def goto(self, env: Environment, v: EvacuateNode):
        super().goto(env, v)
        self.reset_noop_counter()

    def block2(self, env: Environment, e: Edge):
        self.register_block_edge_callback(env, e)

    def block(self, env: Environment, e: Edge):
        """ block the accessible road with the lowest weight, i.e remove it from graph """
        env.G.block_edge(e.v1, e.v2)
        self.n_blocked += 1

    def register_block_edge_callback(self, env: Environment, e:Edge):
        def block_edge():
            self.block(env, e)
        end_time = (self.time + 1)
        block_action = Action(
            agent=self,
            action_type=ActionType.BLOCK,
            description='{0}: Blocking {e.v1} to {e.v2} (end time:{end})'.format(self.name, e=e, end=end_time),
            callback=block_edge,
            end_time=end_time
        )
        self.register_action(env, block_action)

    def reset_noop_counter(self):
        self.noop_counter = Configurator.v_no_ops

    def get_score(self):
        return self.n_blocked

    def no_op(self, env):
        """agent does nothing"""
        self.register_action(env, Action(
            agent=self,
            action_type=ActionType.NO_OP,
            description='{.name}: NO_OP'.format(self),
            end_time=(self.time + 1)
        ))


class SearchAgent(Greedy):
    def __init__(self, name, start_loc: EvacuateNode):
        super().__init__(name, start_loc)
        self.strategy: Stack[Action] = Stack()

    def get_strategy(self, env: Environment):
        if not self.strategy.is_empty():
            return # strategy already exists
        expand_count, self.strategy = SearchTree(env, self).tree_search()
        debug('expand count = {}'.format(expand_count))
        self.describe_strategy()

    def describe_strategy(self):
        print('\nStrategy for {}:'.format(self.name))
        print('number of actions: {}'.format(len(self.strategy.stack)))
        for action in reversed(self.strategy.stack):
            action.describe()

    def act(self, env: Environment):
        """pop the next action in strategy and execute it"""
        if self.strategy.is_empty():
            self.get_strategy(env)
        if self.is_available(env) and not self.strategy.is_empty():
            self.strategy.pop().execute()


class GreedySearch(SearchAgent):
    pass
