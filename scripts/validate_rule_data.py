import json
import sys
from pathlib import Path

from app.domain.rules.models import CashbackRule, PointsRule
from pydantic import ValidationError


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    fixtures = sorted((root / "rule-data" / "fixtures").glob("*.json"))
    failures = 0
    for path in fixtures:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            model = PointsRule if data.get("rule_type") == "points_rate" else CashbackRule
            model.model_validate(data)
            print(f"valid: {path.relative_to(root)}")
        except (OSError, json.JSONDecodeError, ValidationError) as error:
            failures += 1
            print(f"invalid: {path.relative_to(root)}: {error}", file=sys.stderr)
    return failures


if __name__ == "__main__":
    raise SystemExit(main())
