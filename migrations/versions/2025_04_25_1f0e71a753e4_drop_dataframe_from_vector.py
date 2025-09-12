"""Initial migration for document_vectors"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "1f0e71a753e4"
down_revision: Union[str, None] = "0c48d277e3c5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # Create indexes
    op.drop_column(
        "document_vectors",
        "dataframe",
    )


def downgrade() -> None:
    op.add_column("document_vectors", "dataframe", JSONB(), nullable=True)
