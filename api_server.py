import os
import json
import falcon
import pickle

from multi_classifier import MultiClassifier
from build_db import (
    open_block_db,
    get_blocks_per_client,
    get_sync_status,
    get_sync_gaps,
    update_block_db,
    get_validator_blocks,
    get_all_validators_latest_blocks,
    get_blocks,
    count_true_positives,
    count_true_negatives,
    count_false_positives,
    count_false_negatives,
)

DATA_DIR = os.environ.get("DATA_DIR") or "./data/mainnet/training"
BLOCK_DB = os.environ.get("BLOCK_DB") or "./block_db.sqlite"
BN_URL = os.environ.get("BN_URL") or "http://localhost:5052"
SELF_URL = "http://0.0.0.0:8000"
DISABLE_CLASSIFIER = "DISABLE_CLASSIFIER" in os.environ
MODEL_PATH = os.environ.get("MODEL_PATH") or ""


class Classify:
    def __init__(self, classifier, block_db):
        self.classifier = classifier
        self.block_db = block_db

    def on_post(self, req, resp):
        try:
            block_rewards = json.load(req.bounded_stream)
        except json.decoder.JSONDecodeError as e:
            resp.text = json.dumps({"error": f"invalid JSON: {e}"})
            resp.code = falcon.HTTP_400
            return

        if not check_block_rewards_ok(block_rewards, resp):
            return

        update_block_db(self.block_db, self.classifier, block_rewards)
        print(
            f"Processed {len(block_rewards)} block{'' if block_rewards == [] else 's'}"
        )
        resp.text = "OK"


class ClassifyNoStore:
    def __init__(self, classifier):
        self.classifier = classifier

    def on_post(self, req, resp):
        try:
            block_rewards = json.load(req.bounded_stream)
        except json.decoder.JSONDecodeError as e:
            resp.text = json.dumps({"error": f"invalid JSON: {e}"})
            resp.code = falcon.HTTP_400
            return

        if not check_block_rewards_ok(block_rewards, resp):
            return

        classifications = []
        for block_reward in block_rewards:
            label, _, _, _ = classifier.classify(block_reward)
            classifications.append(
                {
                    "best_guess_single": label,
                }
            )
        resp.text = json.dumps(classifications, ensure_ascii=False)


def check_block_rewards_ok(block_rewards, resp):
    # Check required fields
    for block_reward in block_rewards:
        if (
            "block_root" not in block_reward
            or "attestation_rewards" not in block_reward
            or "per_attestation_rewards" not in block_reward["attestation_rewards"]
        ):
            resp.text = json.dumps({"error": "input JSON is not a block reward"})
            resp.code = falcon.HTTP_400
            return False
    return True


class BlocksPerClient:
    def __init__(self, block_db):
        self.block_db = block_db

    def on_get(self, req, resp, start_epoch, end_epoch=None):
        end_epoch = end_epoch or (start_epoch + 1)

        start_slot = 32 * start_epoch
        end_slot = 32 * end_epoch
        blocks_per_client = get_blocks_per_client(self.block_db, start_slot, end_slot)
        resp.text = json.dumps(blocks_per_client, ensure_ascii=False)


class SyncStatus:
    def __init__(self, block_db):
        self.block_db = block_db

    def on_get(self, req, resp):
        sync_status = get_sync_status(self.block_db)
        resp.text = json.dumps(sync_status, ensure_ascii=False)


class SyncGaps:
    def __init__(self, block_db):
        self.block_db = block_db

    def on_get(self, req, resp):
        gaps = get_sync_gaps(self.block_db)
        resp.text = json.dumps(gaps, ensure_ascii=False)


class ValidatorBlocks:
    def __init__(self, block_db):
        self.block_db = block_db

    def on_get(self, req, resp, validator_index, since_slot=None):
        validator_blocks = get_validator_blocks(
            self.block_db, validator_index, since_slot
        )
        resp.text = json.dumps(validator_blocks, ensure_ascii=False)


class MultipleValidatorsBlocks:
    def __init__(self, block_db):
        self.block_db = block_db

    def on_post(self, req, resp, since_slot=None):
        # Validate request.
        try:
            validator_indices = json.load(req.bounded_stream)
        except json.decoder.JSONDecodeError as e:
            resp.text = json.dumps({"error": f"invalid JSON: {e}"})
            resp.code = falcon.HTTP_400
            return

        # I love type checking.
        if type(validator_indices) != list or any(
            type(x) != int for x in validator_indices
        ):
            resp.text = json.dumps({"error": "request must be a list of integers"})
            resp.code = falcon.HTTP_400
            return

        all_blocks = {}
        for validator_index in validator_indices:
            validator_blocks = get_validator_blocks(
                self.block_db, validator_index, since_slot
            )
            all_blocks[validator_index] = validator_blocks

        resp.text = json.dumps(all_blocks, ensure_ascii=False)


class AllValidatorsLatestBlocks:
    def __init__(self, block_db):
        self.block_db = block_db

    def on_get(self, req, resp):
        result = get_all_validators_latest_blocks(self.block_db)
        resp.text = json.dumps(result, ensure_ascii=False)


class Blocks:
    def __init__(self, block_db):
        self.block_db = block_db

    def on_get(self, req, resp, start_slot, end_slot=None):
        blocks = get_blocks(self.block_db, start_slot, end_slot)
        resp.text = json.dumps(blocks, ensure_ascii=False)


class ConfusionMatrix:
    def __init__(self, block_db):
        self.block_db = block_db

    def on_get(self, req, resp, client, start_slot, end_slot=None):
        true_pos = count_true_positives(self.block_db, client, start_slot, end_slot)
        true_neg = count_true_negatives(self.block_db, client, start_slot, end_slot)
        false_pos = count_false_positives(self.block_db, client, start_slot, end_slot)
        false_neg = count_false_negatives(self.block_db, client, start_slot, end_slot)
        resp.text = json.dumps(
            {
                "true_pos": true_pos,
                "true_neg": true_neg,
                "false_pos": false_pos,
                "false_neg": false_neg,
            }
        )


app = application = falcon.App()

classifier = None
if not DISABLE_CLASSIFIER:
	if MODEL_PATH != "":
		if MODEL_PATH.endswith('.pkl'):
			print("Loading classifier from pickle file...")
			classifier = pickle.load(open(MODEL_PATH, "rb"))
			print("Loaded classifier into memory")
		else:
			print("model path must end with .pkl")
			exit(0)
	else:
		print("Initialising classifier, this could take a moment...")
		classifier = MultiClassifier(DATA_DIR) if not DISABLE_CLASSIFIER else None
		print("Done")

block_db = open_block_db(BLOCK_DB)

app.add_route("/classify/no_store", ClassifyNoStore(classifier))
app.add_route("/classify", Classify(classifier, block_db))
app.add_route(
    "/blocks_per_client/{start_epoch:int}/{end_epoch:int}", BlocksPerClient(block_db)
)
app.add_route("/blocks_per_client/{start_epoch:int}", BlocksPerClient(block_db))
app.add_route("/validator/{validator_index:int}/blocks", ValidatorBlocks(block_db))
app.add_route(
    "/validator/{validator_index:int}/blocks/{since_slot:int}",
    ValidatorBlocks(block_db),
)
app.add_route("/validator/blocks", MultipleValidatorsBlocks(block_db))
app.add_route("/validator/blocks/{since_slot:int}", MultipleValidatorsBlocks(block_db))
app.add_route("/validator/blocks/latest", AllValidatorsLatestBlocks(block_db))
app.add_route("/blocks/{start_slot:int}", Blocks(block_db))
app.add_route("/blocks/{start_slot:int}/{end_slot:int}", Blocks(block_db))
app.add_route("/sync/status", SyncStatus(block_db))
app.add_route("/sync/gaps", SyncGaps(block_db))
app.add_route(
    "/confusion/{client}/{start_slot:int}/{end_slot:int}", ConfusionMatrix(block_db)
)

print("Up")
