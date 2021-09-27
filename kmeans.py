#!/usr/bin/env python3

import sys
import json
import matplotlib.pyplot as plt
import numpy as np

from sklearn.cluster import KMeans
from feature_selection import *
from load_blocks import load_or_download_blocks
from prepare_training_data import get_graffiti, classify_block_by_graffiti

K = 3

def into_feature_row(rewards, block):
    num_attestations = len(block["data"]["message"]["body"]["attestations"])
    num_redundant = feat_num_redundant(rewards)
    num_ordered = feat_num_pairwise_ordered(rewards)

    redundant_percent = num_redundant / num_attestations
    ordered_percent = (num_ordered + 1) / num_attestations

    return [ordered_percent, redundant_percent]

def cluster(all_rewards, all_blocks):
    # Transform training set to feature matrix
    # TODO: numpy usage could probably be more efficient
    feature_matrix = []
    training_labels = []
    for block_rewards, block in zip(all_rewards, all_blocks):
        feature_matrix.append(into_feature_row(block_rewards, block))
    feature_matrix = np.array(feature_matrix)

    kmeans = KMeans(n_clusters=K)
    predictions = kmeans.fit_predict(feature_matrix, training_labels)

    fig, ax = plt.subplots()
    ax.set_xlabel("ordered percent")
    ax.set_ylabel("redundant percent")
    x = feature_matrix[:, 0]
    y = feature_matrix[:, 1]
    ax.scatter(x, y, c=predictions, cmap="Accent")

    for i, block in enumerate(all_blocks):
        graffiti = classify_block_by_graffiti(block)

        if graffiti != None:
            ax.annotate(graffiti, (x[i], y[i]))

    fig.savefig("scatter.svg")

    return kmeans, predictions

def main():
    input_file = sys.argv[1]
    with open(input_file, "r") as f:
        all_rewards = json.load(f)

    blocks = load_or_download_blocks(all_rewards)

    kmeans, predictions = cluster(all_rewards, blocks)

    for block, prediction in zip(blocks, predictions):
        graffiti = get_graffiti(block)
        print(f"\"{graffiti}\",{prediction}")

if __name__ == "__main__":
    main()
