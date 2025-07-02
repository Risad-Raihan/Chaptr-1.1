"""Add owner_id to books table

Revision ID: add_owner_id_to_books
Revises: create_books_table
Create Date: 2025-07-02 09:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_owner_id_to_books'
down_revision: Union[str, None] = 'create_books_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add owner_id column
    op.add_column('books', sa.Column('owner_id', sa.Integer(), nullable=False))
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_books_owner_id_users',
        'books',
        'users',
        ['owner_id'],
        ['id']
    )


def downgrade() -> None:
    # Drop foreign key constraint first
    op.drop_constraint('fk_books_owner_id_users', 'books', type_='foreignkey')
    
    # Then drop the column
    op.drop_column('books', 'owner_id') 