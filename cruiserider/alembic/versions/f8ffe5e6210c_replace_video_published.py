"""replace video published flag with status

Revision ID: f8ffe5e6210c
Revises: e07a543ef741
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f8ffe5e6210c"
down_revision: Union[str, Sequence[str], None] = "e07a543ef741"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add status temporarily as nullable
    op.add_column(
        "videos",
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=True
        )
    )

    # Convert existing publishing state
    op.execute(
        """
        UPDATE videos
        SET status = CASE
            WHEN is_published = TRUE THEN 'PUBLISHED'
            ELSE 'DRAFT'
        END
        """
    )

    # Make status mandatory
    op.alter_column(
        "videos",
        "status",
        existing_type=sa.String(length=20),
        nullable=False
    )

    # Remove old publishing flag
    op.drop_column(
        "videos",
        "is_published"
    )


def downgrade() -> None:
    # Restore old publishing flag
    op.add_column(
        "videos",
        sa.Column(
            "is_published",
            sa.Boolean(),
            nullable=True
        )
    )

    # Convert status back to boolean
    op.execute(
        """
        UPDATE videos
        SET is_published = CASE
            WHEN status = 'PUBLISHED' THEN TRUE
            ELSE FALSE
        END
        """
    )

    # Make old column mandatory
    op.alter_column(
        "videos",
        "is_published",
        existing_type=sa.Boolean(),
        nullable=False
    )

    # Remove status
    op.drop_column(
        "videos",
        "status"
    )