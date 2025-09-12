"""Initial migrations 2.0

Revision ID: 1b9478efe2ef
Revises:
Create Date: 2024-09-06 09:22:05.699909

"""
from datetime import datetime, timezone
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1b9478efe2ef'
down_revision: Union[str, None] = '83571689931e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create 'document_sets' table
    op.create_table(
        'document_sets',
        sa.Column('id', sa.Integer, primary_key=True, nullable=False, unique=True, autoincrement=True),
        sa.Column('name', sa.String(60), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('embedding', sa.String(60), nullable=False),
        sa.Column('embedding_dimension', sa.Integer, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)),
        sa.Column('updated_at', sa.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_document_sets_user_id_users'))
    )

    # Create documents table
    op.create_table(
       'documents',
       sa.Column('id', sa.Integer, primary_key=True, nullable=False, unique=True, autoincrement=True),
       sa.Column('document_set_id', sa.Integer, sa.ForeignKey('document_sets.id'), nullable=False),
       sa.Column('title', sa.String(60), nullable=False),
       sa.Column('text_content', sa.Text, nullable=False),
       sa.Column('created_at', sa.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)),
    )
    op.create_index(op.f('ix_documents_document_set_id'), 'documents', ['document_set_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_documents_document_set_id'), table_name='documents')
    op.drop_table('documents')
    op.drop_table('document_sets')