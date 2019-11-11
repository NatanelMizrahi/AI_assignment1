import os
import heapq
import networkx as nx
import matplotlib.pyplot as plt
from heapq import _siftup, _siftdown
from typing import List, Dict, Tuple


class Pair:
    def __init__(self,k,v):
        self.k = k
        self.v = v

    def __lt__(self, other):
        return self.k < other.k

    def __eq__(self, other):
        return self.k == other.k and self.v == other.v

    def __repr__(self):
        return str((self.k, str(self.v)))

    def __hash__(self):
        return hash((self.k, self.v))


class Heap:
    def __init__(self, elements: List[Pair]):
        heapq.heapify(elements)
        self.heap = elements
        self.set = set([e.v for e in elements])

    def insert(self, element):
        heapq.heappush(self.heap, element)
        self.set.add(element.v)

    def insert_many(self, elements):
        for element in elements:
            self.insert(element)

    def extract_min(self):
        min = heapq.heappop(self.heap)
        self.set.remove(min.v)
        return min

    def is_empty(self):
        return len(self.heap) == 0

    def is_min_heap(arr):
        return all(arr[i] >= arr[(i - 1) // 2] for i in range(1, len(arr)))

    def siftdown(self, pos):
        _siftdown(self.heap, 0, pos)

    def update_element(self, old, new):
        i = self.heap.index(old)
        self.heap[i] = new
        if old > new:     # value is increased
            _siftup(self.heap, i)
        elif old < new:   # value is decreased
            _siftdown(self.heap, 0, i)


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
    '''A base Node class for nodes used in the Graph class'''
    def __init__(self,label):
        self.label = label
        # disjkstra algorithm aux variables:
        self.d = 0
        self.prev = None

    def __str__(self):
        return self.label

    def __eq__(self, other):
        return str(self) == str(other)

    def __hash__(self):
        return hash(self.label)

    def describe(self):
        return self.label

    def summary(self):
        return '' if not self.prev else '\nD[{}];P[{}]'.format(self.d, self.prev.label)


class Edge:
    def __init__(self, v1: Node, v2:Node, w=0, name=''):
        self.name = name
        self.v1 = v1
        self.v2 = v2
        self.w = w

    def get(self):
        return (self.v1, self.v2, self.w)

    def reverse(self):
        return Edge(self.v2, self.v1, self.w, self.name + '_')

    def __eq__(self, other):
        return self.v1 == other.v1 and self.v2 == other.v2

    def __str__(self):
        return str((self.v1.label, self.v2.label, self.w))

    def __hash__(self):
        return hash((self.v1, self.v2))

class Graph:
    def __init__(self, V:List[Node]=[],E:List[Edge]=[]):
        self.pos = None # to maintain vertex position in visualization
        self.n_vertices = 0
        self.V:   Dict[Node, List[Node]]     = {}
        self.Adj: Dict[Tuple[Node,Node],Edge]= {}
        self.init(V, E)

    def init(self, V:List[Node], E:List[Edge]):
        '''initialize graph with list of nodes and a list of edges'''
        for v in V: self.add_vertex(v)
        for e in E: self.add_edge(e)

    def add_vertex(self, v):
        if v in self.V:
            raise Exception("{} already exists in V".format(v))
        self.V[v] = set([])
        self.n_vertices += 1

    def add_edge(self, e: Edge):
        v1 = e.v1
        v2 = e.v2
        if (not v1 in self.V) or (not v2 in self.V):
            raise Exception("{} or {} are not in V".format(v1,v2))
        if self.Adj.get((v1,v2)):
            raise Exception("({},{}) already exists in E".format(v1,v2))

        self.V[v1].add(v2)
        self.V[v2].add(v1)
        self.Adj[v1,v2] = e
        self.Adj[v2,v1] = e.reverse()

    def remove_edge(self, v1, v2):
        if (not v1 in self.V) or (not v2 in self.V):
            raise Exception("{} or {} are not in V".format(v1,v2))
        if not self.Adj.get((v1,v2)):
            print("({},{}) not in E".format(v1,v2))
        self.V[v1].remove(v2) # adjacency list is a set
        self.V[v2].remove(v1)
        del self.Adj[v1,v2]
        del self.Adj[v2,v1]

    def remove_vertex(self, v):
        if (not v in self.V):
            raise Exception("{} not in V".format(v))
        for u in self.V[v]:
            self.remove_edge(v,u)
        self.n_vertices -= 1

    def neigbours(self, v):
            return self.V[v]

    def get_vertices(self):
        return self.V.keys()

    def get_edge(self, v1, v2):
        return self.Adj[v1,v2]

    def print_adj(self):
        for u, ns in self.V.items():
            print(u, ': ' + ','.join([str(v) for v in ns]))

    def display(self, graph_id=0, output_path='.', save_img=False):
        filename = '{0}/graph_{1}.png'.format(output_path, graph_id)
        V = self.get_vertices()
        G = nx.Graph()
        G.add_nodes_from(V)
        G.add_weighted_edges_from([e.get() for e in self.Adj.values()])
        edge_labels = nx.get_edge_attributes(G, 'weight')
        node_labels = {v: v.describe() for v in G.nodes()}
        if G.number_of_nodes() == 0:
            return
        if self.pos is None:
            self.pos = nx.spring_layout(G)
        nx.draw(G, self.pos, node_size=1700, with_labels=False)
        nx.draw_networkx_edge_labels(G, self.pos, edge_labels=edge_labels, rotate=False)
        nx.draw_networkx_labels(G, self.pos, node_labels, font_size=9, font_weight='bold')
        plt.margins(0.2)
        plt.legend([], title=graph_id, loc='upper center')
        plt.show()
        if save_img:
            print("Creating graph visualization: " + os.path.abspath(filename))
            plt.savefig(filename)

    @staticmethod
    def shortest_path_successor(src, target):
        v = target
        while v.prev != src:
            v = v.prev
        return v

    def dijkstra(self, s):
        '''
        :param s: source vertex
        :return: at the end of this method, foreach v in V: v.d = dist from source and v.prev = previous in shortest path to source
        '''
        inf = float('inf')
        V = self.get_vertices()
        for v in V:
            v.d = inf
            v.prev = None
        s.d = 0
        Q = Heap([Pair(v.d, v) for v in V])
        while not Q.is_empty():
            pair = Q.extract_min()
            u = pair.v
            for v in self.neigbours(u):
                if v in Q.set:
                    tmp = u.d + self.Adj[u,v].w # w(u,v)
                    if tmp < v.d:
                        Q.update_element(Pair(v.d,v), Pair(tmp,v))
                        v.d = tmp
                        v.prev = u
        #TODO: return dist, prev for each node