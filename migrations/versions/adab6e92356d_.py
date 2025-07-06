"""empty message

Revision ID: adab6e92356d
Revises: 
Create Date: 2025-06-26 14:20:55.030383

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'adab6e92356d'
down_revision = None
branch_labels = None
depends_on = None
from geoalchemy2 import Geometry


def upgrade():
    op.create_table('dgre_river_segment',
                    sa.Column('fid', sa.Integer(), nullable=False),
                    sa.Column('subid', sa.String(), nullable=False),
                    sa.Column('geom', Geometry(geometry_type='MULTILINESTRING', srid=4326, spatial_index=False, from_text='ST_GeomFromEWKT', name='geometry'),    nullable=False),
                    sa.PrimaryKeyConstraint('subid')
                    )

    op.create_table('dgre_municipality',
                    sa.Column('subid', sa.Integer(), nullable=False),
                    sa.Column('adm3_fr', sa.String(length=256), nullable=False),
                    sa.Column('adm2_fr', sa.String(length=256), nullable=False),
                    sa.Column('geom', Geometry(geometry_type='MULTIPOLYGON', srid=4326, spatial_index=False, from_text='ST_GeomFromEWKT', name='geometry'),    nullable=False),
                    sa.PrimaryKeyConstraint('subid'),
                    )
    with op.batch_alter_table('dgre_municipality', schema=None) as batch_op:
        batch_op.create_index('idx_dgre_municipality_geom', ['geom'], unique=False, postgresql_using='gist', postgresql_ops={})


    op.create_table('dgre_riverine_flood',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('fid', sa.Integer(), nullable=False),
                    sa.Column('subid', sa.String(), nullable=False),
                    sa.Column('init_date', sa.DateTime(), nullable=False),
                    sa.Column('forecast_date', sa.DateTime(), nullable=False),
                    sa.Column('init_value', sa.Integer(), nullable=False),
                    sa.Column('value', sa.Integer(), nullable=False),
                    sa.PrimaryKeyConstraint('id'),
                    sa.ForeignKeyConstraint(['subid'], ['dgre_river_segment.subid'], ondelete='CASCADE'),
                    sa.UniqueConstraint( 'subid', 'init_date', 'forecast_date', name='unique_riverine_flood_date')
                    )

    op.create_table('dgre_flash_flood',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('fid', sa.Integer(), nullable=False),
                    sa.Column('subid', sa.Integer(), nullable=False),
                    sa.Column('adm3_fr', sa.String(length=256), nullable=False),
                    sa.Column('forecast_date', sa.DateTime(), nullable=False),
                    sa.Column('init_value', sa.Integer(), nullable=False),
                    sa.Column('value', sa.Integer(), nullable=False),
                    sa.PrimaryKeyConstraint('id'),
                    sa.ForeignKeyConstraint(['subid'], ['dgre_municipality.subid'], ondelete='CASCADE'),
                    sa.UniqueConstraint( 'subid', 'forecast_date', name='unique_flash_flood_date')
                    )

def downgrade():
    op.drop_table('dgre_riverine_flood')
    op.drop_table('dgre_flash_flood')
    op.drop_table('dgre_river_segment')

    with op.batch_alter_table('dgre_municipality', schema=None) as batch_op:
        batch_op.drop_index('idx_dgre_municipality_geom', postgresql_using='gist', column_name='geom')
    op.drop_table('dgre_municipality')
