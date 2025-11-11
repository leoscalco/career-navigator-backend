"""Initial migration: create users, profiles, experiences, courses, academic records, and generated products tables

Revision ID: fb0b11a1d141
Revises: 
Create Date: 2025-11-11 09:55:05.001661

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fb0b11a1d141'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=True),
        sa.Column('user_group', sa.Enum('experienced_continuing', 'experienced_changing', 'inexperienced_with_goal', 'inexperienced_no_goal', name='usergroup'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # Create user_profiles table
    op.create_table(
        'user_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('career_goals', sa.Text(), nullable=True),
        sa.Column('short_term_goals', sa.Text(), nullable=True),
        sa.Column('long_term_goals', sa.Text(), nullable=True),
        sa.Column('cv_content', sa.Text(), nullable=True),
        sa.Column('linkedin_profile_url', sa.String(length=500), nullable=True),
        sa.Column('linkedin_profile_data', sa.JSON(), nullable=True),
        sa.Column('life_profile', sa.Text(), nullable=True),
        sa.Column('age', sa.Integer(), nullable=True),
        sa.Column('birth_country', sa.String(length=100), nullable=True),
        sa.Column('birth_city', sa.String(length=100), nullable=True),
        sa.Column('current_location', sa.String(length=200), nullable=True),
        sa.Column('desired_job_locations', sa.JSON(), nullable=True),
        sa.Column('languages', sa.JSON(), nullable=True),
        sa.Column('culture', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_user_profiles_id'), 'user_profiles', ['id'], unique=False)

    # Create job_experiences table
    op.create_table(
        'job_experiences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('company_name', sa.String(length=200), nullable=False),
        sa.Column('position', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('is_current', sa.Boolean(), nullable=True),
        sa.Column('location', sa.String(length=200), nullable=True),
        sa.Column('achievements', sa.JSON(), nullable=True),
        sa.Column('skills_used', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_job_experiences_id'), 'job_experiences', ['id'], unique=False)

    # Create courses table
    op.create_table(
        'courses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('course_name', sa.String(length=300), nullable=False),
        sa.Column('institution', sa.String(length=200), nullable=True),
        sa.Column('provider', sa.String(length=200), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('completion_date', sa.Date(), nullable=True),
        sa.Column('certificate_url', sa.String(length=500), nullable=True),
        sa.Column('skills_learned', sa.JSON(), nullable=True),
        sa.Column('duration_hours', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_courses_id'), 'courses', ['id'], unique=False)

    # Create academic_records table
    op.create_table(
        'academic_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('institution_name', sa.String(length=200), nullable=False),
        sa.Column('degree', sa.String(length=200), nullable=True),
        sa.Column('field_of_study', sa.String(length=200), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('gpa', sa.Float(), nullable=True),
        sa.Column('honors', sa.String(length=200), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('location', sa.String(length=200), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_academic_records_id'), 'academic_records', ['id'], unique=False)

    # Create generated_products table
    op.create_table(
        'generated_products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('product_type', sa.Enum('linkedin_export', 'cv', 'suggested_courses', 'career_plan_1y', 'career_plan_3y', 'career_plan_5y', 'possible_jobs', 'possible_companies', 'relocation_help', name='producttype'), nullable=False),
        sa.Column('content', sa.JSON(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('generated_at', sa.DateTime(), nullable=False),
        sa.Column('model_used', sa.String(length=100), nullable=True),
        sa.Column('prompt_used', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_generated_products_id'), 'generated_products', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_generated_products_id'), table_name='generated_products')
    op.drop_table('generated_products')
    op.drop_index(op.f('ix_academic_records_id'), table_name='academic_records')
    op.drop_table('academic_records')
    op.drop_index(op.f('ix_courses_id'), table_name='courses')
    op.drop_table('courses')
    op.drop_index(op.f('ix_job_experiences_id'), table_name='job_experiences')
    op.drop_table('job_experiences')
    op.drop_index(op.f('ix_user_profiles_id'), table_name='user_profiles')
    op.drop_table('user_profiles')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')
    op.execute('DROP TYPE usergroup')
    op.execute('DROP TYPE producttype')
