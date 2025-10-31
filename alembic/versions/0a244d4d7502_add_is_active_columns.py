"""Set default True for is_active columns and backfill existing data"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0a244d4d7502'
down_revision = None # your last migration ID
branch_labels = None
depends_on = None


def upgrade():
    # Set default=True at the database level
    op.alter_column('templates', 'is_active',
               existing_type=sa.Boolean(),
               server_default=sa.text('true'),
               existing_nullable=True)

    op.alter_column('sections', 'is_active',
               existing_type=sa.Boolean(),
               server_default=sa.text('true'),
               existing_nullable=True)

    # Backfill existing rows
    conn = op.get_bind()
    conn.execute(sa.text("UPDATE templates SET is_active = true WHERE is_active IS NULL"))
    conn.execute(sa.text("UPDATE sections SET is_active = true WHERE is_active IS NULL"))


def downgrade():
    op.alter_column('templates', 'is_active',
               server_default=None,
               existing_type=sa.Boolean())
    op.alter_column('sections', 'is_active',
               server_default=None,
               existing_type=sa.Boolean())
