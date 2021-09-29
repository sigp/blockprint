#!/usr/bin/env python3

import os
import sys
import json
import numpy as np
import matplotlib.pyplot as plt

from sklearn.neighbors import KNeighborsClassifier
from feature_selection import *
from load_blocks import load_or_download_blocks
from prepare_training_data import classify_rewards_and_blocks_by_graffiti, CLIENTS

# K = 1
# WEIGHTS = "uniform"

K = 5
WEIGHTS = "distance"

MIN_GUESS_THRESHOLD = 0.20
CONFIDENCE_THRESHOLD = 0.95

def into_feature_row(block_reward):
    num_attestations = feat_num_attestations(block_reward)

    num_redundant = feat_num_redundant(block_reward)
    redundant_percent = safe_div(num_redundant, num_attestations)

    num_ordered = feat_num_pairwise_ordered(block_reward)
    ordered_percent = safe_div(num_ordered + 1, num_attestations)

    reward_norm = feat_total_reward_norm(block_reward)

    return [redundant_percent, ordered_percent, reward_norm]

def init_classifier(data_dir, plot_output=None):
    feature_matrix = []
    training_labels = []

    enabled_clients = []

    for i, client in enumerate(CLIENTS):
        client_dir = os.path.join(data_dir, client)

        if not os.path.exists(client_dir):
            continue
        else:
            enabled_clients.append(client)

        for reward_file in os.listdir(client_dir):
            with open(os.path.join(client_dir, reward_file), "r") as f:
                block_reward = json.load(f)

            feature_matrix.append(into_feature_row(block_reward))
            training_labels.append(i)

    feature_matrix = np.array(feature_matrix)

    if plot_output != None:
        plot_feature_matrix(feature_matrix, training_labels, enabled_clients, plot_output)

    knn = KNeighborsClassifier(n_neighbors=K, weights=WEIGHTS)
    knn.fit(feature_matrix, training_labels)
    score = knn.score(feature_matrix, training_labels)

    return knn, enabled_clients, score

def plot_feature_matrix(feature_matrix, colours, enabled_clients, output_path):
    fig = plt.figure()

    ax = fig.add_subplot(projection='3d')

    x = feature_matrix[:, 0]
    y = feature_matrix[:, 1]
    z = feature_matrix[:, 2]

    scatter = ax.scatter(x, y, z, c=colours, marker=".", alpha=0.25, cmap="Set1")

    handles, _ = scatter.legend_elements()
    labels = enabled_clients

    legend1 = ax.legend(handles, labels, loc="best", title="Client")
    ax.add_artist(legend1)

    ax.set_xlabel("redundant %")
    ax.set_ylabel("ordered %")
    ax.set_zlabel("reward norm")

    fig.savefig(output_path)


def compute_guess_list(probability_map, enabled_clients) -> list:
    guesses = []
    for client in enabled_clients:
        if probability_map[client] > CONFIDENCE_THRESHOLD:
            return [client]
        elif probability_map[client] > MIN_GUESS_THRESHOLD:
            guesses.append(client)
    return guesses

def compute_multilabel(guess_list):
    if len(guess_list) == 1:
        return guess_list[0]
    elif len(guess_list) == 2:
        return f"{guess_list[0]} or {guess_list[1]}"
    else:
        return "Unknown"

def compute_best_guess(probability_map) -> str:
    return max(probability_map.keys(), key=lambda client: probability_map[client])

def classify(classifier, enabled_clients, block_reward):
    res = classifier.predict_proba([into_feature_row(block_reward)])

    prob_by_client = {client: res[0][i] for i, client in enumerate(enabled_clients)}

    multilabel = compute_multilabel(compute_guess_list(prob_by_client, enabled_clients))

    label = compute_best_guess(prob_by_client)

    return (label, multilabel, prob_by_client)

def main():
    data_dir = sys.argv[1]
    classify_dir = sys.argv[2]

    classifier, enabled_clients, score = init_classifier(data_dir, plot_output="knn.svg")

    print(f"classifier score: {score}")

    frequency_map = {}
    total_blocks = 0

    for input_file in os.listdir(classify_dir):
        print(f"classifying rewards from file {input_file}")
        with open(os.path.join(classify_dir, input_file), "r") as f:
            block_rewards = json.load(f)

        for block_reward in block_rewards:
            _, multilabel, prob_by_client = classify(classifier, enabled_clients, block_reward)

            if multilabel not in frequency_map:
                frequency_map[multilabel] = 0

            frequency_map[multilabel] += 1

        total_blocks += len(block_rewards)

    print(f"total blocks processed: {total_blocks}")

    for multilabel, num_blocks in sorted(frequency_map.items()):
        percentage = round(num_blocks / total_blocks, 4)
        print(f"{multilabel},{percentage}")

if __name__ == "__main__":
    main()
