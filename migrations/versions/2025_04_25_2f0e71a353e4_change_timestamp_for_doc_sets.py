"""Initial migration for document_vectors"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "2f0e71a353e4"
down_revision: Union[str, None] = "1f0e71a753e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "documents",  # Table name
        "created_at",  # Column name
        type_=sa.DateTime(timezone=True),  # New type
        existing_type=sa.DateTime(timezone=False),  # Old type
        nullable=False,  # Adjust nullability if needed
    )
    op.alter_column(
        "document_sets",  # Table name
        "created_at",  # Column name
        type_=sa.DateTime(timezone=True),  # New type
        existing_type=sa.DateTime(timezone=False),  # Old type
        nullable=False,  # Adjust nullability if needed
    )
    op.alter_column(
        "document_sets",  # Table name
        "updated_at",  # Column name
        type_=sa.DateTime(timezone=True),  # New type
        existing_type=sa.DateTime(timezone=False),  # Old type
        nullable=False,  # Adjust nullability if needed
    )


def downgrade() -> None:

    op.alter_column(
        "documents",  # Table name
        "created_at",  # Column name
        type_=sa.DateTime(timezone=False),  # Old type
        existing_type=sa.DateTime(timezone=True),  # New type
        nullable=False,  # Adjust nullability if needed
    )

    op.alter_column(
        "document_sets",  # Table name
        "created_at",  # Column name
        type_=sa.DateTime(timezone=False),  # Old type
        existing_type=sa.DateTime(timezone=True),  # New type
        nullable=False,  # Adjust nullability if needed
    )

    op.alter_column(
        "document_sets",  # Table name
        "updated_at",  # Column name
        type_=sa.DateTime(timezone=False),  # Old type
        existing_type=sa.DateTime(timezone=True),  # New type
        nullable=False,  # Adjust nullability if needed
    )
