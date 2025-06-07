"""Add service providers tables

Revision ID: 60a90b9f72e2
Revises: 86357a3cd56e
Create Date: 2025-06-04 12:07:32.069512

"""
from enum import Enum
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '60a90b9f72e2'
down_revision: Union[str, None] = '86357a3cd56e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    service_provider_category = sa.Enum('ACCOMMODATION', 'TRANSPORT', name='serviceprovidercategoryenum')
    
    op.create_table(
        'service_providers',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('category', service_provider_category, nullable=False),
        sa.Column('address', sa.String(), nullable=False),
        sa.Column('contact_no', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False, unique=True),
    )   

    op.create_table(
        'service_provider_documents',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('service_provider_id', sa.Integer(), sa.ForeignKey('service_providers.id'), nullable=False)
    )

    op.create_table(
        'service_providers_pending_verifications',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('service_provider_id', sa.Integer(), sa.ForeignKey('service_providers.id'), nullable=False)
    )


def downgrade() -> None:
    op.drop_table('service_providers_pending_verifications')
    op.drop_table('service_provider_documents')
    op.drop_table('service_providers')
    op.execute('DROP TYPE serviceprovidercategoryenum')