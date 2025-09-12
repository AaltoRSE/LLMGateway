"""Initial migration for document_vectors"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '2b9478efe3ef'
down_revision: Union[str, None] = '1b9478efe2ef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create vector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Creating 'document_vectors' table using raw SQL
    op.execute("""
        CREATE TABLE document_vectors (
            id VARCHAR(128) PRIMARY KEY NOT NULL,
            embedding vector(512),
            content TEXT,
            dataframe JSONB,
            blob_data BYTEA,
            blob_meta JSONB,
            blob_mime_type VARCHAR(255),
            meta JSONB
        )
    """)

    # Create indexes
    op.create_index('haystack_hnsw_index', 'document_vectors', ['embedding'], postgresql_using='hnsw', postgresql_ops={'embedding': 'vector_cosine_ops'})
    op.create_index('haystack_keyword_index', 'document_vectors', [sa.text("to_tsvector('english', content)")], postgresql_using='gin')
    op.create_index('idx_meta_document_set_id', 'document_vectors', [sa.text("(meta->>'document_set_id')")])

def downgrade() -> None:
    op.drop_index('idx_meta_document_set_id', table_name='document_vectors')
    op.drop_index('haystack_keyword_index', table_name='document_vectors')
    op.drop_index('haystack_hnsw_index', table_name='document_vectors')
    op.drop_table('document_vectors')
