"""Create users table with constraints and indexes

Revision ID: 123456789abc
Revises: a9ba372271f7 
Create Date: 2025-05-02 12:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '123456789abc'
down_revision: Union[str, None] = 'a9ba372271f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('email', sa.String(), unique=True, nullable=False),
        sa.Column('username', sa.String(), unique=True, nullable=False),
        sa.Column('password', sa.String(), nullable=False),
        sa.Column('profile_picture_key', sa.String(), nullable=True, default="user_profile/default.png"),
        sa.Column('municipality_id', sa.Integer(), nullable=True),

        sa.Column('created', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=True),

        sa.ForeignKeyConstraint(['municipality_id'], ['municipalities.id'], name='fk_users_municipality_id'),
    )

    # Indexes
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

def downgrade() -> None:
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_table('users')
