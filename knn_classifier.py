#!/usr/bin/env python3

import os
import sys
import json
import numpy as np
import matplotlib.pyplot as plt

from sklearn.neighbors import KNeighborsClassifier
from feature_selection import *
from load_blocks import load_or_download_blocks
from prepare_training_data import CLIENTS

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
    # TODO: modularise so we can turn features on and off
    # single_bit_percent = safe_div(feat_num_single_bit(block_reward), num_attestations)

    num_ordered = feat_num_pairwise_ordered(block_reward)
    ordered_percent = safe_div(num_ordered + 1, num_attestations)

    reward_norm = feat_total_reward_norm(block_reward)

    return [redundant_percent, ordered_percent, reward_norm]

class Classifier:
    def __init__(self, data_dir):
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

        knn = KNeighborsClassifier(n_neighbors=K, weights=WEIGHTS)
        knn.fit(feature_matrix, training_labels)
        score = knn.score(feature_matrix, training_labels)

        self.knn = knn
        self.score = score
        self.enabled_clients = enabled_clients

        self.feature_matrix = feature_matrix
        self.training_labels = training_labels

    def classify(self, block_reward):
        res = self.knn.predict_proba([into_feature_row(block_reward)])

        prob_by_client = {client: res[0][i] for i, client in enumerate(self.enabled_clients)}

        multilabel = compute_multilabel(compute_guess_list(prob_by_client, self.enabled_clients))

        label = compute_best_guess(prob_by_client)

        return (label, multilabel, prob_by_client)

    def plot_feature_matrix(self, output_path):
        fig = plt.figure()

        ax = fig.add_subplot(projection='3d')

        x = self.feature_matrix[:, 0]
        y = self.feature_matrix[:, 1]
        z = self.feature_matrix[:, 2]

        scatter = ax.scatter(x, y, z, c=self.training_labels, marker=".", alpha=0.25, cmap="Set1")

        handles, _ = scatter.legend_elements()
        labels = self.enabled_clients

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
    return max(probability_map.keys(), key=lambda client: probability_map[client], default="Unknown")

def main():
    data_dir = sys.argv[1]
    classify_dir = sys.argv[2]

    classifier = Classifier(data_dir)

    print(f"classifier score: {classifier.score}")

    classifier.plot_feature_matrix("knn.svg")

    frequency_map = {}
    total_blocks = 0

    for input_file in os.listdir(classify_dir):
        print(f"classifying rewards from file {input_file}")
        with open(os.path.join(classify_dir, input_file), "r") as f:
            block_rewards = json.load(f)

        for block_reward in block_rewards:
            _, multilabel, prob_by_client = classifier.classify(block_reward)

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
