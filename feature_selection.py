
def feat_num_redundant(block_rewards):
    per_attestation_rewards = block_rewards["attestation_rewards"]["per_attestation_rewards"]

    redundant_attestations = sum(1 for reward_map in per_attestation_rewards
                                 if len(reward_map) == 0)
    return redundant_attestations

def feat_num_pairwise_ordered(block_rewards):
    per_attestation_rewards = block_rewards["attestation_rewards"]["per_attestation_rewards"]
    per_attestation_totals = [sum(rewards.values()) for rewards in per_attestation_rewards]
    pairwise_comparisons = [per_attestation_totals[i] >= per_attestation_totals[i + 1]
                            for i in range(len(per_attestation_totals) - 1)]
    return sum(pairwise_comparisons)
