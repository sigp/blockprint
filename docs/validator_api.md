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
      "Lighthouse": 1,
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
