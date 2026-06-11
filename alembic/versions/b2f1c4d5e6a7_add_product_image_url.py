"""add product image_url

Revision ID: b2f1c4d5e6a7
Revises: ab7a905e0ded
Create Date: 2026-06-11 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'b2f1c4d5e6a7'
down_revision: Union[str, Sequence[str], None] = 'ab7a905e0ded'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _columns(bind, table):
    return {c["name"] for c in sa.inspect(bind).get_columns(table)}


def upgrade() -> None:
    """Add product.image_url (idempotent — safe if it already exists)."""
    bind = op.get_bind()
    if "image_url" not in _columns(bind, "product"):
        op.add_column(
            "product",
            sa.Column("image_url", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    if "image_url" in _columns(bind, "product"):
        op.drop_column("product", "image_url")
