from utils.data_structures import Node, Edge, Graph, Heap, Stack
from copy import copy as shallow_copy
from typing import Dict, Set, TypeVar, Union
from action import Action, ActionType
from configurator import Configurator

AgentType = TypeVar('Agent')


def debug(s):
    if Configurator.debug:
        print(s)


class EvacuateNode(Node):
    """Represents a node with people that are waiting for evacuation"""
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
        return '{}\n(D{}|P{}/{})'\
                .format(self.label, self.deadline, self.n_people, self.n_people_initial) + Node.summary(self)

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
        self.agent.describe()
        print("require evac={}".format(self.require_evac_nodes))


class Environment:
    def __init__(self, G,
                 time=0,
                 agents=[],
                 blocked_edges: Set[Edge] = set([])):
        self.G: Graph = G
        self.time = time
        self.agents = agents
        self.agent_actions = {}
        self.require_evac_nodes: Set[EvacuateNode] = self.init_required_evac_nodes()
        self.blocked_edges = blocked_edges
        self.max_ticks = self.get_max_ticks()

    def tick(self):
        self.time += 1
        self.execute_agent_actions()

    def all_terminated(self):
        return all([agent.terminated for agent in self.agents])

    def get_max_ticks(self):
        return max([v.deadline for v in self.G.get_vertices()]) + 1

    def init_required_evac_nodes(self):
        return set([v for v in self.G.get_vertices() if (not v.is_shelter() and not v.evacuated)])

    def get_blocked_edges(self):
        return shallow_copy(self.blocked_edges)

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
                debug('\n[EXECUTING]' + action.description)
                action.execute()
            del self.agent_actions[self.time]

    def get_state(self, agent:AgentType):
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


class Plan:
    def __init__(self, cost,
                 state: State,
                 action: Action=None,
                 parent=None):
        self.cost = cost
        self.state = state
        self.action = action
        self.parent = parent

    def __lt__(self, other):
        """cost comparator. Tie-breaker prefers non-goal states to provide a chance to get better results"""
        return (self.cost, self.state.is_goal()) < (other.cost, other.state.is_goal())
        # return (self.cost, not self.state.is_goal()) < (other.cost, not other.state.is_goal())

    def summary(self):
        term = 'T' if self.state.agent_state.terminated else ''
        return "({0},{1.loc}|S{1.n_saved}|C{1.n_carrying}|{2}|{3})"\
            .format(self.cost, self.state.agent_state, term, self.state.require_evac_nodes)


class SearchTree:
    def __init__(self, env: Environment, agent):
        self.agent = agent
        self.env = env
        self.root = self.get_root_node()
        self.fringe: Heap[Plan] = Heap([self.root])
        self.hist = [] # used for debug

    def get_initial_state(self):
        return self.env.get_state(self.agent)

    def get_root_node(self):
        return Plan(
            cost=0,
            action=Action(agent=self.agent, description='Root of the tree'),
            parent=None,
            state=self.get_initial_state())

    def restore_env(self):
        """restore environment to actual state after finding a strategy"""
        self.env.apply_state(self.root.state)

    def backtrack(self, goal):
        """backtrack through nodes from goal to root, pushing to the stack each step, returning the agent's strategy """
        strategy = Stack()
        curr_node: Plan = goal
        while curr_node.parent is not None:
            strategy.push(curr_node.action)
            curr_node = curr_node.parent
        self.restore_env()
        # self.display()
        return strategy

    def tree_search(self, max_expand=1000000):
        """initialize state tree using the initial state of problem"""
        expand_count = 0
        while True:
            # if there are no candidates for expansion, return fail
            if self.fringe.is_empty():
                raise Exception("Tree search failed!")
            # choose which node to expand based on strategy: use heuristic to determine the best option to expand
            print([p.cost for p in self.fringe.heap])
            option = self.fringe.extract_min()
            self.hist.append(option) # for debug
            debug("Goal checking node with cost = {}:".format(option.cost))
            # if the node contains a goal state, return the solution
            if option.state.is_goal():
                # check if the chosen node is a goal node
                print("goal reached:")
                option.state.describe()
                return expand_count, self.backtrack(option)
            if expand_count < max_expand:
                # otherwise, expand the node
                self.expand_node(option)
                expand_count += 1
            else:
                return option

    def heuristic(self, state: State=None):
        """given a state for an agent, returns how many people cannot be saved by the agent"""
        self.env.apply_state(state)
        agent = state.agent
        src = agent.loc
        self.env.G.dijkstra(src)
        V = self.env.G.get_vertices()
        require_evac_nodes = [v for v in self.env.require_evac_nodes if v != src]
        # find nodes that can be reached before hurricane hits them. create (node, required_pickup_time) pairs
        evac_candidates, doomed_nodes = [], []
        for v in require_evac_nodes:
            if self.env.time + v.d > v.deadline:
                doomed_nodes.append(v) # nodes we cannot save from the imminent hurricane
            else:
                evac_candidates.append((v, self.env.time + v.d, list(self.env.G.get_shortest_path(src, v))))
        for u, time_after_pickup, pickup_shortest_path in evac_candidates:
            self.env.G.dijkstra(u) # calculate minimum distance from node after pickup
            shelter_candidates = [(v, time_after_pickup + v.d, list(self.env.G.get_shortest_path(u, v))) for v in V
                                  if v.is_shelter() and time_after_pickup + v.d <= v.deadline]
            if not shelter_candidates:
                doomed_nodes.append(u)
            debug('\npossible routes for evacuating {}:'.format(u))
            for shelter, total_time, dropoff_shortest_path in shelter_candidates:
                debug('pickup:(T{}){}(T{}) | drop-off:{}(T{}): Shelter(D{})'.format(self.env.time,
                                                                                    pickup_shortest_path,
                                                                                    time_after_pickup,
                                                                                    dropoff_shortest_path,
                                                                                    total_time,
                                                                                    shelter.deadline))
        n_doomed_people = sum([v.n_people for v in doomed_nodes])
        debug('h(x) = {} [= # of doomed people (doomed_nodes = {})]'.format(n_doomed_people, doomed_nodes))
        return n_doomed_people

    def total_cost(self, state):
        # assumes environment's state was updated before calling this function
        h = 0 if state.is_goal() else self.heuristic(state)
        g = state.agent.penalty
        print('cost = g + h = {} + {} = {}'.format(g, h, g+h))
        return g + h

    def expand_node(self, plan: Plan):
        """Expands fridge, adding (path, state) pair of all possible moves."""
        self.env.apply_state(plan.state)
        agent = plan.state.agent
        debug("Expanding node with cost = {}:".format(plan.cost))
        plan.state.describe()
        neighbours = agent.get_possible_steps(self.env, verbose=True) # options to proceed
        for dest in neighbours + [ActionType.TERMINATE]:
            action, result_state = self.successor(plan.state, dest)
            debug("\ncreated state:")
            result_state.describe()
            cost = self.total_cost(result_state)
            new_plan = Plan(cost=cost,
                            state=result_state,
                            action=action,
                            parent=plan)
            self.fringe.insert(new_plan)

    def successor(self, state: State, dest: Union[EvacuateNode, ActionType]):
        """
        :param state: a state of the environment in the search tree node
        :param dest: a destination node (GOTO action) or ActionType.TERMINATE (for terminate action)
        :return: (action,state) action resulting in the successor state
        """
        self.env.apply_state(state)
        agent = state.agent
        if dest == ActionType.TERMINATE:
            def terminate_agent():
                agent.terminate(self.env)
            action = Action(
                agent=agent,
                description='*[T={:>3}] "TERMINATE" action for {}'.format(agent.time, agent.name),
                callback=terminate_agent)
            agent.local_terminate()
        else:
            def move_agent():
                agent.goto2(self.env, dest)
            action = Action(
                agent=agent,
                description='*[T={:>3}] "GOTO {}->{}" action for {}'.format(agent.time, agent.loc, dest, agent.name),
                callback=move_agent)
            agent.local_goto(self.env, dest)
        action.describe()
        return action, self.env.get_state(agent)

    def display(self):
        nodes = self.hist + self.fringe.heap
        id = 0
        for p in nodes:
            id += 1
            p.tmp = p.summary() + str(id)

        V = [Node(p.tmp) for p in nodes]
        E = [Edge(p.tmp, p.parent.tmp) for p in nodes if p.parent]
        G = Graph(V,E)
        G.display('SEARCH TREE')