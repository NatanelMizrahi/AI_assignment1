import re
from random import choice as rand_choice
from utils.data_structures import Edge, Graph
from agents.agents import Human, Greedy, Vandal
from environment import Environment, ShelterNode, SimpleNode
from configurator import Configurator

class Simulator:
    '''Hurricane evacuation simulator'''
    def __init__(self):
        self.G = None
        self.parse_graph(path='./config/graph.config')
        self.env = Environment(self.G)

    def parse_graph(self, path):
        '''Parse and create graph from config file, syntax same as in assignment instructions'''
        num_v_pattern          = re.compile("#N\s+(\d+)")
        shelter_vertex_pattern = re.compile("#(V\d+)\s+D(\d+)\s+S")
        person_vertex_pattern  = re.compile("#(V\d+)\s+D(\d+)\s+P(\d+)")
        edge_pattern           = re.compile("#(E\d+)\s+(\d+)\s+(\d+)\s+W(\d+)")

        shelter_nodes = []
        person_nodes  = []
        name_2_node   = {}
        n_vertices = 0
        E = []

        with open(path, 'r') as f:
            for line in f.readlines():
                if not line.startswith('#'):
                    continue

                match = num_v_pattern.match(line)
                if match:
                    n_vertices = int(match.group(1))

                match = shelter_vertex_pattern.match(line)
                if match:
                    name, deadline = match.groups()
                    new_node = ShelterNode(name, deadline)
                    shelter_nodes.append(new_node)
                    name_2_node[new_node.label] = new_node

                match = person_vertex_pattern.match(line)
                if match:
                    name, deadline, n_people = match.groups()
                    new_node = SimpleNode(name, deadline, n_people)
                    person_nodes.append(new_node)
                    name_2_node[new_node.label] = new_node

                match = edge_pattern.match(line)
                if match:
                    name, v1_name, v2_name, weight = match.groups()
                    v1 = name_2_node['V'+v1_name]
                    v2 = name_2_node['V'+v2_name]
                    E.append(Edge(v1, v2, int(weight), name))

        V = person_nodes + shelter_nodes

        self.G = Graph(V, E)
        if n_vertices != self.G.n_vertices:
            raise Exception("Error: |V| != N")

    def init_agents(self):
        shelters = [v for v in self.G.get_vertices() if v.is_shelter()]
        for agent_class in [Human, Greedy, Vandal]:
            start_vertex = rand_choice(shelters)
            new_agent = agent_class(agent_class.__name__ + 'Agent', start_vertex)
            self.env.agents.append(new_agent) # TODO: maybe extend graph
            start_vertex.agents.add(new_agent)

    def run_simple_simulation(self):
        self.init_agents()
        for tick in range(self.env.max_ticks):
            print('T='+str(tick))
            for agent in self.env.agents:
                self.env.G.display('T='+str(tick))
                agent.act(self.env) # TODO: consider time in agent and env
        self.env.G.display('Final State: T=' + str(self.env.max_ticks))


if __name__ == '__main__':
    Configurator.get_user_config()
    sim = Simulator()
    # part I
    sim.run_simple_simulation()