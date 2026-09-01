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
# visualization coordinates only
x_coordinates = {
    0: (0, 1),
    1: (2, 1),
    2: (4, 1),
    3: (0, 3),
    4: (2, 3),
    5: (4, 3),
}

z_coordinates = {
    0: (1, 0),
    1: (3, 0),
    2: (1, 2),
    3: (3, 2),
    4: (1, 4),
    5: (3, 4),
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
    matchings = generate_matchings(list(graph.nodes))
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
def decoding_graph(data_qubits):
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

# a helper to extract the correction chain from the matching
def extract_error_chain_from_matching(matching, decoding_G):
    error_chain = []
    path_edges = []
    check_paths = []

    for u, v in matching:
        path = nx.shortest_path(decoding_G, source=u, target=v, weight="weight")
        check_paths.append(path)

        for a, b in zip(path[:-1], path[1:]):
            path_edges.append((a, b))
            error_chain.append(decoding_G[a][b]["qubit"])

    return error_chain, path_edges, check_paths

# plot the syndrome graph and highlight the MWPM edges
def plot_syndrome_graph(syndrome, syndrome_G, matching):
    pos = {node: x_coordinates[node] for node in syndrome_G.nodes}

    plt.figure(figsize=(6, 4))
    nx.draw(syndrome_G, pos=pos, with_labels=True, node_color="lightblue", node_size=700, edge_color="gray")

    edge_labels = nx.get_edge_attributes(syndrome_G, "weight")
    nx.draw_networkx_edge_labels(syndrome_G, pos, edge_labels=edge_labels)

    nx.draw_networkx_nodes(syndrome_G, pos, nodelist=syndrome, node_color="orange",node_size=800)
    nx.draw_networkx_edges(syndrome_G, pos, edgelist=matching, edge_color="red", width=3)

    plt.title("Syndrome graph (red = MWPM)")
    plt.axis("off")
    plt.show()

# plot the decoding graph and highlight the actual correction path
def plot_decoding_graph_with_path(decoding_G, syndrome, matching):
    pos = x_coordinates  # positions of X-checks

    plt.figure(figsize=(6, 4))

    nx.draw(decoding_G, pos=pos, with_labels=True, node_color="lightblue", node_size=700, edge_color="gray")

    # label each decoding-graph edge by the data qubit it represents
    edge_labels = {(u, v): d["qubit"] for u, v, d in decoding_G.edges(data=True)}
    nx.draw_networkx_edge_labels(decoding_G, pos, edge_labels=edge_labels)

    # highlight syndrome checks
    nx.draw_networkx_nodes(decoding_G, pos, nodelist=syndrome, node_color="orange", node_size=800)

    error_chain, path_edges, check_paths = extract_error_chain_from_matching(matching, decoding_G)

    # highlight actual chosen correction path(s)
    nx.draw_networkx_edges(decoding_G, pos, edgelist=path_edges, edge_color="red", width=4)

    plt.title("Decoding graph (red = correction path)")
    plt.axis("off")
    plt.show()

    print("Check paths:", check_paths)
    print("Estimated Z-error chain:", error_chain)

syndrome = [0,1,4,5]

syndrome_graph = build_z_graph(syndrome)

minimum_weight, best_matching = minimum_weight_of_perfect_matchings(syndrome_graph)
print("Minimum weight: ", minimum_weight)
print("Best matching: ", best_matching)

plot_syndrome_graph(syndrome, syndrome_graph, best_matching)
d = decoding_graph(data_qubits)
plot_decoding_graph_with_path(d, syndrome, best_matching)

estimated_error, _, _ = extract_error_chain_from_matching(best_matching, d)

print("Estimated error chain:", estimated_error)
print("Recovered syndrome:", extract_z_syndrome(estimated_error, x_stabilizers))
