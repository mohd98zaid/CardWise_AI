"""create CardWise local MVP schema"""

import sqlalchemy as sa
from alembic import op

from app.db import models
from app.db.database import Base

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

INITIAL_TABLES = [
    models.User.__table__,
    models.SessionToken.__table__,
    models.Issuer.__table__,
    models.CardVariant.__table__,
    models.Source.__table__,
    models.Rule.__table__,
    models.UserCard.__table__,
    models.Scenario.__table__,
    models.ScenarioSpend.__table__,
    models.ScenarioAllocation.__table__,
    models.CalculationRun.__table__,
    models.Reminder.__table__,
    models.ExportJob.__table__,
    models.AuditEvent.__table__,
]


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind, tables=INITIAL_TABLES)
    # Ensure point_value_per_point is deferred to migration 0004_point_valuations
    insp = sa.inspect(bind)
    cols = [c["name"] for c in insp.get_columns("scenario_spend")]
    if "point_value_per_point" in cols:
        with op.batch_alter_table("scenario_spend") as batch_op:
            batch_op.drop_column("point_value_per_point")


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind, tables=INITIAL_TABLES)
