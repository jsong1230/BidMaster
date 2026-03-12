"""Add F-10 notification system tables

Revision ID: 001_add_f10_notifications
Revises:
Create Date: 2026-03-12 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_add_f10_notifications'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. notifications 테이블 생성
    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('data', postgresql.JSONB(astext_type=sa.Text, as_uuid=False), server_default='{}'),
        sa.Column('is_read', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('channel', sa.String(20), nullable=False, server_default='in_app'),
        sa.Column('sent_at', sa.DateTime, nullable=True),
        sa.Column('read_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
    )

    # 인덱스 생성
    op.create_index(
        'idx_notifications_user_unread',
        'notifications',
        ['user_id', 'is_read'],
        postgresql_where=sa.text('is_read = FALSE'),
    )
    op.create_index(
        'idx_notifications_user_created',
        'notifications',
        ['user_id', sa.text('created_at DESC')],
    )

    # Check constraints
    op.execute("""
        ALTER TABLE notifications
        ADD CONSTRAINT chk_notifications_type
        CHECK (type IN ('bid_matched', 'deadline', 'bid_result', 'proposal_ready'));
    """)
    op.execute("""
        ALTER TABLE notifications
        ADD CONSTRAINT chk_notifications_channel
        CHECK (channel IN ('in_app', 'email', 'kakao'));
    """)

    # 2. notification_settings 테이블 생성
    op.create_table(
        'notification_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('notification_type', sa.String(50), nullable=False),
        sa.Column('email_enabled', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('kakao_enabled', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('push_enabled', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
    )

    # 유니크 제약조건
    op.create_unique_constraint(
        'uq_notification_settings_user_type',
        'notification_settings',
        ['user_id', 'notification_type'],
    )

    # Check constraint
    op.execute("""
        ALTER TABLE notification_settings
        ADD CONSTRAINT chk_notification_settings_type
        CHECK (notification_type IN ('bid_matched', 'deadline', 'bid_result', 'proposal_ready'));
    """)

    # 3. user_bid_matches에 status 컬럼 추가
    op.add_column('user_bid_matches', sa.Column('status', sa.String(20), nullable=False, server_default='new'))
    op.create_index('idx_user_bid_matches_status', 'user_bid_matches', ['status'])

    # 4. 기존 사용자 기본 알림 설정 생성
    op.execute("""
        INSERT INTO notification_settings (user_id, notification_type, email_enabled, kakao_enabled, push_enabled)
        SELECT
            u.id,
            t.notification_type,
            TRUE,
            FALSE,
            TRUE
        FROM users u
        CROSS JOIN (
            VALUES
                ('bid_matched'),
                ('deadline'),
                ('bid_result'),
                ('proposal_ready')
        ) AS t(notification_type)
        WHERE u.deleted_at IS NULL
        ON CONFLICT (user_id, notification_type) DO NOTHING;
    """)


def downgrade() -> None:
    # user_bid_matches status 컬럼 제거
    op.drop_index('idx_user_bid_matches_status', 'user_bid_matches')
    op.drop_column('user_bid_matches', 'status')

    # notification_settings 테이블 제거
    op.drop_constraint('chk_notification_settings_type', 'notification_settings', type_='check')
    op.drop_constraint('uq_notification_settings_user_type', 'notification_settings', type_='unique')
    op.drop_table('notification_settings')

    # notifications 테이블 제거
    op.drop_constraint('chk_notifications_channel', 'notifications', type_='check')
    op.drop_constraint('chk_notifications_type', 'notifications', type_='check')
    op.drop_index('idx_notifications_user_created', 'notifications')
    op.drop_index('idx_notifications_user_unread', 'notifications')
    op.drop_table('notifications')
