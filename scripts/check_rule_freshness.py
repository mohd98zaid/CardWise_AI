import json
from datetime import date
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    for path in sorted((root / "rule-data" / "fixtures").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        effective_to = data.get("effective_to")
        status = (
            "open-ended"
            if not effective_to
            else (
                "expired"
                if date.fromisoformat(effective_to) < date.today()
                else "active"
            )
        )
        print(
            f"{path.name}: {status}; verification={data.get('verification_status', 'unknown')}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
