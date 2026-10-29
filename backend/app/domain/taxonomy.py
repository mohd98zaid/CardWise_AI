from app.domain.scenarios.models import TaxonomyItem

CATEGORIES = [
    TaxonomyItem(
        code="online_shopping",
        label="Online shopping",
        description="Purchases made through an online checkout.",
    ),
    TaxonomyItem(
        code="offline_retail", label="Offline retail", description="In-store retail purchases."
    ),
    TaxonomyItem(
        code="groceries", label="Groceries", description="Food and household grocery purchases."
    ),
    TaxonomyItem(
        code="dining", label="Dining", description="Restaurants, cafes, and food delivery."
    ),
    TaxonomyItem(code="fuel", label="Fuel", description="Fuel station purchases."),
    TaxonomyItem(
        code="utilities",
        label="Utilities and bills",
        description="Utility, telecom, and recurring bill payments.",
    ),
    TaxonomyItem(
        code="travel",
        label="Travel and hotels",
        description="Travel, airline, and hotel purchases.",
    ),
    TaxonomyItem(code="transport", label="Transport", description="Local transport and commuting."),
    TaxonomyItem(
        code="healthcare", label="Healthcare", description="Healthcare and pharmacy purchases."
    ),
    TaxonomyItem(
        code="education", label="Education", description="Education and learning expenses."
    ),
    TaxonomyItem(
        code="entertainment",
        label="Entertainment and subscriptions",
        description="Entertainment and subscription payments.",
    ),
    TaxonomyItem(
        code="upi",
        label="UPI",
        description="Eligible credit-card network UPI payments where applicable.",
    ),
    TaxonomyItem(
        code="other", label="Other", description="A known category not represented above."
    ),
    TaxonomyItem(
        code="unknown",
        label="Unknown or unclassified",
        description="Use when the classification is uncertain.",
    ),
]

CHANNELS = [
    TaxonomyItem(
        code="online_card",
        label="Online card transaction",
        description="Card payment through an online checkout.",
    ),
    TaxonomyItem(
        code="in_store_card",
        label="In-store card transaction",
        description="Card payment at a physical terminal.",
    ),
    TaxonomyItem(
        code="upi",
        label="UPI via credit-card network",
        description="UPI payment where the card program supports it.",
    ),
    TaxonomyItem(code="wallet", label="Wallet", description="Wallet load or wallet payment."),
    TaxonomyItem(
        code="contactless", label="Contactless", description="Contactless terminal payment."
    ),
    TaxonomyItem(
        code="emi", label="EMI", description="A transaction converted to or initiated as EMI."
    ),
    TaxonomyItem(
        code="subscription",
        label="Standing instruction or subscription",
        description="Recurring or standing-instruction payment.",
    ),
    TaxonomyItem(code="other", label="Other", description="A channel not represented above."),
    TaxonomyItem(code="unknown", label="Unknown", description="Use when the channel is uncertain."),
]
