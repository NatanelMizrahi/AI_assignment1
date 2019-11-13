from utils.data_structures import Node, Edge, Graph, Heap, Pair
from copy import copy, deepcopy
from typing import Dict, Set


class SimpleNode(Node): #TODO: change name
    '''Represents a node with people that are waiting for evacuation'''
    def __init__(self, label, deadline: int, n_people=0):
        super().__init__(label)
        self.deadline = deadline
        self.n_people = n_people
        self.n_people_initial = self.n_people
        self.evacuated = False
        self.agents = set([])

    def is_shelter(self):
        return False

    def summary(self):
        return '{}:(D{}|P{}/{})'.format(self.label, self.deadline, self.n_people, self.n_people_initial) + Node.summary(self)

    def describe(self):
        return self.summary() + '\n' + '\n'.join([agent.summary() for agent in self.agents])


class ShelterNode(SimpleNode):
    '''Represents a node with a shelter'''
    def is_shelter(self):
        return True

    def summary(self):
        return '{}:(D{})'.format(self.label, self.deadline) + Node.summary(self)

    def describe(self):
        return 'Shelter\n' + super().describe()


class Environment:
    def __init__(self, G,
                 time=0,
                 agents=[],
                 require_evac_nodes=set([])):
        self.G: Graph = G
        self.time = time
        self.agents = agents
        self.agent_actions = {}
        self.require_evac_nodes: Set[Node] = require_evac_nodes
        self.max_ticks = self.get_max_ticks()

    def tick(self):
        self.time += 1
        self.execute_agent_actions()

    def all_terminated(self):
        return all([agent.terminated for agent in self.agents])

    def get_state(self):
        pass
        #TODO

    def get_max_ticks(self):
        return max([v.deadline for v in self.G.get_vertices()]) + 1

    def copy(self):
        return deepcopy(self)

    def copy_agents(self):
        return [copy(agent) for agent in self.agents]

    def is_evacuated(self, v: SimpleNode):
        return v in self.require_evac_nodes

    def get_agent_actions(self):
        return { agent: agent.actions_seq for agent in self.agents }

    def add_agent_actions(self, agent_actions_to_add):
        for action in agent_actions_to_add:
            if action.end_time not in self.agent_actions:
                self.agent_actions[action.end_time] = []
            self.agent_actions[action.end_time].append(action)

    def execute_agent_actions(self):
        queued_actions = self.agent_actions.get(self.time)
        if queued_actions:
            for action in queued_actions:
                print('\n[EXECUTING]' + action.describe())
                action.execute()
            del self.agent_actions[self.time]

    def compute_search_agents_strategy(self):
        return # TODO delete after implementing

        initial_state = self.get_state(...)
        for agent in self.agents:
                agent.get_strategy(self,initial_state)


class State:
    # TODO: maybe create state each time we expand, and apply state on env for each time we compute h(x)??
    def __init__(self,
                 agent,
                 env: Environment,
                 agent_loc: SimpleNode,
                 agent_time,
                 n_saved,
                 n_carrying,
                 node_evacuated_dict: Dict[SimpleNode, bool],
                 blocked_edges_dict:  Dict[Edge, bool],
                 is_terminated=False
             ):
        # TODO: shallow copy agent instead
        self.agent = agent
        self.env = env
        self.agent_loc = agent_loc
        self.agent_time = agent_time
        self.n_saved = n_saved
        self.n_carrying = n_carrying
        self.is_terminated = is_terminated
        self.node_evacuated_dict = node_evacuated_dict # for each node - is it evacuated? (T/F)
        self.blocked_edges_dict = blocked_edges_dict   # for each edge - is it blocked? (T/F)

    def apply(self):
        for v in self.env.G.get_vertices():
            v.evacuated = self.node_evacuated_dict[v]
        for e in self.env.G.get_edges():
            e.blocked = self.blocked_edges_dict[e]
        self.agent.loc = self.agent_loc
        self.agent.n_saved = self.n_saved
        self.agent.n_carrying = self.n_carrying
        self.agent.terminated = self.is_terminated

