import pickle
import json
import os
from typing import Any, Dict, List
from knn_classifier import Classifier, persist_classifier
from prepare_training_data import CLIENTS


def create_test_classifier() -> Classifier:
    """Creates a classifier using test data"""
    data_dir = "tests/data_proc"
    classifier = Classifier(data_dir, grouped_clients=[])
    return classifier


def load_test_blocks() -> List[Dict[str, Any]]:
    test_data = "tests/data/slot_1000000_to_1000256.json"
    with open(test_data, "r") as f:
        block_rewards = json.load(f)
        return block_rewards


def test_classifier_persister() -> None:
    """Test that a persisted classifier can be restored"""
    name = "test_classifier"
    try:
        classifier = create_test_classifier()
        persist_classifier(classifier, name)
        with open(f"{name}.pkl", "rb") as fid:
            clf_loaded = pickle.load(fid)
            test_blocks = load_test_blocks()
            for b in test_blocks:
                assert clf_loaded.classify(b)[0] in CLIENTS
    finally:
        os.remove(f"{name}.pkl")
