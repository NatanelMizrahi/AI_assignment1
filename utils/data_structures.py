import os
import heapq
import networkx as nx
import matplotlib.pyplot as plt
from heapq import _siftdown
from typing import List, Dict, Tuple


class Heap:
    def __init__(self, elements: List=[]):
        heapq.heapify(elements)
        self.heap = elements
        self.set = set(elements)

    def insert(self, element):
        heapq.heappush(self.heap, element)
        self.set.add(element)

    def insert_many(self, elements):
        for element in elements:
            self.insert(element)

    def extract_min(self):
        min_item = heapq.heappop(self.heap)
        self.set.remove(min_item)
        return min_item

    def is_empty(self):
        return len(self.heap) == 0

    def is_min_heap(self):
        return all(self.heap[i] >= self.heap[(i - 1) // 2] for i in range(1, len(self.heap)))

    def siftdown(self, pos):
        _siftdown(self.heap, 0, pos)

    def decrease_key(self, item):
        idx = self.heap.index(item)
        _siftdown(self.heap, 0, idx)

    def __str__(self):
        return str([str(e) for e in self.set])


class Stack:
    def __init__(self):
        self.stack = []

    def is_empty(self):
        return len(self.stack) == 0

    def push(self, element):
        self.stack.append(element)

    def pop(self):
        try:
            return self.stack.pop()
        except:
            raise Exception("Error: {} empty!!".format(self.__class__.__name__))


class Queue(Stack):
    def push(self, element):
        self.stack.insert(0, element)


## GRAPH ##
class Node:
    """A base Node class for nodes used in the Graph class"""

    def __init__(self, label):
        self.label = label
        # dijkstra algorithm aux variables:
        self.d = 0
        self.prev = None

    def __str__(self):
        return self.label

    def __eq__(self, other):
        return str(self) == str(other)

    def __lt__(self, other):
        return self.d < other.d

    def __hash__(self):
        return hash(self.label)

    def __repr__(self):
        return self.label

    def describe(self):
        return self.label

    def summary(self):
        return '' # if not self.prev else '\nD[{}];P[{}]'.format(self.d, self.prev.label)


class Edge:
    def __init__(self, v1: Node, v2: Node, w=0, name=''):
        """edge created lexicographically by its vertices names"""
        if v2 < v1:
            v1, v2 = v2, v1  #
        self.name = name
        self.v1 = v1
        self.v2 = v2
        self.w = w
        self.blocked = False
        self.deadline = float('inf')

    def get(self):
        return self.v1, self.v2, self.w

    def __eq__(self, other):
        return self.v1 == other.v1 and self.v2 == other.v2

    def __str__(self):
        return str((self.v1.label, self.v2.label, self.w))

    def __repr__(self):
        return '({},{})'.format(self.v1.label, self.v2.label)

    def __hash__(self):
        return hash((self.v1, self.v2))


class Graph:
    """Graph with blockable edges"""

    def __init__(self, V: List[Node]=[], E: List[Edge]=[]):
        self.pos = None  # used to maintain vertices position in visualization
        self.n_vertices = 0
        self.V: Dict[Node, List[Node]] = {}
        self.Adj: Dict[Tuple[Node, Node], Edge] = {}
        self.init(V, E)

    def init(self, V: List[Node], E: List[Edge]):
        """initialize graph with list of nodes and a list of edges"""
        for v in V: self.add_vertex(v)
        for e in E: self.add_edge(e)

    def add_vertex(self, v):
        if v in self.V:
            raise Exception("{} already exists in V".format(v))
        self.V[v] = set([])
        self.n_vertices += 1

    def remove_vertex(self, v):
        if v not in self.V:
            raise Exception("{} not in V".format(v))
        for u in self.V[v]:
            self.remove_edge(v, u)
        self.n_vertices -= 1

    def get_edge(self, v1, v2):
        return self.Adj.get((v1, v2))

    def edge_exists_check(self, v1, v2, expected: bool):
        if (v1 not in self.V) or (v2 not in self.V):
            raise Exception("{} or {} are not in V".format(v1, v2))
        edge_exists = self.get_edge(v1, v2)
        if edge_exists and not expected:
            raise Exception("({},{}) already exists in E".format(v1, v2))
        elif not edge_exists and expected:
            raise Exception("({},{}) doesn't exist in E".format(v1, v2))

    def add_edge(self, e: Edge):
        v1 = e.v1
        v2 = e.v2
        self.edge_exists_check(v1, v2, expected=False)
        self.V[v1].add(v2)
        self.V[v2].add(v1)
        self.Adj[v1, v2] = e
        self.Adj[v2, v1] = e

    def remove_edge(self, v1, v2):
        self.edge_exists_check(v1, v2, expected=True)
        self.V[v1].remove(v2)
        self.V[v2].remove(v1)
        del self.Adj[v1, v2]
        del self.Adj[v2, v1]

    def block_edge(self, v1, v2, block_time):
        self.edge_exists_check(v1, v2, expected=True)
        e = self.get_edge(v1, v2)
        e.blocked = True
        e.deadline = block_time

    def is_blocked(self, u, v):
        return self.get_edge(u, v).blocked

    def neighbours(self, u):
        return [v for v in self.V[u] if not self.is_blocked(u, v)]

    def get_vertices(self):
        return self.V.keys()

    def get_edges(self):
        return self.Adj.values()

    def display(self, graph_id=0, output_path='.', save_img=False):
        # if not Configurator.interactive:
        #     return
        filename = '{0}/graph_{1}.png'.format(output_path, graph_id)
        V = self.get_vertices()
        G = nx.Graph()
        G.add_nodes_from(V)
        G.add_weighted_edges_from([e.get() for e in self.Adj.values() if not e.blocked])
        edge_labels = nx.get_edge_attributes(G, 'weight')
        node_labels = {v: v.describe() for v in G.nodes()}
        if G.number_of_nodes() == 0:
            return
        if self.pos is None:
            # save node position to maintain the same graph layout throughout simulations
            self.pos = nx.spring_layout(G, scale=25)
        nx.draw(G, self.pos, node_size=1700, with_labels=False)
        nx.draw_networkx_edge_labels(G, self.pos, edge_labels=edge_labels, rotate=False)
        nx.draw_networkx_labels(G, self.pos, node_labels, font_size=7.5, font_weight='bold')
        plt.margins(0.2)
        plt.legend([], title=graph_id, loc='upper center')
        plt.show()
        if save_img:
            print("Saving graph visualization: " + os.path.abspath(filename))
            plt.savefig(filename)

    @staticmethod
    def shortest_path_successor(src, target):
        """returns source node's successor in the shortest path to target. Must run dijkstra(src) before calling this function"""
        v = target
        while v.prev != src:
            v = v.prev
        return v

    def get_shortest_path(self, src, target):
        """finds the shortest path from source to target node in graph. Must run dijkstra(src) before calling this function"""
        path = [target]
        v = target
        # len(shortest path) <= |V|- 1
        for i in range(self.n_vertices):
            if v == src:
                return reversed(path)
            v = v.prev
            path.append(v)
        raise Exception('path does not exist: {} -> {}'.format(src, target))

    def print_shortest_paths(self, src):
        """prints all the shortest paths from source node. Must run dijkstra(src) before calling this function"""
        print("shortest paths from: " + src.label)
        for v in self.get_vertices():
            print(v.label + ': ' + '->'.join([v.label for v in self.get_shortest_path(src, v)]))

    def dijkstra(self, s, debug=False):
        """
        :param s: source vertex
        :return: after calling this method, foreach v in V:
                 v.d = dist from source
                 v.prev = previous node in shortest path to source
        """
        inf = float('inf')
        V = self.get_vertices()
        for v in V:
            v.d = inf
            v.prev = None
        s.d = 0
        Q = Heap(list(V))
        while not Q.is_empty():
            u = Q.extract_min()
            if debug: self.display(str(Q) + '; u = ' + u.label)
            for v in self.neighbours(u):
                if v in Q.set:
                    if debug: self.display(str(Q) + '; u = ' + u.label + ', v = ' + v.label)
                    val = u.d + self.Adj[u, v].w  # w(u,v)
                    if val < v.d:
                        v.d = val
                        v.prev = u
                        Q.decrease_key(v)
