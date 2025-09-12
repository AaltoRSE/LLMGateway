"""Increase document title length

Revision ID: 616ad38220cd
Revises: 2f0e71a353e4
Create Date: 2025-04-28 06:44:02.348735

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '616ad38220cd'
down_revision: Union[str, None] = '2f0e71a353e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('documents', 'title',
               existing_type=sa.String(length=60),
               type_=sa.String(length=260))

def downgrade() -> None:
    op.alter_column('documents', 'title',
               existing_type=sa.String(length=60),
               type_=sa.String(length=260))
