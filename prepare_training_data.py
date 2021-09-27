#!/usr/bin/env python3

import re
import sys
import json
from load_blocks import load_or_download_blocks

CLIENTS = ["Lighthouse", "Teku", "Nimbus", "Prysm"]

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
    input_file = sys.argv[1]
    with open(input_file, "r") as f:
        rewards = json.load(f)

    blocks = load_or_download_blocks(rewards)

    res = classify_rewards_and_blocks_by_graffiti(rewards, blocks)

    for (client, rewards) in res.items():
        print(f"{client}: {len(rewards)}")

if __name__ == "__main__":
    main()
