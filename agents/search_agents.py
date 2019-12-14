from environment import Environment, EvacuateNode
from utils.data_structures import Stack
from agents.base_agents import Human
from search_tree import SearchTree
from configurator import Configurator, debug
from action import Action


class SearchAgent(Human):
    """Base class for search agents"""

    def __init__(self, name, start_loc: EvacuateNode, max_expand=float('inf')):
        super().__init__(name, start_loc)
        self.strategy: Stack[Action] = Stack()
        self.max_expand = max_expand

    def get_strategy(self, env: Environment):
        if not self.strategy.is_empty():
            return  # strategy already exists
        # performance measure - account for tree expansion time constant T
        self.time += self.max_expand * Configurator.T
        expand_count, self.strategy = SearchTree(env, self).tree_search(max_expand=self.max_expand)
        debug('expand count = {}'.format(expand_count))
        self.describe_strategy()

    def describe_strategy(self):
        print('\nStrategy for {}:'.format(self.name))
        print('number of actions: {}'.format(len(self.strategy.stack)))
        for action in reversed(self.strategy.stack):
            action.describe()

    def act(self, env: Environment):
        """pop the next action in strategy and execute it"""
        if not self.is_available(env):
            return
        if self.strategy.is_empty():
            self.get_strategy(env)
        self.strategy.pop().execute()


class GreedySearch(SearchAgent):
    """A search agent that expands one node at a time in a search tree when devising a strategy"""
    def __init__(self, name, start_loc: EvacuateNode):
        super().__init__(name, start_loc, max_expand=1)


class AStar(SearchAgent):
    """A search agent with an unlimited amount of expansions in a search tree when devising a strategy"""
    def __init__(self, name, start_loc: EvacuateNode):
        super().__init__(name, start_loc, max_expand=100000)


class RTAStar(SearchAgent):
    """A search agent that expands a limited number of nodes at a time in a search tree when devising a strategy"""
    def __init__(self, name, start_loc: EvacuateNode):
        super().__init__(name, start_loc, max_expand=Configurator.limit)

    def act(self, env: Environment):
        """RTA* does only one move at a time and then recalculates from scratch"""
        super().act(env)
        while not self.strategy.is_empty():
            self.strategy.pop()
