"""Add POI flow table for real-time and forecast flow data

Revision ID: add_poi_flow
Revises: add_dust_warning
Create Date: 2025-12-12 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_poi_flow'
down_revision = 'add_dust_warning'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'dgre_poi_flow',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('station_name', sa.String(), nullable=False),
        sa.Column('measurement_date', sa.DateTime(), nullable=False),
        sa.Column('forecast_date', sa.DateTime(), nullable=False),
        sa.Column('flow', sa.Float(), nullable=True),
        sa.Column('water_level', sa.Float(), nullable=True),
        sa.Column('water_level_alert', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('station_name', 'measurement_date', 'forecast_date', name='unique_poi_flow_measurement')
    )

    # Create indexes for better query performance
    with op.batch_alter_table('dgre_poi_flow', schema=None) as batch_op:
        batch_op.create_index('idx_poi_flow_station', ['station_name'], unique=False)
        batch_op.create_index('idx_poi_flow_measurement_date', ['measurement_date'], unique=False)
        batch_op.create_index('idx_poi_flow_forecast_date', ['forecast_date'], unique=False)


def downgrade():
    with op.batch_alter_table('dgre_poi_flow', schema=None) as batch_op:
        batch_op.drop_index('idx_poi_flow_forecast_date')
        batch_op.drop_index('idx_poi_flow_measurement_date')
        batch_op.drop_index('idx_poi_flow_station')

    op.drop_table('dgre_poi_flow')
