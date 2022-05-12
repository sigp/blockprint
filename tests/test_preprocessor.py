import os
import concurrent.futures
import time
import functools

from prepare_training_data import process_file


def test_preprocessor() -> None:
    """Tests training set extraction from block reward files"""
    raw_data_dir = "tests/data"
    input_files = os.listdir(raw_data_dir)
    proc_data_dir = f"/tmp/run-{str(int(time.time()))}"
    disabled_clients = ["Lodestar"]

    with concurrent.futures.ProcessPoolExecutor(max_workers=2) as executor:
        partial = functools.partial(
            process_file, raw_data_dir, proc_data_dir, disabled_clients
        )
        executor.map(partial, input_files)

    generated_files = []
    for _, _, files in os.walk(proc_data_dir):
        generated_files.extend(files)

    correct_files = []
    for _, _, files in os.walk("tests/data_proc"):
        correct_files.extend(files)

    assert set(generated_files) == set(correct_files)
