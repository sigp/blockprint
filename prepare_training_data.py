#!/usr/bin/env python3

import os
import re
import sys
import json
import multiprocessing
import concurrent.futures
import functools

from load_blocks import store_block_rewards

# In lexicographic order, as that's what SciKit uses internally
CLIENTS = ["Lighthouse", "Lodestar", "Nimbus", "Other", "Prysm", "Teku"]

REGEX_PATTERNS = {
    "Lighthouse": [r".*[Ll]ighthouse", r"RP-L v[0-9]*\.[0-9]*\.[0-9]*.*"],
    "Teku": [r".*[Tt]eku", r"RP-T v[0-9]*\.[0-9]*\.[0-9]*.*"],
    "Nimbus": [r".*[Nn]imbus", r"RP-N v[0-9]*\.[0-9]*\.[0-9]*.*"],
    "Prysm": [r".*[Pp]rysm", "prylabs", r"RP-P v[0-9]*\.[0-9]*\.[0-9]*.*"],
    "Lodestar": [],
}

REGEX = {
    client: [re.compile(pattern) for pattern in patterns]
    for (client, patterns) in REGEX_PATTERNS.items()
}


def check_graffiti(graffiti: str) -> str:
    for (client, regexes) in REGEX.items():
        for regex in regexes:
            if regex.match(graffiti):
                return client
    return None


def classify_reward_by_graffiti(block_reward) -> str:
    return check_graffiti(block_reward["meta"]["graffiti"])


def classify_rewards_by_graffiti(rewards):
    result = {client: [] for client in CLIENTS}

    for reward in rewards:
        client = classify_reward_by_graffiti(reward)

        if client is not None:
            result[client].append(reward)

    return result


def process_file(raw_data_dir: str, proc_data_dir: str, file_name: str) -> None:
    with open(os.path.join(raw_data_dir, file_name), "r") as f:
        rewards = json.load(f)

    res = classify_rewards_by_graffiti(rewards)

    for (client, examples) in res.items():
        for block_rewards in examples:
            store_block_rewards(block_rewards, client, proc_data_dir)

    print(f"Finished processing {file_name}")
    sys.stdout.flush()


def main() -> None:
    raw_data_dir = sys.argv[1]
    proc_data_dir = sys.argv[2]

    try:
        parallel_workers = sys.argv[3]
    except IndexError:
        parallel_workers = multiprocessing.cpu_count()

    input_files = os.listdir(raw_data_dir)

    with concurrent.futures.ProcessPoolExecutor(
        max_workers=parallel_workers
    ) as executor:
        partial = functools.partial(process_file, raw_data_dir, proc_data_dir)
        executor.map(partial, input_files)


if __name__ == "__main__":
    main()
