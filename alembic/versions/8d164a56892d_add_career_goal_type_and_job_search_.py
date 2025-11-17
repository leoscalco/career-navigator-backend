"""Add career_goal_type and job_search_locations to user_profiles

Revision ID: 8d164a56892d
Revises: 246291cbef07
Create Date: 2025-11-17 18:40:03.321967

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8d164a56892d'
down_revision: Union[str, Sequence[str], None] = '246291cbef07'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create enum type first
    careergoaltype_enum = sa.Enum('continue_path', 'change_career', 'change_area', 'explore_options', name='careergoaltype')
    careergoaltype_enum.create(op.get_bind(), checkfirst=True)
    
    # Add columns
    op.add_column('user_profiles', sa.Column('career_goal_type', careergoaltype_enum, nullable=True, server_default='continue_path'))
    op.add_column('user_profiles', sa.Column('job_search_locations', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('user_profiles', 'job_search_locations')
    op.drop_column('user_profiles', 'career_goal_type')
    
    # Drop enum type
    sa.Enum(name='careergoaltype').drop(op.get_bind(), checkfirst=True)
