import json
from pathlib import Path

from app.domain.catalogue import CardVariant
from app.domain.rules.models import CashbackRule

SYNTHETIC_VARIANT_ID = "synthetic-variant"


class SyntheticCatalogue:
    """Small file-backed catalogue used for the alpha/demo release only."""

    def __init__(self) -> None:
        fixture_path = (
            Path(__file__).resolve().parents[3]
            / "rule-data"
            / "fixtures"
            / "synthetic-cashback-rule.json"
        )
        with fixture_path.open(encoding="utf-8") as fixture_file:
            self._rule = CashbackRule.model_validate(json.load(fixture_file))
        self._variant = CardVariant(
            id=SYNTHETIC_VARIANT_ID,
            issuer_name="Synthetic Issuer",
            product_family="Synthetic Rewards Card",
            display_name="Synthetic Rewards Card — Online Cashback",
            network="Synthetic Network",
            market="IN",
            currency="INR",
            valid_from=self._rule.effective_from,
            status="active",
            verification_status="synthetic",
            description="A fictional card used to exercise the CardWise calculation flow.",
        )

    def list_variants(self) -> list[CardVariant]:
        return [self._variant]

    def get_variant(self, variant_id: str) -> CardVariant | None:
        return self._variant if variant_id == self._variant.id else None

    def get_cashback_rule(self, variant_id: str) -> CashbackRule | None:
        return self._rule if variant_id == self._rule.card_variant_id else None


catalogue = SyntheticCatalogue()
