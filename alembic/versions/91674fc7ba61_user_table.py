"""user_table

Revision ID: 91674fc7ba61
Revises: a9ba372271f7
Create Date: 2025-04-24 16:44:21.301507

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '91674fc7ba61'
down_revision: Union[str, None] = 'a9ba372271f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False, unique=True),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('password', sa.String(), nullable=False),
        sa.Column('is_verified', sa.Boolean(), nullable=True, default=False),
        sa.Column('district_id', sa.Integer(), nullable=True),
        sa.Column('municipality_id', sa.Integer(), nullable=True),
        sa.Column('ward_id', sa.Integer(), nullable=True),
        sa.Column('created', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ['district_id'], ['districts.id'], name='fk_users_district_id'
        ),
        sa.ForeignKeyConstraint(
            ['municipality_id'], ['municipalities.id'], name='fk_users_municipality_id'
        ),
        sa.ForeignKeyConstraint(
            ['ward_id'], ['wards.id'], name='fk_users_ward_id'
        ),
        sa.PrimaryKeyConstraint('id', name='pk_users_id')
    )


def downgrade() -> None:
    op.drop_table('users')
