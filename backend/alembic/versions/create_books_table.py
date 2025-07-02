"""Create books table

Revision ID: create_books_table
Revises: create_users_table
Create Date: 2025-07-02 06:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'create_books_table'
down_revision: Union[str, None] = 'create_users_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'books',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('author', sa.String(length=255), nullable=True),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=255), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('file_type', sa.String(length=10), nullable=False),
        sa.Column('processing_status', sa.String(length=20), nullable=False),
        sa.Column('processing_error', sa.Text(), nullable=True),
        sa.Column('page_count', sa.Integer(), nullable=True),
        sa.Column('word_count', sa.Integer(), nullable=True),
        sa.Column('language', sa.String(length=50), nullable=True),
        sa.Column('isbn', sa.String(length=20), nullable=True),
        sa.Column('publisher', sa.String(length=255), nullable=True),
        sa.Column('publication_year', sa.Integer(), nullable=True),
        sa.Column('raw_text', sa.Text(), nullable=True),
        sa.Column('cleaned_text', sa.Text(), nullable=True),
        sa.Column('is_embedded', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('embedding_model', sa.String(length=100), nullable=True),
        sa.Column('chunk_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('synopsis', sa.Text(), nullable=True),
        sa.Column('chapter_summary', sa.JSON(), nullable=True),
        sa.Column('firebase_user_id', sa.String(length=128), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_books_title'), 'books', ['title'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_books_title'), table_name='books')
    op.drop_table('books') 