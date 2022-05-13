#!/usr/bin/env python3

import os
import shutil
import random
import argparse
from prepare_training_data import CLIENTS


# Sample a directory of training data so that it contains a balanced number of samples per client
def sample(data_dir, output_dir, disabled_clients, max_imbalance):
    filenames_by_client = {}

    for client in CLIENTS:
        if client in disabled_clients:
            print(f"skipping {client} (disabled)")
            continue

        client_dir = os.path.join(data_dir, client)

        if not os.path.exists(client_dir):
            print(f"skipping {client} (no data)")
            continue

        filenames = []
        for filename in os.listdir(client_dir):
            filenames.append(os.path.join(client_dir, filename))

        filenames_by_client[client] = filenames

    min_files = min(len(filenames) for filenames in filenames_by_client.values())
    max_samples = max_imbalance * min_files

    print(
        f"sampling up to {max_samples} ({max_imbalance}x{min_files}) training blocks per client"
    )

    os.makedirs(output_dir)

    for client, filenames in filenames_by_client.items():
        n_samples = min(len(filenames), max_samples)

        selected_files = random.sample(filenames, n_samples)

        client_output_dir = os.path.join(output_dir, client)
        os.makedirs(client_output_dir)

        for filename in selected_files:
            shutil.copy(filename, client_output_dir)


def parse_args():
    parser = argparse.ArgumentParser("re-sample training data so that it is balanced")
    parser.add_argument(
        "input_dir", help="input directory containing unbalanced training data"
    )
    parser.add_argument(
        "output_dir", help="output directory for balanced training data"
    )
    parser.add_argument(
        "--disable",
        default=[],
        nargs="+",
        help="clients to ignore when forming training data",
    )
    parser.add_argument(
        "--max-imbalance",
        metavar="N",
        default=1,
        type=int,
        help="allow clients to have at most N times the minimum training set size",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    sample(args.input_dir, args.output_dir, args.disable, args.max_imbalance)
