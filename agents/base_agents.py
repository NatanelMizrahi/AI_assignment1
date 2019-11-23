from environment import Environment, EvacuateNode
from agents.agent import Agent
from utils.data_structures import Edge
from configurator import Configurator, debug
from random import choice as rand_choice
from action import Action, ActionType


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

        debug("# NOOPS left: {}".format(self.noop_counter))
        if self.noop_counter != 0:
            self.noop_counter -= 1
            self.no_op(env)
            return

        u = self.loc
        if self.last_action_type() == ActionType.BLOCK:
            targets = self.get_possible_steps(env)
        else:
            targets = env.G.neighbours(self.loc)

        edges = [env.G.get_edge(u, v) for v in targets]
        if not edges:
            self.terminate(env)
            return

        def comp(e: Edge):
            dest = e.v1 if u != e.v1 else e.v2
            return e.w, dest.label  # sort by weight, tie-breaker is destination node's name

        e_min = min(edges, key=comp)
        if self.last_action_type() == ActionType.BLOCK:
            # traverse road with lowest weight, i.e move to second vertex of respective edge
            v = e_min.v1 if u != e_min.v1 else e_min.v2
            self.goto2(env, v)
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
        env.G.block_edge(e.v1, e.v2, block_time=self.time)
        env.blocked_edges.add(e)
        self.n_blocked += 1

    def register_block_edge_callback(self, env: Environment, e:Edge):
        def block_edge():
            self.block(env, e)
        end_time = (self.time + 1)
        block_action = Action(
            agent=self,
            action_type=ActionType.BLOCK,
            description='{0}: Blocking ({e.v1},{e.v2}) (end time:{end})'.format(self.name, e=e, end=end_time),
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

    def is_vandal(self):
        return True
