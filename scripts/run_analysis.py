"""
Run clustering, confusion matrix, and linguistic error analysis.

Usage:
  python scripts/run_analysis.py --results results/benchmark_xxx.json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ambiguity_layer.analysis import run_full_analysis


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, default=None)
    args = parser.parse_args()
    path = run_full_analysis(args.results, args.out_dir)
    print(f"Wrote analysis → {path}")
    print(f"Also wrote → {path.with_suffix('.md').parent / 'analysis_report.md'}")


if __name__ == "__main__":
    main()
