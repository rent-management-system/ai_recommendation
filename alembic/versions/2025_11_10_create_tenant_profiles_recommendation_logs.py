from alembic import op
import sqlalchemy as sa

revision = "e08b90822536"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "TenantProfiles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("Users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_school_location", sa.String(255)),
        sa.Column("salary", sa.Float),
        sa.Column("house_type", sa.String(50)),
        sa.Column("family_size", sa.Integer),
        sa.Column("preferred_amenities", sa.ARRAY(sa.String)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.current_timestamp())
    )
    op.create_table(
        "RecommendationLogs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("tenant_id", sa.Integer, sa.ForeignKey("TenantProfiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("recommendation", sa.JSONB),
        sa.Column("feedback", sa.JSONB),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.current_timestamp())
    )

def downgrade():
    op.drop_table("RecommendationLogs")
    op.drop_table("TenantProfiles")
