"""
Dev-time tool: copy the synthetic CSVs named in data_manifest.py out of the
sibling portfolio repos into this repo's data/<domain>/ folder, so the project
is self-contained and CI can build the warehouse from committed data.

Run once after the source repos change:
    python scripts/vendor_data.py --portfolio-root ..

Not needed at runtime — the vendored data/ folder is what the app reads.
"""

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from data_manifest import MANIFEST  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--portfolio-root", default=str(ROOT.parent),
                    help="folder containing the sibling portfolio repos")
    args = ap.parse_args()
    src_root = Path(args.portfolio_root).resolve()

    copied = 0
    for domain, table, source, _desc in MANIFEST:
        src = src_root / source
        if not src.exists():
            print(f"  MISSING: {src}")
            continue
        dst = ROOT / "data" / domain / f"{table}.csv"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        copied += 1
        print(f"  {domain}_{table:<28} <- {source}")
    print(f"\nvendored {copied}/{len(MANIFEST)} tables into {ROOT / 'data'}")


if __name__ == "__main__":
    main()
