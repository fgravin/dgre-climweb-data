"""empty message

Revision ID: add_dust_warning
Revises: 
Create Date: 2025-10-02 14:20:55.030383

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_dust_warning'
down_revision = 'adab6e92356d'
branch_labels = None
depends_on = None
from geoalchemy2 import Geometry

def upgrade():

    op.create_table('dgre_geo_region',
                               sa.Column('gid', sa.String(length=256), nullable=False),
                               sa.Column('country_iso', sa.String(length=3), nullable=False),
                               sa.Column('name', sa.String(length=256), nullable=False),
                               sa.Column('geom', Geometry(geometry_type='MULTIPOLYGON', srid=4326, spatial_index=False, from_text='ST_GeomFromEWKT', name='geometry'), nullable=False),
                               sa.PrimaryKeyConstraint('gid')
                               )
    with op.batch_alter_table('dgre_geo_region', schema=None) as batch_op:
        batch_op.create_index('idx_dgre_geo_region_geom', ['geom'], unique=False, postgresql_using='gist', postgresql_ops={})

    op.create_table('dgre_dust_warning',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('gid', sa.String(length=256), nullable=False),
                    sa.Column('init_date', sa.DateTime(), nullable=False),
                    sa.Column('forecast_date', sa.DateTime(), nullable=False),
                    sa.Column('value', sa.Integer(), nullable=False),
                    sa.ForeignKeyConstraint(['gid'], ['dgre_geo_region.gid'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('gid', 'init_date', 'forecast_date', name='unique_dust_warming_date')
                    )

def downgrade():
    op.drop_table('dgre_dust_warning')

    with op.batch_alter_table('dgre_geo_region', schema=None) as batch_op:
        batch_op.drop_index('idx_dgre_geo_region_geom', postgresql_using='gist', column_name='geom')
    op.drop_table('dgre_geo_region')

