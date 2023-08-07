ALTER TABLE blocks RENAME TO blocks_legacy;

CREATE TABLE blocks (
    slot INT,
    parent_slot INTEGER,
    proposer_index INT,
    best_guess_single TEXT,
    best_guess_multi TEXT,
    pr_grandine FLOAT DEFAULT 0.0,
    pr_lighthouse FLOAT,
    pr_lodestar FLOAT,
    pr_nimbus FLOAT,
    pr_prysm FLOAT,
    pr_teku FLOAT,
    graffiti_guess TEXT,
    UNIQUE(slot, proposer_index)
);

INSERT INTO
    blocks(slot, parent_slot, proposer_index, best_guess_single, best_guess_multi,
           pr_lighthouse, pr_lodestar, pr_nimbus, pr_prysm, pr_teku, graffiti_guess)
SELECT slot, parent_slot, proposer_index, best_guess_single, best_guess_multi,
       pr_lighthouse, pr_lodestar, pr_nimbus, pr_prysm, pr_teku, graffiti_guess
FROM blocks_legacy;

DROP TABLE blocks_legacy;

VACUUM;
