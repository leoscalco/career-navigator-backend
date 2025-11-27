"""Add roadmap_tasks table

Revision ID: roadmap_tasks_001
Revises: 2347e1d3fbd6
Create Date: 2025-11-25 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'roadmap_tasks_001'
down_revision: Union[str, Sequence[str], None] = '2347e1d3fbd6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create roadmap_tasks table
    op.create_table(
        'roadmap_tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=True),
        sa.Column('plan_type', sa.String(length=20), nullable=False),
        sa.Column('period', sa.String(length=50), nullable=False),
        sa.Column('task_type', sa.String(length=50), nullable=False),
        sa.Column('task_content', sa.Text(), nullable=False),
        sa.Column('task_index', sa.Integer(), nullable=False),
        sa.Column('is_completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['product_id'], ['generated_products.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_roadmap_tasks_user_id'), 'roadmap_tasks', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_roadmap_tasks_user_id'), table_name='roadmap_tasks')
    op.drop_table('roadmap_tasks')

