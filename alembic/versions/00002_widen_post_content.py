import sqlalchemy as sa

from alembic import op

revision = '0002_widen_post_content'
down_revision = '0001_init_telegram'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('telegram_post', 'content', type_=sa.Text(), existing_nullable=True)


def downgrade():
    op.alter_column('telegram_post', 'content', type_=sa.String(length=255), existing_nullable=True)
