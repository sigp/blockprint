#!/usr/bin/env python3

# Tasks that are intended to run alongside the API server to keep it up to date.
import os
import time
import json
import requests
import sseclient
import multiprocessing

from api_client import post_block_rewards, get_sync_gaps
from load_blocks import download_block_rewards

BN_URL = os.environ.get("BN_URL") or "http://localhost:5052"
BLOCKPRINT_URL = os.environ.get("BP_URL") or "http://localhost:8000"

EVENT_URL_PATH = "eth/v1/events?topics=block_reward"
HEADERS = {"Accept": "text/event-stream"}

BACKFILL_WAIT_SECONDS = 60
FAIL_WAIT_SECONDS = 5


class BlockRewardListener:
    def __init__(self, bn_url, blockprint_url):
        self.bn_url = bn_url
        self.blockprint_url = blockprint_url

    def run(self):
        while True:
            try:
                event_url = f"{self.bn_url}/{EVENT_URL_PATH}"
                res = requests.get(event_url, stream=True, headers=HEADERS)
                res.raise_for_status()

                client = sseclient.SSEClient(res)

                for event in client.events():
                    block_reward = json.loads(event.data)
                    slot = int(block_reward["meta"]["slot"])
                    print(f"Classifying block {slot}")
                    post_block_rewards(self.blockprint_url, [block_reward])

            except Exception as e:
                print(f"Block listener failed with: {e}")
                time.sleep(FAIL_WAIT_SECONDS)


def explode_gap(start_slot, end_slot, sprp):
    next_boundary = (start_slot // sprp + 1) * sprp

    if end_slot > next_boundary:
        return [(start_slot, next_boundary)] + explode_gap(
            next_boundary + 1, end_slot, sprp
        )
    else:
        return [(start_slot, end_slot)]


def explode_gaps(gaps, sprp=2048):
    "Divide sync gaps into manageable chunks aligned to Lighthouse's restore points"
    exploded = []

    for gap in gaps:
        start_slot = int(gap["start"])
        end_slot = int(gap["end"])
        exploded.extend(explode_gap(start_slot, end_slot, sprp))

    return exploded


class Backfiller:
    def __init__(self, bn_url, blockprint_url):
        self.bn_url = bn_url
        self.blockprint_url = blockprint_url

    def run(self):
        while True:
            try:
                sync_gaps = get_sync_gaps(self.blockprint_url)
                chunks = explode_gaps(sync_gaps)

                for (start_slot, end_slot) in chunks:
                    print(f"Downloading backfill blocks {start_slot}..={end_slot}")
                    block_rewards = download_block_rewards(
                        start_slot, end_slot, beacon_node=self.bn_url
                    )

                    print(f"Classifying backfill blocks {start_slot}..={end_slot}")
                    post_block_rewards(self.blockprint_url, block_rewards)

                if len(chunks) == 0:
                    print("Blockprint is synced")
                    time.sleep(BACKFILL_WAIT_SECONDS)

            except Exception as e:
                print(f"Backfiller failed with: {e}")
                time.sleep(FAIL_WAIT_SECONDS)


if __name__ == "__main__":
    listener_task = lambda: BlockRewardListener(BN_URL, BLOCKPRINT_URL).run()
    multiprocessing.Process(target=listener_task, name="block_listener").start()

    backfill_task = lambda: Backfiller(BN_URL, BLOCKPRINT_URL).run()
    multiprocessing.Process(target=backfill_task, name="backfiller").start()
