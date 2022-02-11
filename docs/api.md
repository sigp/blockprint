# Blockprint Public API

The blockprint API is publicly accessible at `https://api.blockprint.sigp.io`.

## `/blocks_per_client/{start_epoch}/{end_epoch}`

Return the number of blocks proposed by each client in the requested epochs.
The `end_epoch` may be omitted to fetch data for a single epoch.

### Examples

Get block proposers for a single epoch.

```bash
curl "https://api.blockprint.sigp.io/blocks_per_client/96000
```

```json
{
  "Uncertain": 0,
  "Lighthouse": 5,
  "Lodestar": 0,
  "Nimbus": 0,
  "Other": 0,
  "Prysm": 23,
  "Teku": 4
}
```

Get block proposers for several epochs.

```bash
curl "https://api.blockprint.sigp.io/blocks_per_client/96000/97000"
```

```json
{
  "Uncertain": 0,
  "Lighthouse": 7415,
  "Lodestar": 0,
  "Nimbus": 86,
  "Other": 0,
  "Prysm": 20665,
  "Teku": 3465
}
```

## `/sync/status`

Return the status of Blockprint's database. This conveys how up-to-date Blockprint's view of the
chain is.

```bash
curl "https://api.blockprint.sigp.io/sync/status"
```

```json
{
  "greatest_block_slot": 3112960,
  "synced": true
}
```

Results can't be relied on for slots greater than `greatest_block_slot`, or if `synced` is `false`.

`synced: false` indicates the presence of _gaps_ in Blockprint's DB.
