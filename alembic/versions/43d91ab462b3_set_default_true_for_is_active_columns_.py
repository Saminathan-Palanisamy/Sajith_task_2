"""Set default True for is_active columns and backfill existing data

Revision ID: 43d91ab462b3
Revises: 7753081c4e35
Create Date: 2025-10-31 12:38:03.502738

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '43d91ab462b3'
down_revision: Union[str, Sequence[str], None] = '7753081c4e35'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Set default True for new rows
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('is_active',
            existing_type=sa.Boolean(),
            server_default=sa.text('true'),
            existing_nullable=True)

    # 🟢 Backfill existing rows
    op.execute("UPDATE users SET is_active = TRUE WHERE is_active IS NULL;")

def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('is_active',
            existing_type=sa.Boolean(),
            server_default=None,
            existing_nullable=True)