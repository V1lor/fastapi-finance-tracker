"""Add categories

Revision ID: 157c96cea96c
Revises: dbb89867eeb3
Create Date: 2025-11-27 20:05:04.214401

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '157c96cea96c'
down_revision: Union[str, Sequence[str], None] = 'dbb89867eeb3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from alembic import op
    from sqlalchemy import String, Integer
    from sqlalchemy.sql import table, column

    # Создаем временный объект таблицы для вставки
    categories_table = table('categories',
        column('id', Integer),
        column('name', String)
    )

    op.bulk_insert(categories_table,
        [
            {'name': 'Еда'},
            {'name': 'Транспорт'},
            {'name': 'Жилье'},
            {'name': 'Развлечения'},
            {'name': 'Здоровье'},
            {'name': 'Другое'},
        ]
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass
