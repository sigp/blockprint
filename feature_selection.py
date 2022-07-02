import scipy
import difflib
import statistics

PHASE0_REWARD_BASE = 6_000_000
ALTAIR_REWARD_BASE = 30_000_000
TARGET_COMMITTEE_SIZE = 128


def feat_num_attestations(block_reward):
    per_attestation_rewards = block_reward["attestation_rewards"][
        "per_attestation_rewards"
    ]
    return len(per_attestation_rewards)


def feat_num_slots_from_parent(block_reward):
    slot = int(block_reward["meta"]["slot"])
    parent_slot = int(block_reward["meta"]["parent_slot"])
    assert slot > parent_slot
    return slot - parent_slot


def feat_num_redundant(block_reward):
    per_attestation_rewards = block_reward["attestation_rewards"][
        "per_attestation_rewards"
    ]

    redundant_attestations = sum(
        1 for reward_map in per_attestation_rewards if len(reward_map) == 0
    )
    return redundant_attestations


def feat_percent_redundant_boost(block_reward):
    "Add +0.2 to the redundant percentage to create some separation from the 0.0 line"
    percent_redundant = ALL_FEATURES["percent_redundant"](block_reward)
    if percent_redundant == 0.0:
        return 0.0
    else:
        return min(1.0, percent_redundant + 0.2)


def feat_num_pairwise_ordered(block_reward):
    per_attestation_rewards = block_reward["attestation_rewards"][
        "per_attestation_rewards"
    ]
    per_attestation_totals = [
        sum(rewards.values()) for rewards in per_attestation_rewards
    ]
    pairwise_comparisons = [
        per_attestation_totals[i] >= per_attestation_totals[i + 1]
        for i in range(len(per_attestation_totals) - 1)
    ]
    return sum(pairwise_comparisons) + 1


def feat_difflib_rewards(block_reward):
    "Ratcliff and Obershelp distance of the per-attestation rewards from fully sorted"
    per_attestation_rewards = block_reward["attestation_rewards"][
        "per_attestation_rewards"
    ]
    attestation_totals = [sum(rewards.values()) for rewards in per_attestation_rewards]
    sorted_attestation_totals = sorted(attestation_totals, reverse=True)
    return difflib.SequenceMatcher(
        None, attestation_totals, sorted_attestation_totals
    ).ratio()


def generic_attestation_difflib(sort_key, reverse=False):
    def feature_fn(block_reward):
        raw_attestations = block_reward["attestation_rewards"].get("attestations") or []
        per_attestation_rewards = block_reward["attestation_rewards"][
            "per_attestation_rewards"
        ]
        attestation_rewards = [
            sum(rewards.values()) for rewards in per_attestation_rewards
        ]
        attestations = [
            (int(att["slot"]), int(att["index"]), att["beacon_block_root"], reward)
            for (att, reward) in zip(raw_attestations, attestation_rewards)
        ]
        sorted_attestations = sorted(attestations, key=sort_key, reverse=reverse)
        return difflib.SequenceMatcher(None, attestations, sorted_attestations).ratio()

    return feature_fn


def feat_spearman_correlation(block_reward):
    "Spearman correlation coefficient for the per attestation rewards vs their sorted version"
    per_attestation_rewards = block_reward["attestation_rewards"][
        "per_attestation_rewards"
    ]
    attestation_totals = [sum(rewards.values()) for rewards in per_attestation_rewards]
    sorted_attestation_totals = sorted(attestation_totals, reverse=True)
    # Spearman coefficient isn't defined for uniform/constant sequences, so we just default
    # that to 1.0
    if attestation_totals == sorted_attestation_totals:
        return 1.0
    else:
        return scipy.stats.spearmanr(
            attestation_totals, sorted_attestation_totals
        ).correlation


def feat_total_reward(block_reward):
    total_reward = block_reward["attestation_rewards"]["total"]
    return total_reward


def feat_total_reward_norm(block_reward, base=ALTAIR_REWARD_BASE):
    total_reward = feat_total_reward(block_reward)
    return safe_div(total_reward, base)


def feat_num_single_bit(block_reward):
    per_attestation_rewards = block_reward["attestation_rewards"][
        "per_attestation_rewards"
    ]
    num_single_bit = sum(
        1 for reward_map in per_attestation_rewards if len(reward_map) == 1
    )
    return num_single_bit


# The density is the percentage of committee validators covered per attestation.
def feat_median_density(block_reward):
    per_attestation_rewards = block_reward["attestation_rewards"][
        "per_attestation_rewards"
    ]
    densities = [
        len(rewards) // TARGET_COMMITTEE_SIZE for rewards in per_attestation_rewards
    ]
    return safe_median(densities)


def feat_mean_density(block_reward):
    per_attestation_rewards = block_reward["attestation_rewards"][
        "per_attestation_rewards"
    ]
    densities = [
        len(rewards) // TARGET_COMMITTEE_SIZE for rewards in per_attestation_rewards
    ]
    return safe_mean(densities)


def safe_div(x, y):
    if y == 0.0:
        return 0.0
    else:
        return x / y


def safe_mean(values):
    if values == []:
        return 0.0
    else:
        return statistics.mean(values)


def safe_median(values):
    if values == []:
        return 0.0
    else:
        return statistics.median(values)


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
    "percent_redundant_boost": feat_percent_redundant_boost,
    "num_pairwise_ordered": feat_num_pairwise_ordered,
    "percent_pairwise_ordered": scale_by_num_attestations(feat_num_pairwise_ordered),
    "difflib_rewards": feat_difflib_rewards,
    "difflib_slot_index": generic_attestation_difflib(lambda x: (x[0], x[1])),
    "difflib_index_slot": generic_attestation_difflib(lambda x: (x[1], x[0])),
    "difflib_slot_index_rev": generic_attestation_difflib(
        lambda x: (x[0], x[1]), reverse=True
    ),
    "difflib_index_slot_rev": generic_attestation_difflib(
        lambda x: (x[1], x[0]), reverse=True
    ),
    "difflib_slot": generic_attestation_difflib(lambda x: x[0]),
    "difflib_slot_rev": generic_attestation_difflib(lambda x: x[0], reverse=True),
    "difflib_slot_reward": generic_attestation_difflib(lambda x: (x[0], x[3])),
    "difflib_slot_reward_rev": generic_attestation_difflib(
        lambda x: (x[0], x[3]), reverse=True
    ),
    "spearman_correlation": feat_spearman_correlation,
    "reward": feat_total_reward,
    "norm_reward": feat_total_reward_norm,
    "norm_reward_per_slot": scale_by_num_slots(feat_total_reward_norm),
    "reward_per_attestation": scale_by_num_attestations(feat_total_reward),
    "median_density": feat_median_density,
    "mean_density": feat_mean_density,
    "num_single_bit": feat_num_single_bit,
    "percent_single_bit": scale_by_num_attestations(feat_num_single_bit),
}
