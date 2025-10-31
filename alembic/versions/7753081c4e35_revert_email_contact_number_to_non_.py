"""Revert email/contact_number to non-nullable"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '7753081c4e35'
down_revision = 'f9aafeb0d673'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # Fetch all users with NULL email or contact_number
    result = conn.execute(text("SELECT id FROM users WHERE email IS NULL OR contact_number IS NULL"))
    users = result.fetchall()

    # Assign unique temporary email/contact_number for each user
    for i, (user_id,) in enumerate(users, start=1):
        temp_email = f"temp_{user_id}@example.com"
        temp_contact = f"000000000{i:03d}"
        conn.execute(
            text("UPDATE users SET email = :email, contact_number = :contact WHERE id = :id"),
            {"email": temp_email, "contact": temp_contact, "id": user_id}
        )

    # ✅ Now enforce NOT NULL constraint
    op.alter_column('users', 'email',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.alter_column('users', 'contact_number',
               existing_type=sa.VARCHAR(),
               nullable=False)



def downgrade():
    op.alter_column('users', 'contact_number',
               existing_type=sa.VARCHAR(),
               nullable=True)
    op.alter_column('users', 'email',
               existing_type=sa.VARCHAR(),
               nullable=True)
