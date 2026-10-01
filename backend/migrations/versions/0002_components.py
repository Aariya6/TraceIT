"""field protocols, interventions, data sources and observation validation"""
from alembic import op
import sqlalchemy as sa
revision='0002_components'; down_revision='0001_initial'; branch_labels=None; depends_on=None

def upgrade():
    op.add_column('users',sa.Column('role',sa.String(30),nullable=False,server_default='citizen'))
    op.add_column('observations',sa.Column('validation',sa.JSON(),nullable=False,server_default='{}'))
    op.create_table('field_protocols',sa.Column('id',sa.Integer(),primary_key=True),sa.Column('water_body_id',sa.Integer(),sa.ForeignKey('water_bodies.id',ondelete='CASCADE'),nullable=False),sa.Column('title',sa.String(180),nullable=False),sa.Column('version',sa.String(30),nullable=False),sa.Column('steps',sa.JSON(),nullable=False),sa.Column('required_measurements',sa.JSON(),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False))
    op.create_table('interventions',sa.Column('id',sa.Integer(),primary_key=True),sa.Column('water_body_id',sa.Integer(),sa.ForeignKey('water_bodies.id',ondelete='CASCADE'),nullable=False),sa.Column('created_by_id',sa.Integer(),sa.ForeignKey('users.id',ondelete='SET NULL')),sa.Column('title',sa.String(180),nullable=False),sa.Column('status',sa.String(30),nullable=False),sa.Column('action_type',sa.String(60),nullable=False),sa.Column('notes',sa.Text(),nullable=False),sa.Column('target_date',sa.DateTime(timezone=True)),sa.Column('outcome',sa.Text(),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False))
    op.create_table('data_sources',sa.Column('id',sa.Integer(),primary_key=True),sa.Column('name',sa.String(150),nullable=False),sa.Column('kind',sa.String(40),nullable=False),sa.Column('url',sa.String(500),nullable=False),sa.Column('description',sa.Text(),nullable=False),sa.Column('update_frequency',sa.String(80),nullable=False),sa.Column('enabled',sa.Boolean(),nullable=False),sa.Column('last_checked_at',sa.DateTime(timezone=True)),sa.Column('metadata_json',sa.JSON(),nullable=False))

def downgrade():
    op.drop_table('data_sources');op.drop_table('interventions');op.drop_table('field_protocols');op.drop_column('observations','validation');op.drop_column('users','role')
