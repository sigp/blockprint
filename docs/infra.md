Running blockprint in production
================================

This document describes the architecture we use to run blockprint in production.

![Blockprint Architecture](../imgs/architecture.png)

The **required** components are:

- [`blockprint`][blockprint]: Machine-learning classifier and webserver. This is where the model is
  loaded, and where the sqlite block database is modified.
- [`blockprint-bg`][blockprint-bg]: Daemon that runs alongside `blockprint` and feeds it the latest
  blocks from the canonical chain. This daemon will also heal any _gaps_ in the database caused by
  periods of downtime.
- [`lighthouse`][lighthouse]: Lighthouse computes the _block reward_ data for each block, which is
  what `blockprint` uses for classification. It is also used by `blockprint-bg` to track the
  canonical chain.

If measuring `blockprint`'s accuracy is desired (recommended), then the following **optional**
services enable that:

- [`blockdreamer`][blockdreamer]: Blockdreamer triggers block production on a collection of
  consensus clients. It builds a block using each client and then posts that block to a configured
  endpoint (`blockgauge`). It can also be configured to store the responses (block rewards) for
  each block, which can later be used to train new models.
- [`blockgauge`][blockgauge]: Blockgauge keeps track of `blockprint`'s accuracy and is responsible
  for classifying blocks received from `blockdreamer`. It exposes an HTTP endpoint for
  `blockdreamer` to POST to, and sends every block received to Lighthouse to be converted into
  block reward JSON. It then POSTs each block reward JSON to `blockprint` to receive a
  classification. It stores the classification from `blockprint` (in-memory) and provides a
  `/confusion` HTTP API to display information on false positives, false negatives, etc.
- `consensus1`, `consensus2`, etc: Consensus clients that `blockdreamer` uses for block production.
   We run 2 nodes for each client: one subscribed to all subnets, and one subscribed to default
   subnets. The reason being that clients tend to produce substantially different (better) blocks
   when subscribed to all subnets.
- [`eleel`][eleel]: Electric Eel is a _multiplexer_ that allows a single execution node to be shared by
  multiple consensus clients. This makes it easier to run multiple consensus nodes. Additionally
  `eleel` has the ability to rapidly build dummy execution payloads, which the consensus clients
  include in their dummy blocks produced by `blockdreamer`.

## Running `blockprint`

Run the API server (`api_server.py`) on `localhost` using Gunicorn or similar. There's an example
service file in [`infra/blockprint.service`](../infra/blockprint.service).

## Running `blockprint-bg`

Run the background daemon (`background_tasks.py`) on the same server as the main blockprint API
and the central Lighthouse instance. There's an example service file in
[`infra/blockprint-bg.service`](../infra/blockprint-bg.service).

## Running `lighthouse`

Run Lighthouse alongside `blockprint` and `blockprint-bg`.

If classification of historic blocks is desired, you need the `--reconstruct-historic-states` flag.
Running a Lighthouse tree-states alpha can help keep the size of the CL archive down.

If you're running blockdreamer, you'll also need `--always-prepare-payload --prepare-payload-lookahead 8000`.

## Running `eleel`

You can run one Eleel instance per worker node, or one central instance serving all workers.

Follow the [Eleel docs][eleel] for setting it up. We use the central Lighthouse node that serves
block reward requests to control Eleel, although other configurations are possible.

An example configuration file is included in [`infra/eleel.service`](../infra/eleel.service).

## Running `blockgauge`

We run [blockgauge][blockgauge] on the primary server alongside `blockprint` and `lighthouse`, both
of which it connects to. Blockgauge's API is then accessed by the workers via HTTPS with basic auth,
using a Caddy reverse proxy (see below).

See [`infra/blockgauge.service`](../infra/blockgauge.service) for an example service file.

## Running `blockdreamer`

We use one blockdreamer instance per block-building worker machine. Follow the
[blockdreamer docs][blockdreamer] for information on how to set it up. An example service file
is included at [`infra/blockdreamer.service`](../infra/blockdreamer.service), and an example
configuration TOML at [`infra/blockdreamer.toml`](../infra/blockdreamer.toml).

We post to blockgauge on the primary server via HTTPS. This is authenticated with a username and
password set in the `Caddyfile` (see below).

## Running `caddy`

We use Caddy to encrypt the traffic to and from the blockprint API and blockgauge. The `Caddyfile`
for our server (minus passwords!) is in [`infra/Caddyfile`](../infra/Caddyfile).

HTTP basic auth is used to protect the private blockprint APIs and the blockgauge endpoint.

For Eleel, requests are authenticated with JWT secrets managed by Eleel itself.

## Running workers

Configuring each of the CL clients for compatibility with blockdreamer is a matter of tweaking a few
parameters:

- Ensure a unique P2P port is set (for nodes sharing the same host).
- Ensure a unique HTTP port is set.
- Use a dummy fee recipient to ensure that block building doesn't fail.
- Connect to Eleel's client endpoint (`http://localhost:8552`, or `https://server.com/eleel`).
- Use `skip_randao_verification` in the blockdreamer config for Lighthouse, Nimbus and Grandine
  workers.

## Required Lighthouse APIs

It isn't (currently) possible to substitute the central Lighthouse instance for another consensus
client. We require the following custom APIs which are Lighthouse-specific:

- [`GET /lighthouse/analysis/block_rewards`][get_block_rewards]: This endpoint produces block
  reward JSON for a range of blocks _from the canonical chain_. Used by `blockprint-bg`.
- [`POST /lighthouse/analysis/block_rewards`][post_block_rewards]: This endpoint produces block
  reward JSON for a list of blocks `POST`ed to the endpoint. Used by `blockgauge`.

[blockprint]: https://github.com/sigp/blockprint/blob/main/api_server.py
[blockprint-bg]: https://github.com/sigp/blockprint/blob/main/background_tasks.py
[lighthouse]: https://github.com/sigp/lighthouse
[blockdreamer]: https://github.com/blockprint-collective/blockdreamer
[blockgauge]: https://github.com/blockprint-collective/blockgauge
[eleel]: https://github.com/sigp/eleel

[get_block_rewards]: https://lighthouse-book.sigmaprime.io/api-lighthouse.html#lighthouseanalysisblock_rewards
[post_block_rewards]: https://github.com/sigp/lighthouse/blob/2841f60686d642fcc0785c884d43e34e47a800dc/beacon_node/http_api/src/lib.rs#L4279-L4294
