from environment import Environment, EvacuateNode
from configurator import Configurator, debug
from action import Action, ActionType
from copy import copy as shallow_copy
from typing import List


class Agent:
    def __init__(self, name, start_loc: EvacuateNode):
        self.loc: EvacuateNode = start_loc
        self.actions_seq: List[Action] = []
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
                print('{}. {} -> {}'.format(i, self.loc.label, v.summary().replace('\n',' ')))
            print('{}. TERMINATE\n'.format(len(possible_steps)))
        return list(possible_steps)

    def is_reachable(self, env: Environment, v: EvacuateNode, verbose=False):
        """returns True iff transit to node v can be finished within v's deadline AND (u,v) is not blocked"""
        e = env.G.get_edge(self.loc, v)
        if env.G.is_blocked(e.v1, e.v2):
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
        e = env.G.get_edge(self.loc, v)
        if env.G.is_blocked(e.v1, e.v2):
            print('edge ({},{}) is blocked. Cannot complete move. Terminating.'.format(e.v1, e.v2))
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

    def register_goto_callback(self, env: Environment, v):
        if not self.is_reachable(env, v, verbose=True):
            self.terminate(env)
            return

        def goto_node():
            self.goto(env, v)
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

    def get_targets(self, env: Environment, src):
        V = env.G.get_vertices()
        shelters = [v for v in V if (v != src and v.is_shelter())]
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
        if len(self.actions_seq) == 0:
            return None
        return self.actions_seq[-1].action_type

    def register_action(self, env: Environment, action: Action, verbose=True):
        if action.action_type not in [ActionType.TERMINATE, ActionType.NO_OP]: # immediate actions - no delay
            env.add_agent_actions([action])
        self.actions_seq.append(action)
        self.time = max(self.time, action.end_time)
        if verbose:
            print('\n[START]' + action.description)

    def summary(self):
        terminate_string = '[${}]'.format(self.get_score()) if self.terminated else ''
        return '{0.name}|{0.loc}|S{0.n_saved}|C{0.n_carrying}{0.goto_str}|T{0.time:.2f}'.format(self) + terminate_string

    def describe(self):
        print(self.summary())

    def get_agent_state(self):
        return shallow_copy(self)

    def update(self, other):
        for k, v in other.__dict__.items():
            setattr(self, k, v)

    def __hash__(self):
        return hash(repr(self))

    def is_vandal(self):
        return False
