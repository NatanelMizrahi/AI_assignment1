from utils.data_structures import Heap, Stack
from typing import Union
from utils.tree import display_tree
from environment import Environment, Plan, State, EvacuateNode
from configurator import Configurator, debug
from action import Action, ActionType


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
        """creates a root node for the search tree representing the initial state"""
        return Plan(
            cost=0,
            action=None,
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
        self.display()
        return strategy

    def tree_search(self, max_expand=float('inf')):
        """initialize state tree using the initial state of problem"""
        expand_count = 0
        while True:
            # if there are no candidates for expansion, return fail
            if self.fringe.is_empty():
                raise Exception("Tree search failed!")
            # choose which node to expand based on strategy: use heuristic to determine the best option to expand
            option = self.fringe.extract_min()
            self.hist.append(option) # for debug
            # if the node contains a goal state, return the solution
            if option.state.is_goal():
                # check if the chosen node is a goal node
                debug("goal reached:")
                option.state.describe()
                return expand_count, self.backtrack(option)
            elif expand_count < max_expand:
                # otherwise, expand the node
                self.expand_node(option)
                expand_count += 1
            else:
                print('Maximum number of expansions reached. Returning best strategy so far')
                return expand_count, self.backtrack(option)

    def heuristic(self, state: State=None):
        """given a state for an agent, returns how many people cannot be saved by the agent"""
        self.env.apply_state(state)
        agent = state.agent
        src = agent.loc
        self.env.G.dijkstra(src)
        V = self.env.G.get_vertices()
        require_evac_nodes = list(self.env.require_evac_nodes)
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
        debug('h(x) = {} = # of doomed people (doomed_nodes = {})'.format(n_doomed_people, doomed_nodes))
        return n_doomed_people

    def total_cost(self, state):
        # assumes environment's state was updated before calling this function
        h = 0 if state.is_goal() else self.heuristic(state)
        g = state.agent.penalty
        debug('cost = g + h = {} + {} = {}'.format(g, h, g+h))
        return g + h

    def expand_node(self, plan: Plan):
        """Expands fringe, adding (path, state) pair of all possible moves."""
        self.env.apply_state(plan.state)
        agent = plan.state.agent
        debug("Expanding node ID={0.ID} (cost = {0.cost}):".format(plan))
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
            debug("plan ID={}".format(new_plan.ID))
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
        """plots the search tree"""
        if not Configurator.view_strategy:
            return
        state_nodes = self.hist + self.fringe.heap
        for node in state_nodes:
            node.tmp = node.summary() + ' {}'.format(node.ID)
        V = [node.tmp for node in state_nodes]
        E = [(node.tmp, node.parent.tmp) for node in state_nodes if node.parent is not None]
        display_tree(V[0], V, E)
