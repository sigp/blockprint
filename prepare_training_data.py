#!/usr/bin/env python3

import os
import re
import sys
import json
from load_blocks import store_block_rewards

# In lexicographic order, as that's what SciKit uses internally
CLIENTS = ["Lighthouse", "Lodestar", "Nimbus", "Other", "Prysm", "Teku"]

REGEX_PATTERNS = {
    "Lighthouse": ["Lighthouse/v", ".*[Ll]oopring", r"RP-L v[0-9]*\.[0-9]*\.[0-9]*"],
    "Teku": [
        "teku/v",
        "bitcoinsuisse.com",
        ".*Allnodes",
        r"RP-T v[0-9]*\.[0-9]*\.[0-9]*",
    ],
    "Nimbus": ["Nimbus/v", r"RP-N v[0-9]*\.[0-9]*\.[0-9]*"],
    "Prysm": [
        "prylabs",
        ".*[Dd][Aa]pp[Nn]ode",
        "SharedStake.org Prysm",
        r"RP-P v[0-9]*\.[0-9]*\.[0-9]*"
        # Prater only
        # "graffitiwall:",
    ],
    "Lodestar": [],
}

REGEX = {
    client: [re.compile(pattern) for pattern in patterns]
    for (client, patterns) in REGEX_PATTERNS.items()
}


def classify_reward_by_graffiti(block_reward) -> str:
    graffiti = block_reward["meta"]["graffiti"]
    for (client, regexes) in REGEX.items():
        for regex in regexes:
            if regex.match(graffiti):
                return client
    return None


def classify_rewards_by_graffiti(rewards):
    result = {client: [] for client in CLIENTS}

    for reward in rewards:
        client = classify_reward_by_graffiti(reward)

        if client is not None:
            result[client].append(reward)

    return result


def main():
    raw_data_dir = sys.argv[1]
    proc_data_dir = sys.argv[2]

    for input_file in os.listdir(raw_data_dir):
        print(f"processing {input_file}")
        with open(os.path.join(raw_data_dir, input_file), "r") as f:
            rewards = json.load(f)

        res = classify_rewards_by_graffiti(rewards)

        for (client, examples) in res.items():
            for block_rewards in examples:
                store_block_rewards(block_rewards, client, proc_data_dir)


if __name__ == "__main__":
    main()
