"""add rule regression test cases"""

from alembic import op

from app.db.models import RuleTestCase

revision = "0002_rule_test_cases"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    RuleTestCase.__table__.create(bind=op.get_bind(), checkfirst=True)


def downgrade() -> None:
    RuleTestCase.__table__.drop(bind=op.get_bind(), checkfirst=True)
