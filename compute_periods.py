#!/usr/bin/env python3

import os
import csv
import sys
import json
import sqlite3
import requests
from knn_classifier import Classifier, compute_best_guess
from multi_classifier import MultiClassifier
from prepare_training_data import CLIENTS

DEFAULT_BN = "http://localhost:5052"

def get_head_slot(bn_url):
    res = requests.get(f"{bn_url}/eth/v1/beacon/headers/head")
    res.raise_for_status()

    return int(res.json()["data"]["header"]["message"]["slot"])

def is_active_validator(validator, slot):
    epoch = slot // 32

    activation_epoch = int(validator["validator"]["activation_epoch"])
    exit_epoch = int(validator["validator"]["exit_epoch"])

    return activation_epoch <= epoch < exit_epoch

def get_active_validator_count(slot, bn_url):
    res = requests.get(f"{bn_url}/eth/v1/beacon/states/{slot}/validators")
    res.raise_for_status()

    return sum(1 for validator in res.json()["data"] if is_active_validator(validator, slot))

def fetch_periods_from_bn(slots_per_period, bn_url):
    head_slot = get_head_slot(bn_url)

    periods = []

    for i, start_slot in enumerate(range(0, head_slot, slots_per_period)):
        end_slot = min(start_slot + slots_per_period, head_slot)
        num_active_validators = get_active_validator_count(end_slot, bn_url)

        periods.append({
            "id": i,
            "end_slot": end_slot,
            "num_active_validators": num_active_validators
        })

    return periods

def create_period_db(slots_per_period, db_dir):
    db_path = os.path.join(db_dir, f"aggregated_{slots_per_period}.sqlite")

    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)

    conn.execute(
        """CREATE TABLE periods (
            id INT PRIMARY KEY,
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

    return conn

def best_guess_for_period(proposals, end_slot):
    relevant_proposals = [guess for (slot, _, guess, _) in proposals if slot <= end_slot]

    if len(relevant_proposals) == 0:
        relevant_proposals = [guess for (_, _, guess, _) in proposals]

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

def compute_period_validators(period, period_db, block_db):
    period_id = period["id"]
    end_slot = period["end_slot"]
    num_validators = period["num_active_validators"]

    period_db.execute(
        "INSERT INTO periods VALUES (?, ?, ?)",
        (period_id, end_slot, num_validators)
    )

    # Build validators table
    for validator_index in range(0, num_validators + 1):
        proposals = list(block_db.execute(
            """SELECT slot, proposer_index, best_guess_single, best_guess_multi
               FROM blocks
               WHERE proposer_index = ? ORDER BY slot ASC""",
               (validator_index,)
        ))

        recent_client = best_guess_for_period(proposals, end_slot)
        most_common_client = compute_best_guess(count_frequency([guess for (_, _, guess, _) in proposals]))

        period_db.execute(
            "INSERT INTO period_validators VALUES (?, ?, ?, ?)",
            (period_id, validator_index, recent_client, most_common_client)
        )

    period_db.commit()

def build_period_db(block_db_path, period_db_dir, slots_per_period, bn_url=DEFAULT_BN):
    block_db = sqlite3.connect(block_db_path)

    period_db = create_period_db(slots_per_period, period_db_dir)

    print(f"fetching active validators every {slots_per_period} slots from BN")
    periods = fetch_periods_from_bn(slots_per_period, bn_url)

    for period in periods:
        print(f"computing validator client affinity up to slot {period['end_slot']}")
        compute_period_validators(period, period_db, block_db)

    print("done")
    return period_db

def period_db_to_csv(period_db, output_file):
    # Output rows
    fieldnames = ["period_id", "end_slot", "num_active_validators", "Unknown", *CLIENTS]

    csv_file = open(output_file, "w", newline="")
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()

    periods = period_db.execute("SELECT * FROM periods")

    for (period_id, end_slot, num_active_validators) in periods:
        row = {
            "period_id": period_id,
            "end_slot": end_slot,
            "num_active_validators": num_active_validators,
            "Unknown": 0,
        }

        for client in CLIENTS:
            row[client] = 0

        client_counts = period_db.execute(
            """SELECT recent_client, COUNT(validator_index)
               FROM period_validators
               WHERE period_id = ?
               GROUP BY recent_client""",
            (period_id,)
        )

        for (client, count) in client_counts:
            row[client] = count

        writer.writerow(row)

    csv_file.close()
