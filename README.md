# `blockprint`

Blockprint is a tool for measuring client diversity on the Ethereum beacon chain.

It's the backend behind these tweets:

* 12 Jan 2022: https://twitter.com/sproulM_/status/1481109509544513539
* 21 Oct 2021: https://twitter.com/sproulM_/status/1451065804183662592
* 22 Sep 2021: https://twitter.com/sproulM_/status/1440512518242197516

## Public API

As of Feb 11 2022 Blockprint is hosted on a server managed by Sigma Prime.

For API documentation please see [`docs/api.md`](./docs/api.md).

## Running `blockprint`

### Lighthouse

Blockprint needs to run alongside a Lighthouse node v2.1.2 or newer.

It uses the [`/lighthouse/analysis/block_rewards`][block_rewards_endpoint] endpoint.

[block_rewards_endpoint]: https://lighthouse-book.sigmaprime.io/api-lighthouse.html

### VirtualEnv

All Python commands should be run from a virtualenv with the dependencies from `requirements.txt`
installed.

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### k-NN Classifier

Blockprint's classifier is a k-nearest neighbours classifier in `knn_classifier.py`.

See `./knn_classifier.py --help` for command line options including cross
validation (CV) and manual classification.

### Training the Classifier

The classifier is trained from a directory of reward batches. You can fetch batches with the
`load_blocks.py` script by providing a start slot, end slot and output directory:

```
./load_blocks.py 2048001 2048032 testdata
```

The directory `testdata` now contains 1 or more files of the form `slot_X_to_Y.json` downloaded
from Lighthouse.

To train the classifier on this data, use the `prepare_training_data.py` script:

```
./prepare_training_data.py testdata testdata_proc
```

This will read files from `testdata` and write the graffiti-classified training data to
`testdata_proc`, which is structured as directories of _single_ block reward files for each
client.

```
$ tree testdata_proc
testdata_proc
├── Lighthouse
│   ├── 0x03ae60212c73bc2d09dd3a7269f042782ab0c7a64e8202c316cbcaf62f42b942.json
│   └── 0x5e0872a64ea6165e87bc7e698795cb3928484e01ffdb49ebaa5b95e20bdb392c.json
├── Nimbus
│   └── 0x0a90585b2a2572305db37ef332cb3cbb768eba08ad1396f82b795876359fc8fb.json
├── Prysm
│   └── 0x0a16c9a66800bd65d997db19669439281764d541ca89c15a4a10fc1782d94b1c.json
└── Teku
    ├── 0x09d60a130334aa3b9b669bf588396a007e9192de002ce66f55e5a28309b9d0d3.json
    ├── 0x421a91ebdb650671e552ce3491928d8f78e04c7c9cb75e885df90e1593ca54d6.json
    └── 0x7fedb0da9699c93ce66966555c6719e1159ae7b3220c7053a08c8f50e2f3f56f.json
```

You can then use this directory as the datadir argument to `./knn_classifier.py`:

```
./knn_classifier.py testdata_proc --classify testdata
```

If you then want to use the classifier to build an sqlite database:

```
./build_db.py --db-path block_db.sqlite --classify-dir testdata --data-dir testdata_proc
```


### Running the API server

```
gunicorn api_server:app --timeout 1800
```

It will take a few minutes to start-up while it loads all of the training data into memory.
