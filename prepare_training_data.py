#!/usr/bin/env python3

import os
import re
import sys
import json
import multiprocessing
import concurrent.futures
import functools
import argparse

from load_blocks import store_block_rewards

# In lexicographic order, as that's what SciKit uses internally
CLIENTS = ["Lighthouse", "Lodestar", "Nimbus", "Other", "Prysm", "Teku"]

REGEX_PATTERNS = {
    "Lighthouse": [r".*[Ll]ighthouse", r"RP-[A-Z]?L v[0-9]*\.[0-9]*\.[0-9]*.*"],
    "Teku": [r".*[Tt]eku", r"RP-[A-Z]?T v[0-9]*\.[0-9]*\.[0-9]*.*"],
    "Nimbus": [r".*[Nn]imbus", r"RP-[A-Z]?N v[0-9]*\.[0-9]*\.[0-9]*.*"],
    "Prysm": [r".*[Pp]rysm", "prylabs", r"RP-[A-Z]?P v[0-9]*\.[0-9]*\.[0-9]*.*"],
    "Lodestar": [r".*[Ll]odestar"],
}

REGEX = {
    client: [re.compile(pattern) for pattern in patterns]
    for (client, patterns) in REGEX_PATTERNS.items()
}


def check_graffiti(graffiti: str, disabled_clients=[]) -> str:
    for (client, regexes) in REGEX.items():
        if client in disabled_clients:
            continue

        for regex in regexes:
            if regex.match(graffiti):
                return client
    return None


def classify_reward_by_graffiti(block_reward, disabled_clients=[]) -> str:
    return check_graffiti(
        block_reward["meta"]["graffiti"], disabled_clients=disabled_clients
    )


def classify_rewards_by_graffiti(rewards, disabled_clients=[]):
    result = {client: [] for client in CLIENTS if client not in disabled_clients}

    for reward in rewards:
        client = classify_reward_by_graffiti(reward, disabled_clients=disabled_clients)

        if client is not None:
            result[client].append(reward)

    return result


def process_file(
    raw_data_dir: str, proc_data_dir: str, disabled_clients: list[str], file_name: str
) -> None:
    with open(os.path.join(raw_data_dir, file_name), "r") as f:
        rewards = json.load(f)

    res = classify_rewards_by_graffiti(rewards, disabled_clients=disabled_clients)

    for (client, examples) in res.items():
        for block_rewards in examples:
            store_block_rewards(block_rewards, client, proc_data_dir)

    print(f"Finished processing {file_name}")
    sys.stdout.flush()


def parse_args():
    parser = argparse.ArgumentParser("create training data for the KNN classifier")

    parser.add_argument(
        "raw_data_dir", help="input containing data to classify using graffiti"
    )
    parser.add_argument(
        "proc_data_dir", help="output for processed data, suitable for KNN training"
    )
    parser.add_argument(
        "--disable",
        default=[],
        nargs="+",
        help="clients to ignore when forming training data",
    )
    parser.add_argument(
        "--num-workers",
        default=multiprocessing.cpu_count(),
        type=int,
        help="number of parallel processes to utilize",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    raw_data_dir = args.raw_data_dir
    proc_data_dir = args.proc_data_dir
    parallel_workers = args.num_workers
    disabled_clients = args.disable

    input_files = os.listdir(raw_data_dir)

    with concurrent.futures.ProcessPoolExecutor(
        max_workers=parallel_workers
    ) as executor:
        partial = functools.partial(
            process_file, raw_data_dir, proc_data_dir, disabled_clients
        )
        executor.map(partial, input_files)


if __name__ == "__main__":
    main()
