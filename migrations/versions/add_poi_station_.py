"""Add POI station geometry table

Revision ID: add_poi_station
Revises: add_poi_flow
Create Date: 2025-12-12 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geometry

# revision identifiers, used by Alembic.
revision = 'add_poi_station'
down_revision = 'add_poi_flow'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'dgre_poi_station',
        sa.Column('station_name', sa.String(length=256), nullable=False),
        sa.Column('name_fr', sa.String(length=256), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('geom', Geometry(geometry_type='POINT', srid=4326, spatial_index=False, from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
        sa.PrimaryKeyConstraint('station_name')
    )

    # Create spatial index on geometry column
    with op.batch_alter_table('dgre_poi_station', schema=None) as batch_op:
        batch_op.create_index('idx_dgre_poi_station_geom', ['geom'], unique=False, postgresql_using='gist', postgresql_ops={})


def downgrade():
    with op.batch_alter_table('dgre_poi_station', schema=None) as batch_op:
        batch_op.drop_index('idx_dgre_poi_station_geom', postgresql_using='gist')

    op.drop_table('dgre_poi_station')
