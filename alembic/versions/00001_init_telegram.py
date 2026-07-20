import uuid

import sqlalchemy as sa

from alembic import op

revision = '0001_init_telegram'
down_revision = None
branch_labels = None
depends_on = None

from app.core.config import settings


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        'telegram_channel',
        sa.Column(
            'id',
            sa.dialects.postgresql.UUID(as_uuid=True),
            primary_key=True,
            default=uuid.uuid4,
        ),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=False),
        sa.Column('url', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_table(
        'telegram_post',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('content', sa.String(length=255), nullable=True),
        sa.Column('posted_at', sa.DateTime, nullable=False),
        sa.Column('url', sa.String(length=255), nullable=False),
        sa.Column('channel_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('telegram_channel.id'), nullable=False),
        sa.Column('embedding', sa.Vector(settings.rag.embedding_n_dim), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_table(
        'telegram_post_media',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('post_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('telegram_post.id'), nullable=False),
        sa.Column('embedding', sa.Vector(settings.rag.embedding_n_dim), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )


def downgrade():
    op.drop_table('telegram_post_media')
    op.drop_table('telegram_post')
    op.drop_table('telegram_channel')
    op.execute("DROP EXTENSION IF EXISTS vector")