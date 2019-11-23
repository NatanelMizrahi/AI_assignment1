import re
from configurator import Configurator
from random import choice as rand_choice
from utils.data_structures import Edge
from agents.search_agents import SearchAgent
from environment import Environment, ShelterNode, EvacuateNode, SmartGraph


class Simulator:
    """Hurricane evacuation simulator"""

    def __init__(self):
        self.G: SmartGraph = self.get_graph()
        self.env: Environment = Environment(self.G)
        self.G.env = self.env

    def get_graph(self):
        if Configurator.graph_path is 'random':
            return Configurator.randomize_config()
        else:
            return self.parse_graph(Configurator.graph_path)

    def parse_graph(self, path):
        """Parse and create graph from tests file, syntax same as in assignment instructions"""
        num_v_pattern          = re.compile("#N\s+(\d+)")
        shelter_vertex_pattern = re.compile("#(V\d+)\s+D(\d+)\s+S")
        person_vertex_pattern  = re.compile("#(V\d+)\s+D(\d+)\s+P(\d+)")
        edge_pattern           = re.compile("#(E\d+)\s+(\d+)\s+(\d+)\s+W(\d+)")

        shelter_nodes = []
        person_nodes = []
        name_2_node = {}
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
                    new_node = ShelterNode(name, int(deadline))
                    shelter_nodes.append(new_node)
                    name_2_node[new_node.label] = new_node

                match = person_vertex_pattern.match(line)
                if match:
                    name, deadline, n_people = match.groups()
                    new_node = EvacuateNode(name, int(deadline), int(n_people))
                    person_nodes.append(new_node)
                    name_2_node[new_node.label] = new_node

                match = edge_pattern.match(line)
                if match:
                    name, v1_name, v2_name, weight = match.groups()
                    v1 = name_2_node['V'+v1_name]
                    v2 = name_2_node['V'+v2_name]
                    E.append(Edge(v1, v2, int(weight), name))

        V = person_nodes + shelter_nodes
        print(V)
        print(n_vertices)
        if n_vertices != len(V):
            raise Exception("Error: |V| != N")
        return SmartGraph(V, E)

    def init_agents(self, agents):
        shelters = [v for v in self.G.get_vertices() if v.is_shelter()]
        for agent_class in agents:
            start_vertex = rand_choice(shelters)
            new_agent = agent_class(agent_class.__name__, start_vertex)
            self.env.agents.append(new_agent)
            start_vertex.agents.add(new_agent)
        search_agents_active = any([isinstance(agent, SearchAgent) for agent in self.env.agents])
        if search_agents_active:
            print("SearchAgent(s) active, running a Vandal-only simulation to predict edge blocking deadlines")
            self.env.get_edge_deadlines()

    def run_simulation(self, agents):
        self.init_agents(agents)
        print('** STARTING SIMULATION **')
        while not self.env.all_terminated():
            tick = self.env.time
            print('\nT={}'.format(tick))
            for agent in self.env.agents:
                self.env.G.display('T={}: {}'.format(tick, agent.name))
                agent.act(self.env)
            self.env.tick()
        self.env.G.display('Final State: T=' + str(self.env.time))
