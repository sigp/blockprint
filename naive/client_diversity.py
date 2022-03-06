#!/usr/bin/env python3

import sys
import json
from naive_classifier import classify_block, CLIENT_LABELS


def main():
    input_file = sys.argv[1]
    with open(input_file, "r") as f:
        rewards = json.load(f)

    frequency_map = {client: 0 for client in CLIENT_LABELS}
    for block in rewards:
        client = classify_block(block)
        frequency_map[client] += 1

    for client in CLIENT_LABELS:
        percentage = round(frequency_map[client] / len(rewards), 3)
        print(f"{client},{percentage}")


if __name__ == "__main__":
    main()
