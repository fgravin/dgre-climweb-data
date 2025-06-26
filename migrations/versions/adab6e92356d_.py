"""empty message

Revision ID: adab6e92356d
Revises: 
Create Date: 2025-06-26 14:20:55.030383

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'adab6e92356d'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('dgre_riverine_flood',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('fid', sa.Integer(), nullable=False),
                    sa.Column('subid', sa.String(), nullable=False),
                    sa.Column('init_date', sa.DateTime(), nullable=False),
                    sa.Column('forecast_date', sa.DateTime(), nullable=False),
                    sa.Column('init_value', sa.Integer(), nullable=False),
                    sa.Column('value', sa.Integer(), nullable=False),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint( 'subid', 'init_date', 'forecast_date', name='unique_riverine_flood_date')
                    )

    op.create_table('dgre_flash_flood',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('fid', sa.Integer(), nullable=False),
                    sa.Column('subid', sa.String(), nullable=False),
                    sa.Column('init_date', sa.DateTime(), nullable=False),
                    sa.Column('forecast_date', sa.DateTime(), nullable=False),
                    sa.Column('init_value', sa.Integer(), nullable=False),
                    sa.Column('value', sa.Integer(), nullable=False),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint( 'subid', 'init_date', 'forecast_date', name='unique_flash_flood_date')
                    )

def downgrade():
    op.drop_table('dgre_riverine_flood')
    op.drop_table('dgre_flash_flood')
