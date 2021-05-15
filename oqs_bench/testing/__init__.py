import os
from typing import List
from pathlib import Path

import pandas as pd

from oqs_bench.testing.config_types import KEMConfig, SignConfig
from oqs_bench.testing.test_runner import KEMTestRunner, SignTestRunner

import yaml

CURRENT_PATH = Path(__file__).parent

if __name__ == '__main__':
    def _test(config_name: str, test_runner, result_dir: str):
        config = yaml.safe_load(open(CURRENT_PATH / "configs" / f"{config_name}.yml", "r"))
        for candidate in config:
            variant_results = []
            for i, variant in enumerate(candidate["variants"]):
                print(f"Testing {candidate['algorithm']}, Variant {i + 1}/{len(candidate['variants'])} ({variant})", end='\r')
                runner = test_runner(candidate["algorithm"], variant, candidate["runner"])
                variant_results.append(runner.test())
            algorithm_data = pd.concat(variant_results)
            csv_out = CURRENT_PATH / "results" / result_dir / f'{candidate["algorithm"]}.csv'
            if not csv_out.parent.exists():
                csv_out.parent.mkdir(parents=True)
            algorithm_data.to_csv(csv_out)
            print(end='\n')

    print("Testing KEMs.")
    _test("kems", KEMTestRunner, "kem")

    print("Testing DSSs.")
    _test("signschemes", SignTestRunner, "sign")
