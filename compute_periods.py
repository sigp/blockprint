#!/usr/bin/env python3

import os
import csv
import sqlite3
import requests
import statistics
from knn_classifier import compute_best_guess
from prepare_training_data import CLIENTS
from build_db import block_row_to_obj

DEFAULT_BN = "http://localhost:5052"

# The 95%-confidence median estimate seems to offer precision while still allowing for uncertainty
DEFAULT_GUESS = "guess_med_95"


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

    return sum(
        1 for validator in res.json()["data"] if is_active_validator(validator, slot)
    )


def fetch_periods_from_bn(slots_per_period, bn_url):
    head_slot = get_head_slot(bn_url)

    periods = []

    for i, start_slot in enumerate(range(0, head_slot, slots_per_period)):
        end_slot = min(start_slot + slots_per_period, head_slot)
        num_active_validators = get_active_validator_count(end_slot, bn_url)

        periods.append(
            {
                "id": i,
                "end_slot": end_slot,
                "num_active_validators": num_active_validators,
            }
        )

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
            guess_k_recent TEXT,
            guess_mode TEXT,
            guess_med_95 TEXT,
            FOREIGN KEY(period_id) REFERENCES periods(id)
        )
        """
    )

    return conn


# Guess the client from the most recent 3 proposals.
#
# Prefer proposals from within the period but take into account later proposals if no others
# available.
def guess_from_k_recent(proposals, end_slot, k=3):
    relevant_proposals = [block for block in proposals if block["slot"] <= end_slot]

    if len(relevant_proposals) == 0:
        relevant_proposals = proposals

    num_recent = max(k, len(relevant_proposals))
    recent_relevant = relevant_proposals[-1 * num_recent :]

    return compute_best_guess(
        count_frequency([block["best_guess_single"] for block in recent_relevant])
    )


# Guess the client from the single most recent proposal.
#
# Return "Unkown" if no proposal has slot less than `end_slot`, and "Uncertain" if the classifier
# is not confident about the most recent proposal.
def guess_from_latest(proposals, end_slot, check_prob=True):
    relevant_proposals = [block for block in proposals if block["slot"] <= end_slot]

    if len(relevant_proposals) == 0:
        return "Unknown"

    latest = relevant_proposals[-1]
    guess = latest["best_guess_single"]

    if not check_prob or latest["probability_map"][guess] > 0.95:
        return guess
    else:
        return "Uncertain"


# Guess the client from the most common classification, ignoring the period end slot.
def guess_from_mode(proposals, end_slot):
    return compute_best_guess(
        count_frequency([block["best_guess_single"] for block in proposals])
    )


def guess_from_weighted_average(proposals, end_slot, confidence_threshold=0.95):
    if len(proposals) == 0:
        return "Unknown"

    averages = {
        client: sum(proposal["probability_map"][client] for proposal in proposals)
        / len(proposals)
        for client in CLIENTS
    }
    best_guess = compute_best_guess(averages)
    if averages[best_guess] > confidence_threshold:
        return best_guess
    else:
        return "Uncertain"


def guess_from_median(proposals, end_slot, confidence_threshold=0.95):
    if len(proposals) == 0:
        return "Unknown"

    medians = {
        client: statistics.median(
            proposal["probability_map"][client] for proposal in proposals
        )
        for client in CLIENTS
    }
    best_guess = compute_best_guess(medians)
    if medians[best_guess] > confidence_threshold:
        return best_guess
    else:
        return "Uncertain"


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
        "INSERT INTO periods VALUES (?, ?, ?)", (period_id, end_slot, num_validators)
    )

    # Build validators table
    for validator_index in range(0, num_validators + 1):
        proposals = list(
            map(
                block_row_to_obj,
                block_db.execute(
                    """SELECT *
               FROM blocks
               WHERE proposer_index = ? ORDER BY slot ASC""",
                    (validator_index,),
                ),
            )
        )

        guess_k_recent = guess_from_k_recent(proposals, end_slot)
        guess_mode = guess_from_mode(proposals, end_slot)
        guess_med_95 = guess_from_median(proposals, end_slot, confidence_threshold=0.95)

        period_db.execute(
            "INSERT INTO period_validators VALUES (?, ?, ?, ?, ?)",
            (period_id, validator_index, guess_k_recent, guess_mode, guess_med_95),
        )

    period_db.commit()


def open_period_db(period_db_path):
    return sqlite3.connect(period_db_path)


def build_period_db(
    block_db_path, period_db_dir, slots_per_period, periods=None, bn_url=DEFAULT_BN
):
    block_db = sqlite3.connect(block_db_path)

    period_db = create_period_db(slots_per_period, period_db_dir)

    if periods is None:
        print(f"fetching active validators every {slots_per_period} slots from BN")
        periods = fetch_periods_from_bn(slots_per_period, bn_url)

    for period in periods:
        print(f"computing validator client affinity up to slot {period['end_slot']}")
        compute_period_validators(period, period_db, block_db)

    print("done")
    return period_db


def slot_to_period_id(period_db, slot):
    res = list(
        period_db.execute(
            "SELECT id, MIN(end_slot) FROM periods WHERE end_slot > ?", (slot,)
        )
    )
    assert len(res) == 1
    period_id = res[0][0]
    if period_id is None:
        raise Exception(f"no period known for slot {slot}")
    return int(period_id)


def row_to_obj(row):
    assert len(row) == 5

    return {
        "period_id": row[0],
        "validator_index": row[1],
        "guess_k_recent": row[2],
        "guess_mode": row[3],
        "guess_med_95": row[4],
    }


def most_recent_period_id(period_db):
    res = list(period_db.execute("SELECT id, MAX(end_slot) FROM periods"))
    assert len(res) == 1

    period_id = res[0][0]
    if period_id is None:
        raise Exception("no max period, DB is probably empty")
    return int(period_id)


def get_data_for_validators(period_db, validator_indices=None, slot=None):
    if slot is None:
        period_id = most_recent_period_id(period_db)
    else:
        period_id = slot_to_period_id(period_db, slot)

    if validator_indices is None:
        rows = period_db.execute(
            "SELECT * FROM period_validators WHERE period_id = ?", [period_id]
        )
    else:
        assert 0 < len(validator_indices) <= 999
        rows = period_db.execute(
            f"""SELECT * FROM period_validators WHERE period_id = ?
                AND validator_index IN ({','.join(['?'] * len(validator_indices))})""",
            [period_id, *validator_indices],
        )

    return [row_to_obj(row) for row in rows]


def get_client_for_validators(
    period_db, validator_indices, slot=None, guess_column=DEFAULT_GUESS
):
    return {
        x["validator_index"]: x[guess_column]
        for x in get_data_for_validators(period_db, validator_indices, slot)
    }


def get_validators_per_client(period_db, period_id, guess_column=DEFAULT_GUESS):
    validators_per_client = {client: 0 for client in ["Unknown", "Uncertain", *CLIENTS]}

    # NOTE: SQL injection. Don't read `guess_column` from the web lol
    client_counts = period_db.execute(
        f"""SELECT {guess_column}, COUNT(validator_index)
            FROM period_validators
            WHERE period_id = ?
            GROUP BY {guess_column}""",
        (period_id,),
    )

    for client, count in client_counts:
        validators_per_client[client] = int(count)

    return validators_per_client


def period_db_to_csv(period_db, output_file, guess_column=DEFAULT_GUESS):
    # Output rows
    fieldnames = [
        "period_id",
        "end_slot",
        "num_active_validators",
        "Unknown",
        "Uncertain",
        *CLIENTS,
    ]

    csv_file = open(output_file, "w", newline="")
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()

    periods = period_db.execute("SELECT * FROM periods")

    for period_id, end_slot, num_active_validators in periods:
        row = {
            "period_id": period_id,
            "end_slot": end_slot,
            "num_active_validators": num_active_validators,
        }

        validators_per_client = get_validators_per_client(
            period_db, period_id, guess_column
        )

        row.update(validators_per_client)

        writer.writerow(row)

    csv_file.close()
