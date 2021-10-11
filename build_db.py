#!/usr/bin/env python3

import os
import sys
import json
import sqlite3
from knn_classifier import Classifier, compute_best_guess
from multi_classifier import MultiClassifier
from prepare_training_data import CLIENTS

def list_all_files(classify_dir):
    for root, _, files in os.walk(classify_dir):
        for filename in files:
            yield os.path.join(root, filename)

def build_block_db(db_path, data_dir, classify_dir):
    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)

    conn.execute(
        """CREATE TABLE blocks (
            slot INT,
            proposer_index INT,
            best_guess_single TEXT,
            best_guess_multi TEXT,
            pr_lighthouse FLOAT,
            pr_lodestar FLOAT,
            pr_nimbus FLOAT,
            pr_prysm FLOAT,
            pr_teku FLOAT
        )
        """
    )

    conn.execute("CREATE INDEX block_proposers ON blocks (proposer_index)")

    print("loading classifier")
    classifier = MultiClassifier(data_dir)
    print("classifier loaded")

    for input_file in list_all_files(classify_dir):
        print(f"classifying rewards from file {input_file}")
        with open(input_file, "r") as f:
            block_rewards = json.load(f)

        for block_reward in block_rewards:
            label, multilabel, prob_by_client = classifier.classify(block_reward)

            proposer_index = block_reward["meta"]["proposer_index"]
            slot = int(block_reward["meta"]["slot"])

            pr_clients = [prob_by_client.get(client) or 0.0 for client in CLIENTS]

            conn.execute(
                "INSERT INTO blocks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (slot, proposer_index, label, multilabel, *pr_clients)
            )

        conn.commit()

    return conn

def block_row_to_obj(row):
    slot = row[0]
    proposer = row[1]
    best_guess_single = row[2]
    best_guess_multi = row[3]

    probability_map = { client: row[4 + i] for i, client in enumerate(CLIENTS) }

    return {
        "slot": slot,
        "proposer_index": proposer,
        "best_guess_single": best_guess_single,
        "best_guess_multi": best_guess_multi,
        "probability_map": probability_map
    }

def main():
    db_path = sys.argv[1]
    data_dir = sys.argv[2]
    data_to_classify = sys.argv[3]

    conn = build_block_db(db_path, data_dir, data_to_classify)

    conn.close()

if __name__ == "__main__":
    main()
