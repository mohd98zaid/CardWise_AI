"""add persisted calculation trace steps"""

from alembic import op

from app.db.models import CalculationTraceStep

revision = "0003_calculation_trace_steps"
down_revision = "0002_rule_test_cases"
branch_labels = None
depends_on = None


def upgrade() -> None:
    CalculationTraceStep.__table__.create(bind=op.get_bind(), checkfirst=True)


def downgrade() -> None:
    CalculationTraceStep.__table__.drop(bind=op.get_bind(), checkfirst=True)
