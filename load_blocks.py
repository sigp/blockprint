#!/usr/bin/env python3

import os
import sys
import json
import requests

BLOCK_STORAGE = "blocks"
BEACON_NODE = "http://localhost:5052"


def load_or_download_blocks(
    block_rewards, block_storage=BLOCK_STORAGE, beacon_node=BEACON_NODE
):
    return [
        load_or_download_block(block_reward["block_root"], block_storage, beacon_node)
        for block_reward in block_rewards
    ]


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


def store_block_rewards(block_rewards, client, proc_data_dir):
    block_root = block_rewards["block_root"]

    # Delete unused fields to save disk space
    block_rewards["attestation_rewards"]["prev_epoch_rewards"] = {}
    block_rewards["attestation_rewards"]["curr_epoch_rewards"] = {}

    client_dir = os.path.join(proc_data_dir, client)
    os.makedirs(client_dir, exist_ok=True)
    with open(os.path.join(client_dir, f"{block_root}.json"), "w") as f:
        json.dump(block_rewards, f)


def download_block_reward_batches(
    start_slot, end_slot, output_dir, beacon_node=BEACON_NODE, batch_size=2048
):
    # assert start_slot % 2048 == 1, "batch start should be 1 mod 2048 for efficiency"
    for batch_start in range(start_slot, end_slot, batch_size):
        batch_end = min(batch_start + batch_size - 1, end_slot)

        print(f"downloading batch from slot {batch_start} to {batch_end}")

        block_rewards = download_block_rewards(batch_start, batch_end, beacon_node)

        for block_reward in block_rewards:
            # Delete unused fields to save disk space
            block_reward["attestation_rewards"]["prev_epoch_rewards"] = {}
            block_reward["attestation_rewards"]["curr_epoch_rewards"] = {}

        os.makedirs(output_dir, exist_ok=True)
        filename = f"slot_{batch_start}_to_{batch_end}.json"
        with open(os.path.join(output_dir, filename), "w") as f:
            json.dump(block_rewards, f)


def download_block_rewards(start_slot, end_slot, beacon_node=BEACON_NODE):
    url = f"{beacon_node}/lighthouse/analysis/block_rewards?start_slot={start_slot}&end_slot={end_slot}"  # noqa: E501
    res = requests.get(url)
    res.raise_for_status()
    return res.json()


def main():
    start_slot = int(sys.argv[1])
    end_slot = int(sys.argv[2])
    output_dir = sys.argv[3]

    download_block_reward_batches(start_slot, end_slot, output_dir)


if __name__ == "__main__":
    main()
