import requests


def post_block_rewards(url, block_rewards):
    res = requests.post(f"{url}/classify", json=block_rewards)
    res.raise_for_status()


def get_sync_gaps(url):
    res = requests.get(f"{url}/sync/gaps")
    res.raise_for_status()
    return res.json()
