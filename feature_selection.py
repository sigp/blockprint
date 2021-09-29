PHASE0_REWARD_BASE = 6_000_000
ALTAIR_REWARD_BASE = 30_000_000

def feat_num_attestations(block_reward):
    per_attestation_rewards = block_reward["attestation_rewards"]["per_attestation_rewards"]
    return len(per_attestation_rewards)

def feat_num_redundant(block_reward):
    per_attestation_rewards = block_reward["attestation_rewards"]["per_attestation_rewards"]

    redundant_attestations = sum(1 for reward_map in per_attestation_rewards
                                 if len(reward_map) == 0)
    return redundant_attestations

def feat_num_pairwise_ordered(block_reward):
    per_attestation_rewards = block_reward["attestation_rewards"]["per_attestation_rewards"]
    per_attestation_totals = [sum(rewards.values()) for rewards in per_attestation_rewards]
    pairwise_comparisons = [per_attestation_totals[i] >= per_attestation_totals[i + 1]
                            for i in range(len(per_attestation_totals) - 1)]
    return sum(pairwise_comparisons)

def feat_total_reward(block_reward):
    total_reward = block_reward["attestation_rewards"]["total"]
    return total_reward

def feat_reward_per_attestation(block_reward):
    total_reward = feat_total_reward(block_reward)
    num_attestations = feat_num_attestations(block_reward)

    return safe_div(total_reward, num_attestations)

def feat_total_reward_norm(block_reward, base=ALTAIR_REWARD_BASE):
    total_reward = feat_total_reward(block_reward)
    return safe_div(total_reward, base)

def feat_num_single_bit(block_reward):
    per_attestation_rewards = block_reward["attestation_rewards"]["per_attestation_rewards"]
    num_single_bit = sum(1 for reward_map in per_attestation_rewards
                         if len(reward_map) == 1)
    return num_single_bit

def safe_div(x, y):
    if y == 0.0:
        return 0.0
    else:
        return x / y
