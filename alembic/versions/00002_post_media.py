import uuid

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

from alembic import op
from app.core.config import settings

revision = '0002_post_media'
down_revision = '0001_init_telegram'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Vectors from the previous embedding model are in a different space (and dimension) and cannot be cast.
    op.execute('DELETE FROM telegram_post')
    op.alter_column(
        'telegram_post',
        'embedding',
        existing_type=Vector(),
        type_=Vector(settings.rag.embedding_n_dim),
        nullable=True,
        postgresql_using=None,
    )
    op.create_table(
        'telegram_post_media',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column(
            'post_id',
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey('telegram_post.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('position', sa.Integer, nullable=False, server_default='0'),
        sa.Column('data', sa.LargeBinary, nullable=False),
        sa.Column('mime_type', sa.String(length=64), nullable=False),
        sa.Column('embedding', Vector(settings.rag.embedding_n_dim), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_telegram_post_media_post_id', 'telegram_post_media', ['post_id'])
    op.create_index('ix_telegram_post_media_id', 'telegram_post_media', ['id'])


def downgrade() -> None:
    op.drop_table('telegram_post_media')
    op.execute('DELETE FROM telegram_post WHERE embedding IS NULL')
    op.alter_column('telegram_post', 'embedding', existing_type=Vector(), nullable=False)
