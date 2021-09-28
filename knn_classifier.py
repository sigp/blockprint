#!/usr/bin/env python3

import os
import sys
import json

from sklearn.neighbors import KNeighborsClassifier
from feature_selection import *
from load_blocks import load_or_download_blocks
from prepare_training_data import classify_rewards_and_blocks_by_graffiti, CLIENTS

# K = 1
# WEIGHTS = "uniform"

K = 5
WEIGHTS = "distance"

MIN_GUESS_THRESHOLD = 0.20
CONFIDENCE_THRESHOLD = 0.75

def into_feature_row(block_reward):
    num_attestations = feat_num_attestations(block_reward)
    num_redundant = feat_num_redundant(block_reward)
    num_ordered = feat_num_pairwise_ordered(block_reward)
    ordered_percent = (num_ordered + 1) / num_attestations
    redundant_percent = num_redundant / num_attestations

    return [redundant_percent, ordered_percent]

def init_classifier(data_dir):
    feature_matrix = []
    training_labels = []

    for client in CLIENTS:
        client_dir = os.path.join(data_dir, client)

        for reward_file in os.listdir(client_dir):
            with open(os.path.join(client_dir, reward_file), "r") as f:
                block_reward = json.load(f)

            feature_matrix.append(into_feature_row(block_reward))
            training_labels.append(client)

    knn = KNeighborsClassifier(n_neighbors=K, weights=WEIGHTS)
    knn.fit(feature_matrix, training_labels)
    score = knn.score(feature_matrix, training_labels)

    return knn, score

def compute_guess_list(probability_map) -> list:
    guesses = []
    for client in CLIENTS:
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

def main():
    data_dir = sys.argv[1]

    classifier, score = init_classifier(data_dir)

    print(f"classifier score: {score}")

    input_file = sys.argv[2]
    with open(input_file, "r") as f:
        block_rewards = json.load(f)

    frequency_map = {}

    for block_reward in block_rewards:
        res = classifier.predict_proba([into_feature_row(block_reward)])

        prob_by_client = {client: res[0][i] for i, client in enumerate(CLIENTS)}

        multilabel = compute_multilabel(compute_guess_list(prob_by_client))

        if multilabel not in frequency_map:
            frequency_map[multilabel] = 0

        frequency_map[multilabel] += 1

    for multilabel, num_blocks in sorted(frequency_map.items()):
        percentage = round(num_blocks / len(block_rewards), 3)
        print(f"{multilabel},{percentage}")

if __name__ == "__main__":
    main()
