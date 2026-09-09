"""One-time NLP setup: spaCy model + light NLTK resources."""

from __future__ import annotations

import subprocess
import sys


def main() -> None:
    subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
    try:
        import nltk

        for pkg in ("punkt", "wordnet", "omw-1.4"):
            nltk.download(pkg, quiet=True)
    except Exception as exc:  # noqa: BLE001
        print(f"NLTK optional download skipped: {exc}")
    print("NLP setup complete.")


if __name__ == "__main__":
    main()
