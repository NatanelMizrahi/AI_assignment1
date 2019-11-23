from utils.data_structures import Node, Edge, Graph
from typing import List, Set, TypeVar
from copy import copy as shallow_copy
from action import Action
from itertools import count
AgentType = TypeVar('Agent')


class EvacuateNode(Node):
    """Represents a node with people that are waiting for evacuation"""
    def __init__(self, label, deadline: int, n_people=0):
        super().__init__(label)
        self.deadline = deadline
        self.n_people = n_people
        self.n_people_initial = self.n_people
        self.evacuated = (n_people == 0)
        self.agents: Set[AgentType] = set([])

    def is_shelter(self):
        return False

    def summary(self):
        return '{}\n(D{}|P{}/{})'.format(self.label, self.deadline, self.n_people, self.n_people_initial)\
               + Node.summary(self)

    def describe(self):
        return self.summary() + '\n' + '\n'.join([agent.summary() for agent in self.agents])


class ShelterNode(EvacuateNode):
    """Represents a node with a shelter"""
    def is_shelter(self):
        return True

    def summary(self):
        return '{}\n(D{})'.format(self.label, self.deadline) + Node.summary(self)

    def describe(self):
        return 'Shelter\n' + super().describe()


class SmartGraph(Graph):
    """A variation of a graph that accounts for edge and node deadlines when running dijkstra"""

    def __init__(self, V: List[Node]=[], E: List[Edge]=[], env=None):
        """:param env: the enclosing environment in which the graph "lives". Used to access the environment's time."""
        super().__init__(V, E)
        self.env = env

    def is_blocked(self, u, v):
        e = self.get_edge(u, v)
        return e.blocked or self.env.time + e.w > e.deadline


class State:
    def __init__(self,
                 agent: AgentType,
                 agent_state: AgentType,
                 require_evac_nodes: Set[EvacuateNode],
                 blocked_edges: Set[Edge]):
        """creates a new state. Inherits env and agent data, unless overwritten"""
        self.agent = agent
        self.agent_state = agent_state
        self.require_evac_nodes = require_evac_nodes
        self.blocked_edges = blocked_edges

    def is_goal(self):
        return self.agent_state.terminated

    def describe(self):
        print("State: [{:<30}Evac:{}|Blocked:{}]"
              .format(self.agent.summary(), self.require_evac_nodes, self.blocked_edges))


class Environment:
    def __init__(self, G):
        self.time = 0
        self.G: SmartGraph = G
        self.agents: List[AgentType] = []
        self.require_evac_nodes: Set[EvacuateNode] = self.init_required_evac_nodes()
        self.blocked_edges: Set[Edge] = set([])
        self.agent_actions = {}

    def tick(self):
        self.time += 1
        self.execute_agent_actions()

    def all_terminated(self):
        return all([agent.terminated for agent in self.agents])

    def init_required_evac_nodes(self):
        return set([v for v in self.G.get_vertices() if (not v.is_shelter() and v.n_people > 0)])

    def get_blocked_edges(self):
        return set([e for e in self.G.get_edges() if self.G.is_blocked(e.v1, e.v2)]) # shallow_copy(self.blocked_edges)

    def get_require_evac_nodes(self):
        return shallow_copy(self.require_evac_nodes)

    def get_agent_actions(self):
        return {agent: agent.actions_seq for agent in self.agents}

    def add_agent_actions(self, agent_actions_to_add):
        for action in agent_actions_to_add:
            if action.end_time not in self.agent_actions:
                self.agent_actions[action.end_time] = []
            self.agent_actions[action.end_time].append(action)

    def execute_agent_actions(self):
        queued_actions = self.agent_actions.get(self.time)
        if queued_actions:
            for action in queued_actions:
                print('[EXECUTING]' + action.description)
                action.execute()
            del self.agent_actions[self.time]

    def get_state(self, agent: AgentType):
        return State(
            agent,
            agent.get_agent_state(),
            self.get_require_evac_nodes(),
            self.get_blocked_edges()
        )

    def apply_state(self, state: State):
        """applies a state to the environment, in terms of the agent's state variables,
           node evacuation status and blocked edges"""
        agent, to_copy = state.agent, state.agent_state
        agent.update(to_copy)
        self.time = agent.time
        self.require_evac_nodes = shallow_copy(state.require_evac_nodes)
        self.blocked_edges = shallow_copy(state.blocked_edges)
        for v in self.G.get_vertices():
            v_requires_evac = v in self.require_evac_nodes
            v.evacuated = not v_requires_evac
            v.n_people = v.n_people_initial if v_requires_evac else v.n_people
        for e in self.G.get_edges():
            e.blocked = e in self.blocked_edges

    # Bonus
    def get_edge_deadlines(self):
        vandals = [agent for agent in self.agents if agent.is_vandal()]
        if not vandals:
            return
        vandal_states = [self.get_state(vandal) for vandal in vandals]
        V = self.G.get_vertices()
        agent_locs = {v: shallow_copy(v.agents) for v in V}
        self.G.display('Initial State: (Vandals simulation)')
        while not all([vandal.terminated for vandal in vandals]):
            print('\nT={} (Vandals simulation)'.format(self.time))
            for vandal in vandals:
                vandal.act(self)
            self.tick()
        self.G.display('Final State: (Vandals simulation)')
        # restore initial state, keeping edge blocking times (edge deadlines)
        for vandal_state in vandal_states:
            self.apply_state(vandal_state)
        for v in V:
            v.agents = agent_locs[v]
        print("Finished vandals simulation. Edge deadlines:")
        print(set([(e, e.deadline) for e in self.G.get_edges() if e.deadline < float('inf')]))


class Plan:
    ID = count(0)

    def __init__(self, cost,
                 state: State,
                 action: Action,
                 parent=None):
        self.ID = next(Plan.ID)
        self.cost = cost
        self.state = state
        self.action = action
        self.parent = parent
        self.depth = parent and (parent.depth + 1) or 0

    def __lt__(self, other):
        """search tree node comparator. Tie-breaker prefers states in higher depths
           to increase likelihood of larger number of people being saved"""
        return (self.cost, other.depth) < (other.cost, self.depth)

    def summary(self):
        return "[{1.loc}]\nF={0}\nS{1.n_saved}|C{1.n_carrying}|{2}{3}\nB:{4}"\
            .format(self.cost,
                    self.state.agent_state,
                    self.state.require_evac_nodes or [],
                    '|T' if self.state.agent_state.terminated else '',
                    self.state.blocked_edges or [])
