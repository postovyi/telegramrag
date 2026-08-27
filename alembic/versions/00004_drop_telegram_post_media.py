import uuid

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

from alembic import op

revision = '0004_drop_telegram_post_media'
down_revision = '0003_resize_embeddings_1024'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table('telegram_post_media')


def downgrade():
    op.create_table(
        'telegram_post_media',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column(
            'post_id',
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey('telegram_post.id'),
            nullable=False,
        ),
        sa.Column('embedding', Vector(1024), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
