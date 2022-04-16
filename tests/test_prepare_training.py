from typing import List
from prepare_training_data import check_graffiti


def check_list(ls: List[str], value: str) -> bool:
    for item in ls:
        assert check_graffiti(item) == value


def test_graffiti_regex() -> None:
    """Testing various known graffitis"""
    # Prysm
    prysm = [
        "prylabs-validator-3",
        "RP-P v1.2.1",
        "RP-P v1.2.1 (Alea iacta est.)",
        "generic prysm graffiti",
        "Prysm/v",
        "prysm",
        "SharedStake.org Prysm GCP-SG",
    ]
    check_list(prysm, "Prysm")

    lighthouse = [
        "Lighthouse/v2.1.2-0177b92",
        "RP-L v1.2.3 (Alea iacta est.)",
        "let there be lighthouse",
        "lighthouse",
        "Lighthouse",
    ]
    check_list(lighthouse, "Lighthouse")

    teku = [
        "Teku validator pew pew pwx",
        "RP-T v1.2.1",
        "teku/v21.12.1",
        "future of finance, nbd [teku]",
        "Teku tasd1der ribeye",  # Yep
    ]
    check_list(teku, "Teku")

    nimbus = [
        "Nimbus",
        "RP-N v1.3.0 (meek was here)",
        "nimbus",
        "Nimbus/v1.5.5-67ab47-stateofus",
    ]
    check_list(nimbus, "Nimbus")
