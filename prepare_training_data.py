#!/usr/bin/env python3

import os
import re
import sys
import json
from load_blocks import load_or_download_blocks, store_block_rewards

# In lexicographic order, as that's what SciKit uses internally
CLIENTS = ['Lighthouse', 'Nimbus', 'Prysm', 'Teku']

REGEX_PATTERNS = {
    "Lighthouse": [
        "Lighthouse/v",
        ".*[Ll]oopring",
    ],
    "Teku": [
        "teku/v",
        "bitcoinsuisse.com",
        ".*Allnodes",
    ],
    "Nimbus": [
        "Nimbus/v",
    ],
    "Prysm": [
        "prylabs",
        ".*[Dd][Aa]pp[Nn]ode",
        "SharedStake.org Prysm",
    ]
}

REGEX = {client: [re.compile(pattern) for pattern in patterns]
         for (client, patterns) in REGEX_PATTERNS.items()}

def get_graffiti(block) -> str:
    graffiti_hex = block["data"]["message"]["body"]["graffiti"]

    try:
        graffiti = bytes.fromhex(graffiti_hex[2:]).decode("utf-8")
        return graffiti
    except UnicodeDecodeError:
        return ""

def classify_block_by_graffiti(block) -> str:
    graffiti = get_graffiti(block)

    for (client, regexes) in REGEX.items():
        for regex in regexes:
            if regex.match(graffiti):
                return client
    return None

def classify_rewards_and_blocks_by_graffiti(rewards, blocks):
    assert len(rewards) == len(blocks)

    result = {client: [] for client in CLIENTS}

    for reward, block in zip(rewards, blocks):
        client = classify_block_by_graffiti(block)

        if client != None:
            result[client].append((reward, block))

    return result

def main():
    raw_data_dir = sys.argv[1]
    proc_data_dir = sys.argv[2]

    for input_file in os.listdir(raw_data_dir):
        print(f"processing {input_file}")
        with open(os.path.join(raw_data_dir, input_file), "r") as f:
            rewards = json.load(f)

        blocks = load_or_download_blocks(rewards)

        res = classify_rewards_and_blocks_by_graffiti(rewards, blocks)

        for (client, examples) in res.items():
            for (block_rewards, _) in examples:
                store_block_rewards(block_rewards, client, proc_data_dir)

if __name__ == "__main__":
    main()
