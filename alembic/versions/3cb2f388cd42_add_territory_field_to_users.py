"""add_territory_field_to_users

Revision ID: 3cb2f388cd42
Revises: 7c107bd9796d
Create Date: 2025-05-31 23:42:53.331236

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3cb2f388cd42'
down_revision: Union[str, None] = '7c107bd9796d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('territory', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'territory')
    # ### end Alembic commands ###
