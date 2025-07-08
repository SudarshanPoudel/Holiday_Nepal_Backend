"""Create user saved plans and user rating plans

Revision ID: 82ee810c101c
Revises: c15097e3c2b2
Create Date: 2025-07-08 08:56:45.434566
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '82ee810c101c'
down_revision: Union[str, None] = 'c15097e3c2b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # user_saved_plans (many-to-many)
    op.create_table(
        "user_saved_plans",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("plans.id"), primary_key=True),
    )

    op.create_table(
        "user_plan_ratings",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("plans.id"), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.CheckConstraint('rating >= 1 AND rating <= 5', name='rating_between_1_and_5'),
    )
    

def downgrade() -> None:
    op.drop_table("user_plan_ratings")
    op.drop_table("user_saved_plans")
