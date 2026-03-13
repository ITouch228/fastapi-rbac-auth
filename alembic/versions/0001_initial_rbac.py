"""initial rbac schema"""

from alembic import op
import sqlalchemy as sa

revision = '0001_initial_rbac'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=64), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.UniqueConstraint('name'),
    )
    op.create_table(
        'business_elements',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=64), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.UniqueConstraint('name'),
    )
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('email'),
    )
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_table(
        'access_role_rules',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('role_id', sa.Integer(), sa.ForeignKey('roles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('element_id', sa.Integer(), sa.ForeignKey('business_elements.id', ondelete='CASCADE'), nullable=False),
        sa.Column('read_permission', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('read_all_permission', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('create_permission', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('update_permission', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('update_all_permission', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('delete_permission', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('delete_all_permission', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.UniqueConstraint('role_id', 'element_id', name='uq_role_element'),
    )
    op.create_table(
        'user_roles',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role_id', sa.Integer(), sa.ForeignKey('roles.id', ondelete='CASCADE'), nullable=False),
        sa.UniqueConstraint('user_id', 'role_id', name='uq_user_role'),
    )
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token_jti', sa.String(length=64), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_revoked', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('user_agent', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('token_jti'),
    )
    op.create_index('ix_refresh_tokens_token_jti', 'refresh_tokens', ['token_jti'])


def downgrade() -> None:
    op.drop_index('ix_refresh_tokens_token_jti', table_name='refresh_tokens')
    op.drop_table('refresh_tokens')
    op.drop_table('user_roles')
    op.drop_table('access_role_rules')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
    op.drop_table('business_elements')
    op.drop_table('roles')
