"""CLI: python3 -m analysis power"""

from __future__ import annotations

import json
import sys

from analysis.power import power_table


def main(argv: list[str]) -> int:
    if not argv or argv[0] != "power":
        print("usage: python3 -m analysis power", file=sys.stderr)
        return 2
    print(json.dumps(power_table(), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))