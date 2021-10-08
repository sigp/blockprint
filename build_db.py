#!/usr/bin/env python3

import os
import sys
import json
import sqlite3
from knn_classifier import Classifier, compute_best_guess
from multi_classifier import MultiClassifier

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
            best_guess_multi TEXT
        )
        """
    )

    conn.execute(
        """CREATE TABLE periods (
            id INT PRIMARY KEY,
            start_slot INT,
            end_slot INT,
            num_active_validators INT
        )
        """
    )

    conn.execute(
        """CREATE TABLE period_validators (
            period_id INT,
            validator_index INT,
            recent_client TEXT,
            most_common_client TEXT,
            FOREIGN KEY(period_id) REFERENCES periods(id)
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

            conn.execute(
                "INSERT INTO blocks VALUES (?, ?, ?, ?)",
                (slot, proposer_index, label, multilabel)
            )

        conn.commit()

    return conn

def best_guess_for_period(all_proposals, end_slot):
    relevant_proposals = [guess for (slot, _, guess, _) in all_proposals if slot <= end_slot]

    if len(relevant_proposals) == 0:
        relevant_proposals = [guess for (_, _, guess, _) in all_proposals]

    num_recent = max(3, len(relevant_proposals))
    recent_relevant = relevant_proposals[-1 * num_recent:]

    return compute_best_guess(count_frequency(recent_relevant))

def count_frequency(guesses):
    client_frequency = {}

    for client in guesses:
        if client not in client_frequency:
            client_frequency[client] = 1
        else:
            client_frequency[client] += 1

    return client_frequency

def compute_period_validators(period, conn):
    period_id = period["id"]
    start_slot = period["start_slot"]
    end_slot = period["end_slot"]
    num_validators = period["num_validators"]

    conn.execute(
        "INSERT INTO periods VALUES (?, ?, ?, ?)",
        (period_id, start_slot, end_slot, num_validators)
    )

    # Build validators table
    for validator_index in range(0, num_validators + 1):
        proposals = list(conn.execute("SELECT * FROM blocks WHERE proposer_index = ? ORDER BY slot ASC", (validator_index,)))

        recent_client = best_guess_for_period(proposals, end_slot)
        most_common_client = compute_best_guess(count_frequency([guess for (_, _, guess, _) in proposals]))

        conn.execute(
            "INSERT INTO period_validators VALUES (?, ?, ?, ?)",
            (period_id, validator_index, recent_client, most_common_client)
        )

    conn.commit()

def main():
    db_path = sys.argv[1]
    data_dir = sys.argv[2]
    data_to_classify = sys.argv[3]

    conn = build_block_db(db_path, data_dir, data_to_classify)

    conn.close()
    return

    # FIXME(sproul): automate this
    periods = [
        {"id": 0, "start_slot": 1, "end_slot": 110592, "num_validators": 34711},
        {"id": 1, "start_slot": 110593, "end_slot": 221184, "num_validators": 48535}
    ]

    for period in periods:
        print(f"computing period {period} stats")
        compute_period_validators(period, conn)

    conn.close()

if __name__ == "__main__":
    main()
