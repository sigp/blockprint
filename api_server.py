import json
import falcon

from multi_classifier import MultiClassifier
from build_db import open_block_db, get_blocks_per_client, get_sync_status
from compute_periods import open_period_db, get_client_for_validators, get_validators_per_client

DATA_DIR = "./data/mainnet/altair"
BLOCK_DB = "./data.sqlite"

class Classify:
    def __init__(self, classifier):
        self.classifier = classifier

    def on_post(self, req, resp):
        try:
            block_rewards = json.load(req.bounded_stream)
        except json.decoder.JSONDecodeError as e:
            resp.text = json.dumps({"error": f"invalid JSON: {e}"})
            resp.code = falcon.HTTP_400
            return

        results = []

        # Check required fields
        if ("block_root" not in block_reward or
            "attestation_rewards" not in block_reward or
            "per_attestation_rewards" not in block_reward["attestation_rewards"]):
           resp.text = json.dumps({"error": "input JSON is not a block reward"})
           resp.code = falcon.HTTP_400
           return

        best_guess_single, best_guess_multi, probability_map = self.classifier.classify(block_reward)

        should_store = req.get_param_as_bool("store", default=False)

        result = {
            "block_root": block_reward["block_root"],
            "best_guess_single": best_guess_single,
            "best_guess_multi": best_guess_multi,
            "probability_map": probability_map,
        }

        resp.text = json.dumps(result, ensure_ascii=False)

class BlocksPerClient:
    def __init__(self, block_db):
        self.block_db = block_db

    def on_get(self, req, resp, start_slot, end_slot):
        blocks_per_client = get_blocks_per_client(self.block_db, start_slot, end_slot)
        resp.text = json.dumps(blocks_per_client, ensure_ascii=False)

class SyncStatus:
    def __init__(self, block_db):
        self.block_db = block_db

    def on_get(self, req, resp):
        sync_status = get_sync_status(self.block_db)
        resp.text = json.dumps(sync_status, ensure_ascii=False)

app = application = falcon.App()

print("Initialising classifier, this could take a moment...")
classifier = MultiClassifier(DATA_DIR)
print("Done")

block_db = open_block_db(BLOCK_DB)

app.add_route("/classify", Classify(classifier))
app.add_route("/blocks_per_client/{start_slot:int}/{end_slot:int}", BlocksPerClient(block_db))
app.add_route("/sync_status", SyncStatus(block_db))

print("Up")
