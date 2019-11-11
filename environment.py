from configurator import Configurator
from utils.data_structures import Node


class SimpleNode(Node): #TODO: change name
    '''Represents a node with people that are waiting for evacuation'''
    def __init__(self, label, deadline, n_people=0):
        super().__init__(label)
        self.deadline = int(deadline)
        self.n_people = int(n_people)
        self.n_people_initial = self.n_people
        self.evacuated = False
        self.agents = set([])

    def is_shelter(self):
        return False

    def summary(self):
        return '{}:(D{}|P{}/{})'.format(self.label, self.deadline, self.n_people, self.n_people_initial) + Node.summary(self)

    def describe(self):
        return  self.summary() + '\n' + '\n'.join([agent.summary() for agent in self.agents])


class ShelterNode(SimpleNode):
    '''Represents a node with a shelter'''
    def is_shelter(self):
        return True

    def summary(self):
        return '{}:(D{})'.format(self.label, self.deadline) + Node.summary(self)

    def describe(self):
        return 'Shelter\n' + super().describe()


class Environment:
    def __init__(self, G):
        self.G = G # TODO: is it legal to extend graph?
        self.time = 0
        self.agents = []
        self.max_ticks = self.get_max_ticks()


    def get_state(self):
        return self

    def get_max_ticks(self):
        return max([v.deadline for v in self.G.get_vertices()])