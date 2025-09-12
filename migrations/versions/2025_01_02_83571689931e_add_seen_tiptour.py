"""add seen_tiptour

Revision ID: 83571689931e
Revises: 5f105431d5cd
Create Date: 2025-03-11 11:36:26.162082

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '83571689931e'
down_revision: Union[str, None] = '5f105431d5cd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('seen_tiptour', sa.Boolean(), nullable=False, server_default=sa.text('FALSE')))
    # ### end Alembic commands ###

def downgrade() -> None:
    op.drop_column('users', 'seen_tiptour')
    # ### end Alembic commands ###
