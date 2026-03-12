"""F-03 제안서 테이블 추가

Revision ID: 002_f03_proposals
Revises: 001_add_f10_notifications
Create Date: 2026-03-12

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_f03_proposals'
down_revision = '001_add_f10_notifications'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # companies 테이블이 없으면 생성
    op.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name VARCHAR(200) NOT NULL,
            business_number VARCHAR(20),
            ceo_name VARCHAR(100),
            address VARCHAR(500),
            phone VARCHAR(20),
            email VARCHAR(200),
            description TEXT,
            business_areas VARCHAR(100)[],
            certifications JSONB,
            established_date VARCHAR(10),
            employee_count INTEGER,
            annual_revenue INTEGER,
            is_primary BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
    """)

    op.create_index('idx_companies_user', 'companies', ['user_id'])
    op.create_index('idx_companies_business_number', 'companies', ['business_number'])

    # proposals 테이블 생성
    op.execute("""
        CREATE TABLE proposals (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
            bid_id UUID NOT NULL REFERENCES bids(id) ON DELETE RESTRICT,
            company_id UUID REFERENCES companies(id) ON DELETE SET NULL,
            title VARCHAR(300) NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'draft',
            version INTEGER NOT NULL DEFAULT 1,
            evaluation_checklist JSONB,
            page_count INTEGER DEFAULT 0,
            word_count INTEGER DEFAULT 0,
            generated_at TIMESTAMP,
            submitted_at TIMESTAMP,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
            deleted_at TIMESTAMP
        )
    """)

    op.create_index('idx_proposals_user', 'proposals', ['user_id'], postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_proposals_bid', 'proposals', ['bid_id'], postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_proposals_status', 'proposals', ['status'], postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_proposals_user_updated', 'proposals', ['user_id', 'updated_at'], postgresql_where=sa.text('deleted_at IS NULL'))

    # proposal_sections 테이블 생성
    op.execute("""
        CREATE TABLE proposal_sections (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            proposal_id UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,
            section_key VARCHAR(50) NOT NULL,
            title VARCHAR(200) NOT NULL,
            "order" INTEGER NOT NULL,
            content TEXT,
            metadata JSONB,
            is_ai_generated BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_proposal_sections_key UNIQUE (proposal_id, section_key)
        )
    """)

    op.create_index('idx_proposal_sections_proposal', 'proposal_sections', ['proposal_id'])

    # proposal_versions 테이블 생성
    op.execute("""
        CREATE TABLE proposal_versions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            proposal_id UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,
            version_number INTEGER NOT NULL,
            snapshot JSONB NOT NULL,
            created_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
    """)

    op.create_index('idx_proposal_versions_proposal', 'proposal_versions', ['proposal_id'])

    # bids 테이블에 requirements 컬럼 추가
    op.execute("""
        ALTER TABLE bids ADD COLUMN IF NOT EXISTS requirements JSONB
    """)


def downgrade() -> None:
    op.drop_index('idx_proposal_versions_proposal', 'proposal_versions')
    op.drop_index('idx_proposal_sections_proposal', 'proposal_sections')
    op.drop_index('idx_proposals_user_updated', 'proposals')
    op.drop_index('idx_proposals_status', 'proposals')
    op.drop_index('idx_proposals_bid', 'proposals')
    op.drop_index('idx_proposals_user', 'proposals')

    op.drop_table('proposal_versions')
    op.drop_table('proposal_sections')
    op.drop_table('proposals')

    op.drop_index('idx_companies_business_number', 'companies')
    op.drop_index('idx_companies_user', 'companies')
    op.drop_table('companies')

    op.execute("ALTER TABLE bids DROP COLUMN IF EXISTS requirements")
