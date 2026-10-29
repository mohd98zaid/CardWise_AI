"""store scenario point valuation assumptions"""

import sqlalchemy as sa
from alembic import op

revision = "0004_point_valuations"
down_revision = "0003_calculation_trace_steps"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = [c["name"] for c in insp.get_columns("scenario_spend")]
    if "point_value_per_point" not in cols:
        with op.batch_alter_table("scenario_spend") as batch_op:
            batch_op.add_column(
                sa.Column("point_value_per_point", sa.Numeric(18, 4), nullable=True)
            )


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = [c["name"] for c in insp.get_columns("scenario_spend")]
    if "point_value_per_point" in cols:
        with op.batch_alter_table("scenario_spend") as batch_op:
            batch_op.drop_column("point_value_per_point")
