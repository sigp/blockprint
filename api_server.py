import json
import falcon

from multi_classifier import MultiClassifier
from build_db import open_block_db, get_blocks_per_client, get_sync_status, get_sync_gaps, \
                     update_block_db, get_validator_blocks

DATA_DIR = "./data/mainnet/training"
BLOCK_DB = "./block_db.sqlite"
BN_URL = "http://localhost:5052"
SELF_URL = "http://localhost:8000"

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

        results = []

        # Check required fields
        for block_reward in block_rewards:
            if ("block_root" not in block_reward or
                "attestation_rewards" not in block_reward or
                "per_attestation_rewards" not in block_reward["attestation_rewards"]):
               resp.text = json.dumps({"error": "input JSON is not a block reward"})
               resp.code = falcon.HTTP_400
               return

        update_block_db(self.block_db, self.classifier, block_rewards)
        print(f"Processed {len(block_rewards)} block{'' if block_rewards == [] else 's'}")
        resp.text = "OK"

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
        validator_blocks = get_validator_blocks(self.block_db, validator_index, since_slot)
        resp.text = json.dumps(validator_blocks, ensure_ascii=False)

app = application = falcon.App()

print("Initialising classifier, this could take a moment...")
classifier = MultiClassifier(DATA_DIR)
print("Done")

block_db = open_block_db(BLOCK_DB)

app.add_route("/classify", Classify(classifier, block_db))
app.add_route("/blocks_per_client/{start_epoch:int}/{end_epoch:int}", BlocksPerClient(block_db))
app.add_route("/blocks_per_client/{start_epoch:int}", BlocksPerClient(block_db))
app.add_route("/validator/{validator_index:int}/blocks", ValidatorBlocks(block_db))
app.add_route("/validator/{validator_index:int}/blocks/{since_slot:int}", ValidatorBlocks(block_db))
app.add_route("/sync/status", SyncStatus(block_db))
app.add_route("/sync/gaps", SyncGaps(block_db))

print("Up")
