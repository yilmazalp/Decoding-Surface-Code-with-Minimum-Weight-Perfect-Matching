import random
import networkx as nx
import numpy as np
import pandas as pd
import itertools
import matplotlib.pyplot as plt

# we have 13 data qubits
data_qubits = [0,1,2,3,4,5,6,7,8,9,10,11,12]

# determine x-type checks based on data qubits
x_stabilizers = {
    0: [0, 3, 5],
    1: [1, 3, 4, 6],
    2: [2, 4, 7],
    3: [5, 8, 10],
    4: [6, 8, 9, 11],
    5: [7, 9, 10],
}

# determine z-type checks based on data qubits
z_stabilizers = {
    0: [0, 1, 3],
    1: [1, 2, 4],
    2: [3, 5, 6, 8],
    3: [4, 6, 7, 9],
    4: [8, 10, 11],
    5: [9, 11, 12],
}

# extract z_syndrome
def extract_z_syndrome(error_qubits, x_stabilizers) -> list:

    syndrome_list = []

    for check in x_stabilizers:
        count = 0

        for qubit in error_qubits:
            if qubit in x_stabilizers[check]:
                count = (count +1)%2

        if count == 1:
            syndrome_list.append(check)

    return syndrome_list


# extract x_syndrome
def extract_x_syndrome(error_qubits, z_stabilizers) -> list:

    syndrome_list = []

    for check in list(z_stabilizers.keys()):
        count = 0
        for qubit in error_qubits:
            if qubit in z_stabilizers[check]:
                count = (count +1)%2
        if count == 1:
            syndrome_list.append(check)

    return syndrome_list

# generate Z errors
def generate_z_error(number_of_data_qubits: int, p: float) -> list[int]:
    error_qubits = []

    for qubit in range(number_of_data_qubits):
        random_number = random.random()
        if random_number < p:
            error_qubits.append(qubit)

    return error_qubits

# compute distance
def compute_distance(p1, p2):
    return sum(abs(a - b) for a, b in zip(p1, p2))

x_coordinates = {
        0: (0, 0),
        1: (1, 0),
        2: (2, 0),
        3: (0, 1),
        4: (1, 1),
        5: (2, 1),
    }


# build the syndrome graph
def build_z_graph(syndrome: list):
    G = nx.Graph()
    G.add_nodes_from(syndrome)

    weighted_edges = [(u,v, compute_distance(x_coordinates[u],x_coordinates[v]))
                      for u,v in itertools.combinations(G.nodes, 2)]

    G.add_weighted_edges_from(weighted_edges)

    return G

# getting minimum-weight perfect matchings
def generate_matchings(nodes):
    if len(nodes) == 0:
        return [[]]

    first = nodes[0]
    matchings = []

    for i in range(1, len(nodes)):
        partner = nodes[i]

        remaining_nodes = nodes[1:i] + nodes[i+1:]
        remaining_matchings = generate_matchings(remaining_nodes)

        # recursive matching
        for matching in remaining_matchings:
            matchings.append([(first, partner)] + matching)

    return matchings

# find the minimum weight perfect matching
def minimum_weight_of_perfect_matchings(graph):
    matchings = generate_matchings(graph.nodes)
    weight_sum_list = []

    for matches in matchings:
        weight_sum = 0
        for edge in matches:
            weight_sum += graph.get_edge_data(edge[0], edge[1])["weight"]
        weight_sum_list.append(weight_sum)

    minimum_weight = min(weight_sum_list)
    min_weight_index = weight_sum_list.index(minimum_weight)

    return minimum_weight, matchings[min_weight_index]

#build the decoding graph
def decoding_graph(x_check_list, data_qubits):
    G = nx.Graph()

    G.add_nodes_from(x_stabilizers.keys())


    for qubit in data_qubits:

        checks = []

        for check in x_stabilizers:
            if qubit in x_stabilizers[check]:
                checks.append(check)

        if len(checks)==2:
            G.add_edge(checks[0], checks[1], qubit=qubit, weight=1)

    return G


G = build_z_graph([0, 5])

pos = {node: x_coordinates[node] for node in G.nodes}

nx.draw(G, pos=pos, with_labels=True, node_color="lightblue", node_size=500)

edge_labels = nx.get_edge_attributes(G, "weight")
nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)

plt.show()
