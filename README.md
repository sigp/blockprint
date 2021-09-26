# `blockprint`

This is a repository for discussion and development of tools for Ethereum block
fingerprinting.

The primary aim is to measure beacon chain client diversity using on-chain
data, as described in this tweet:

https://twitter.com/sproulM_/status/1440512518242197516

![](imgs/first_estimate.jpeg)

## Getting Started

The raw data for block fingerprinting needs to be sourced from Lighthouse's `block_rewards` API.

This is a new API that is currently only available on the `block-rewards-api` branch, i.e. this
pull request: https://github.com/sigp/lighthouse/pull/2628

Lighthouse can be built from source by following the instructions [here][lighthouse_src].

[lighthouse_src]: https://lighthouse-book.sigmaprime.io/installation-source.html

## Naive Estimate

To run an estimate using the method from the original tweet:

```bash
curl "http://localhost:5052/lighthouse/block_rewards?start_slot=2151489&end_slot=2151694" > data.json
./client_diversity.py data.json
```

```
Lighthouse,0.22
Prysm,0.65
Teku,0.055
Teku or Nimbus,0.075
```

Adjust the start and end slots to a wider range for better accuracy, or to see historical
trends.

## TODO

- [ ] Improve the classification algorithm using better stats or machine learning.
      I (Michael) will try a k-NN classifier this week.
- [ ] Decide on data representations and APIs for presenting data to a frontend.
- [ ] Implement a web backend for the above API.
