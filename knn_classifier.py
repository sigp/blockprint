#!/usr/bin/env python3

import sys
import json

from sklearn.neighbors import KNeighborsClassifier
from feature_selection import *
from load_blocks import load_or_download_blocks
from prepare_training_data import classify_rewards_and_blocks_by_graffiti, CLIENTS

K = 1

def into_feature_row(rewards, block):
    num_attestations = len(block["data"]["message"]["body"]["attestations"])
    num_redundant = feat_num_redundant(rewards)
    num_ordered = feat_num_pairwise_ordered(rewards)
    ordered_percent = (num_ordered + 1) / num_attestations

    return [num_redundant, ordered_percent]

def train_classifier(all_rewards, all_blocks):
    training_set = classify_rewards_and_blocks_by_graffiti(all_rewards, all_blocks)

    # Transform training set to feature matrix
    # TODO: use numpy here
    feature_matrix = []
    training_labels = []
    for (client, examples) in training_set.items():
        for (rewards, block) in examples:
            feature_matrix.append(into_feature_row(rewards, block))
            training_labels.append(client)

    knn = KNeighborsClassifier(n_neighbors=K)
    knn.fit(feature_matrix, training_labels)
    score = knn.score(feature_matrix, training_labels)

    return knn, score

def main():
    input_file = sys.argv[1]
    with open(input_file, "r") as f:
        all_rewards = json.load(f)

    blocks = load_or_download_blocks(all_rewards)

    classifier, score = train_classifier(all_rewards, blocks)

    print(f"classifier score: {score}")

    frequency_map = {client: 0 for client in CLIENTS}

    for rewards, block in zip(all_rewards, blocks):
        res = classifier.predict([into_feature_row(rewards, block)])
        label = res[0]
        frequency_map[label] += 1

    for client in CLIENTS:
        percentage = round(frequency_map[client] / len(rewards), 3)
        print(f"{client},{percentage}")

if __name__ == "__main__":
    main()
