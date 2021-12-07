import statistics

PHASE0_REWARD_BASE = 6_000_000
ALTAIR_REWARD_BASE = 30_000_000
TARGET_COMMITTEE_SIZE = 128

def feat_num_attestations(block_reward):
    per_attestation_rewards = block_reward["attestation_rewards"]["per_attestation_rewards"]
    return len(per_attestation_rewards)

def feat_num_slots_from_parent(block_reward):
    slot = int(block_reward["meta"]["slot"])
    parent_slot = int(block_reward["meta"]["parent_slot"])
    assert slot > parent_slot
    return slot - parent_slot

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
    return sum(pairwise_comparisons) + 1

def feat_total_reward(block_reward):
    total_reward = block_reward["attestation_rewards"]["total"]
    return total_reward

def feat_total_reward_norm(block_reward, base=ALTAIR_REWARD_BASE):
    total_reward = feat_total_reward(block_reward)
    return safe_div(total_reward, base)

def feat_num_single_bit(block_reward):
    per_attestation_rewards = block_reward["attestation_rewards"]["per_attestation_rewards"]
    num_single_bit = sum(1 for reward_map in per_attestation_rewards
                         if len(reward_map) == 1)
    return num_single_bit

# The density is the percentage of committee validators covered per attestation.
def feat_median_density(block_reward):
    per_attestation_rewards = block_reward["attestation_rewards"]["per_attestation_rewards"]
    densities = [len(rewards) // TARGET_COMMITTEE_SIZE for rewards in per_attestation_rewards]
    return statistics.median(densities)

def safe_div(x, y):
    if y == 0.0:
        return 0.0
    else:
        return x / y

def scale_by_num_attestations(feature_fn):
    def f(block_reward):
        num_attestations = feat_num_attestations(block_reward)
        feat = feature_fn(block_reward)
        return safe_div(feat, num_attestations)
    return f

def scale_by_num_slots(feature_fn):
    def f(block_reward):
        num_slots = feat_num_slots_from_parent(block_reward)
        feat = feature_fn(block_reward)
        return safe_div(feat, num_slots)
    return f

ALL_FEATURES = {
    "num_attestations": feat_num_attestations,
    "num_redundant": feat_num_redundant,
    "percent_redundant": scale_by_num_attestations(feat_num_redundant),
    "num_pairwise_ordered": feat_num_pairwise_ordered,
    "percent_pairwise_ordered": scale_by_num_attestations(feat_num_pairwise_ordered),
    "reward": feat_total_reward,
    "norm_reward": feat_total_reward_norm,
    "norm_reward_per_slot": scale_by_num_slots(feat_total_reward_norm),
    "reward_per_attestation": scale_by_num_attestations(feat_total_reward),
    "median_density": feat_median_density,
    "num_single_bit": feat_num_single_bit,
    "percent_single_bit": scale_by_num_attestations(feat_num_single_bit)
}
