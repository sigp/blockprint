CLIENT_LABELS = ["Lighthouse", "Prysm", "Teku", "Teku or Nimbus"]


def classify_block(block_rewards) -> str:
    per_attestation_rewards = block_rewards["attestation_rewards"][
        "per_attestation_rewards"
    ]

    redundant_attestations = sum(
        1 for reward_map in per_attestation_rewards if len(reward_map) == 0
    )

    per_attestation_totals = [
        sum(rewards.values()) for rewards in per_attestation_rewards
    ]
    pairwise_comparisons = [
        per_attestation_totals[i] >= per_attestation_totals[i + 1]
        for i in range(len(per_attestation_totals) - 1)
    ]

    all_ordered = all(pairwise_comparisons)
    num_ordered = sum(pairwise_comparisons)

    ordered_percentage = (num_ordered + 1) / len(per_attestation_totals)

    if all_ordered and redundant_attestations == 0:
        return "Lighthouse"
    elif ordered_percentage > 0.83:
        return "Prysm"
    elif ordered_percentage > 0.788:
        return "Teku"
    else:
        return "Teku or Nimbus"
