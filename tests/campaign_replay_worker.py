"""Subprocess helper that runs one campaign attempt and prints the outcome."""

from __future__ import annotations

import json
from pathlib import Path
import sys

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from campaign.runner import RunConfig, run_campaign  # noqa: E402


def main() -> None:
    payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    payload["cost_bps"] = tuple(payload["cost_bps"])
    result = run_campaign(RunConfig(**payload))
    sys.stdout.write(
        json.dumps({"status": result.status, "reason": result.reason})
    )
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
