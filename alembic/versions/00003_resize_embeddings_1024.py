from alembic import op

revision = '0003_resize_embeddings_1024'
down_revision = '0002_widen_post_content'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('ALTER TABLE telegram_post ALTER COLUMN embedding TYPE vector(1024)')
    op.execute('ALTER TABLE telegram_post_media ALTER COLUMN embedding TYPE vector(1024)')


def downgrade():
    op.execute('ALTER TABLE telegram_post ALTER COLUMN embedding TYPE vector(512)')
    op.execute('ALTER TABLE telegram_post_media ALTER COLUMN embedding TYPE vector(512)')
