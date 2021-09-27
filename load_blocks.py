#!/usr/bin/env python3

import os
import json
import requests

BLOCK_STORAGE = "blocks"
BEACON_NODE = "http://localhost:5052"

def load_or_download_blocks(block_rewards, block_storage=BLOCK_STORAGE, beacon_node=BEACON_NODE):
    return [load_or_download_block(block_reward["block_root"], block_storage, beacon_node)
            for block_reward in block_rewards]

def load_or_download_block(block_root, block_storage, beacon_node):
    block = load_block(block_root, block_storage)

    if block is None:
        block = download_block(block_root, beacon_node)
        store_block(block, block_root, block_storage)

    return block

def block_path(block_root, block_storage):
    return f"{block_storage}/{block_root}.json"

def load_block(block_root, block_storage):
    try:
        with open(block_path(block_root, block_storage), "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def store_block(block, block_root, block_storage):
    os.makedirs(block_storage, exist_ok=True)
    with open(block_path(block_root, block_storage), "w") as f:
        json.dump(block, f)

def download_block(block_root, beacon_node):
    url = f"{beacon_node}/eth/v2/beacon/blocks/{block_root}"
    res = requests.get(url)
    res.raise_for_status()
    return res.json()

def main():
    input_file = sys.argv[1]
    with open(input_file, "r") as f:
        rewards = json.load(f)

    load_or_download_blocks(rewards)

if __name__ == "__main__":
    main()
