"""add search

Revision ID: 521c26172c55
Revises: 92323df3558f
Create Date: 2025-02-15 15:40:28.001812

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.models import custom_types

# revision identifiers, used by Alembic.
revision: str = '521c26172c55'
down_revision: Union[str, None] = '92323df3558f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "searches",
        sa.Column("id", custom_types.UUID_as_Integer(), nullable=False),
        sa.Column("question", sa.String(), nullable=True),
        sa.Column("response", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("searches")
    # ### end Alembic commands ###