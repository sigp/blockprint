# Blockprint Private API

Blockprint's private API includes sensitive information on individual
validators and is only available upon request. Please contact Michael Sproul on
one of the following platforms to request access:

* Twitter: `sproulM_`
* Discord: `sproul#3907`
* Email: `<firstname>` at `sigmaprime.io`

## Authentication

Authentication is Basic Auth over HTTPS. You will be supplied with a static username and password.

## `/validator/{validator_index}/blocks/{since_slot}`

Fetch the blocks proposed by a single `validator_index`.

The `since_slot` is optional, and causes only blocks with `slot >= since_slot` to be returned.

### Example

```
curl -u user:pass "https://api.blockprint.sigp.io/validator/1024/blocks/2500000"
```

```json
[
  {
    "slot": 2547607,
    "best_guess_single": "Prysm",
    "best_guess_multi": "Prysm",
    "probability_map": {
      "Lighthouse": 0,
      "Lodestar": 0,
      "Nimbus": 0,
      "Prysm": 0,
      "Teku": 0
    }
  },
  {
    "slot": 2592198,
    "best_guess_single": "Lighthouse",
    "best_guess_multi": "Lighthouse or Prysm",
    "probability_map": {
      "Lighthouse": 0.5,
      "Lodestar": 0,
      "Nimbus": 0,
      "Prysm": 0.5,
      "Teku": 0
    }
  }
]
```

_Client identification has been edited above to preserve the privacy of validator 1024_.

## `/validator/blocks/{since_slot}`

This is a bulk version of the `/validator/{validator_index}/blocks` API that accepts multiple
validator indices in a POST request.

The `since_slot` is optional.

The response format is the same as the single-validator API but in a JSON map
keyed by validator index.

## Example

```bash
curl -u user:pass -X POST --data "[1023, 1024]" "https://api.blockprint.sigp.io/validator/blocks/2700000"
```

```json
{
  "1023": [
    {
      "slot": 2793129,
      "best_guess_single": "[REDACTED]",
      "best_guess_multi": "[REDACTED]",
      "probability_map": {
        "Lighthouse": 0,
        "Lodestar": 0,
        "Nimbus": 0,
        "Prysm": 0,
        "Teku": 0
      }
    },
    {
      "slot": 2882842,
      "best_guess_single": "[REDACTED]",
      "best_guess_multi": "[REDACTED]",
      "probability_map": {
        "Lighthouse": 0,
        "Lodestar": 0,
        "Nimbus": 0,
        "Prysm": 0,
        "Teku": 0
      }
    }
  ],
  "1024": []
}
```

## `/validator/blocks/latest`

Fetch the slot of the most recent block proposed by each validator along with the corresponding `best_guess_single`.
This is useful when you need an overview of the whole validator set at the current moment and are not interested in previous blocks.

## Example

```bash
curl -u user:pass "https://api.blockprint.sigp.io/validator/blocks/latest"
```

```json
[
  {
    "proposer_index": 0,
    "slot": 4430606,
    "best_guess_single": "[REDACTED]"
  },
  {
    "proposer_index": 1,
    "slot": 4457868,
    "best_guess_single": "[REDACTED]"
  },
  {
    "proposer_index": 2,
    "slot": 4222303,
    "best_guess_single": "[REDACTED]"
  },
  ...
]
```

## `/blocks/{start_slot}/{end_slot}`

Fetch detailed information on all blocks in a given range, including proposer
index and estimated client. This is useful if you prefer a time-centric view
to a validator-centric one.

The `end_slot` is _exclusive_ and will default to infinity if omitted.

### Example

```bash
curl -u user:pass "https://api.blockprint.sigp.io/blocks/1/2"
```

```json
[
  {
    "slot": 1,
    "proposer_index": 19026,
    "best_guess_single": "[REDACTED]",
    "best_guess_multi": "[REDACTED]",
    "probability_map": {
      "Lighthouse": 0,
      "Lodestar": 0,
      "Nimbus": 0,
      "Prysm": 0,
      "Teku": 0
    }
  }
]
```

The response is the same as the `GET /validator/{index}/blocks` endpoint, with the addition of
a `"proposer_index"` field.
