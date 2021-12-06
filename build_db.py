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

def create_block_db(db_path):
    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)

    conn.execute(
        """CREATE TABLE blocks (
            id INTEGER PRIMARY KEY,
            parent_id INTEGER,
            slot INT,
            proposer_index INT,
            best_guess_single TEXT,
            best_guess_multi TEXT,
            pr_lighthouse FLOAT,
            pr_lodestar FLOAT,
            pr_nimbus FLOAT,
            pr_prysm FLOAT,
            pr_teku FLOAT,
            FOREIGN KEY(parent_id) REFERENCES blocks(id),
            UNIQUE(slot, proposer_index)
        )
        """
    )

    conn.execute("CREATE INDEX block_proposers ON blocks (proposer_index)")
    conn.execute("CREATE INDEX block_slots ON blocks (slot)")

    return conn

def open_block_db(db_path):
    if not os.path.exists(db_path):
        raise Exception(f"no database found at {db_path}")

    return sqlite3.connect(db_path)

def build_block_db(db_path, data_dir, classify_dir, update=True):
    if update:
        conn = open_block_db(db_path)
    else:
        conn = create_block_db(db_path)

    print("loading classifier")
    classifier = MultiClassifier(data_dir)
    print("classifier loaded")

    for input_file in list_all_files(classify_dir):
        print(f"classifying rewards from file {input_file}")
        with open(input_file, "r") as f:
            block_rewards = json.load(f)

        update_block_db(conn, classifier, block_rewards)

    return conn

def load_block_parent_id(conn, parent_slot) -> int:
    # TODO: could use some re-org proofing
    res = list(conn.execute("SELECT MIN(id) FROM blocks WHERE slot = ?", [parent_slot]))
    assert len(res) == 1

    parent_id = res[0][0]
    if parent_id is None:
        return None
    else:
        return int(parent_id)

def update_block_db(conn, classifier, block_rewards):
    for block_reward in block_rewards:
        label, multilabel, prob_by_client = classifier.classify(block_reward)

        proposer_index = block_reward["meta"]["proposer_index"]
        slot = int(block_reward["meta"]["slot"])
        parent_slot = int(block_reward["meta"]["parent_slot"])

        insert_block(conn, slot, parent_slot, proposer_index, label, multilabel, prob_by_client)

    conn.commit()

def insert_block(conn, slot, parent_slot, proposer_index, label, multilabel, prob_by_client):
    pr_clients = [prob_by_client.get(client) or 0.0 for client in CLIENTS]

    parent_id = load_block_parent_id(conn, parent_slot)

    conn.execute(
        """INSERT INTO blocks (parent_id, slot, proposer_index, best_guess_single,
                               best_guess_multi, pr_lighthouse, pr_lodestar, pr_nimbus,
                               pr_prysm, pr_teku)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (parent_id, slot, proposer_index, label, multilabel, *pr_clients)
    )

def get_greatest_block_slot(block_db):
    res = list(block_db.execute("SELECT MAX(slot) FROM blocks"))
    assert len(res) == 1

    slot = res[0][0]
    if slot is None:
        return 0
    else:
        return int(slot)

def get_missing_parent_blocks(block_db):
    res = list(block_db.execute("SELECT slot FROM blocks WHERE parent_id IS NULL AND slot <> 1"))
    return res

def get_sync_status(block_db):
    greatest_block_slot = get_greatest_block_slot(block_db)
    synced = len(get_missing_parent_blocks(block_db)) == 0
    return {
        "greatest_block_slot": greatest_block_slot,
        "synced": synced
    }

def get_blocks_per_client(block_db, start_slot, end_slot):
    blocks_per_client = {
        client: 0
        for client in ["Uncertain", *CLIENTS]
    }

    client_counts = block_db.execute(
        """SELECT best_guess_single, COUNT(proposer_index)
           FROM blocks
           WHERE slot >= ? AND slot < ?
           GROUP BY best_guess_single""",
        (start_slot, end_slot)
    )

    for (client, count) in client_counts:
        blocks_per_client[client] = int(count)

    return blocks_per_client

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

    conn = build_block_db(db_path, data_dir, data_to_classify, update=False)

    conn.close()

if __name__ == "__main__":
    main()
