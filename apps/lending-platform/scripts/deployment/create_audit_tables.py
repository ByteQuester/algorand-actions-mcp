#!/usr/bin/env python3
"""
Create Audit Tables for Lending Platform
Sets up all required database tables for audit trail and compliance
"""

import asyncio
import asyncpg
import os
from datetime import datetime

# Database connection from environment
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://lending_admin:secure_password_123@localhost:5432/lending_platform')


async def create_audit_tables():
    """Create all audit system tables"""

    print("🗄️ Creating Audit Tables")
    print("=" * 50)

    conn = await asyncpg.connect(DATABASE_URL)

    try:
        # Create audit_events table with partitioning
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_events (
                event_id UUID PRIMARY KEY,
                event_type VARCHAR(100) NOT NULL,
                timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                user_id VARCHAR(255),
                session_id VARCHAR(255),
                loan_id VARCHAR(255),
                agent_name VARCHAR(255),
                details JSONB,
                ip_address INET,
                user_agent TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW()
            ) PARTITION BY RANGE (timestamp);

            -- Create indexes for performance
            CREATE INDEX IF NOT EXISTS idx_audit_events_loan_id ON audit_events(loan_id);
            CREATE INDEX IF NOT EXISTS idx_audit_events_user_id ON audit_events(user_id);
            CREATE INDEX IF NOT EXISTS idx_audit_events_timestamp ON audit_events(timestamp);
            CREATE INDEX IF NOT EXISTS idx_audit_events_event_type ON audit_events(event_type);
            CREATE INDEX IF NOT EXISTS idx_audit_events_agent ON audit_events(agent_name);
        """)
        print("✅ Created audit_events table")

        # Create monthly partitions for current and next 3 months
        current_month = datetime.now()
        for i in range(4):
            month = current_month.month + i
            year = current_month.year
            if month > 12:
                month -= 12
                year += 1

            partition_name = f"audit_events_{year}_{month:02d}"
            start_date = f"{year}-{month:02d}-01"
            end_month = month + 1 if month < 12 else 1
            end_year = year if month < 12 else year + 1
            end_date = f"{end_year}-{end_month:02d}-01"

            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {partition_name}
                PARTITION OF audit_events
                FOR VALUES FROM ('{start_date}') TO ('{end_date}');
            """)
            print(f"✅ Created partition: {partition_name}")

        # Create compliance_checks table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS compliance_checks (
                check_id UUID PRIMARY KEY,
                loan_id VARCHAR(255) NOT NULL,
                check_type VARCHAR(100) NOT NULL,
                decision_data JSONB NOT NULL,
                compliance_score NUMERIC(5,2),
                bias_score NUMERIC(5,2),
                issues JSONB,
                passed BOOLEAN,
                checked_at TIMESTAMPTZ DEFAULT NOW(),
                checked_by VARCHAR(255)
            );

            CREATE INDEX IF NOT EXISTS idx_compliance_loan_id ON compliance_checks(loan_id);
            CREATE INDEX IF NOT EXISTS idx_compliance_check_type ON compliance_checks(check_type);
            CREATE INDEX IF NOT EXISTS idx_compliance_passed ON compliance_checks(passed);
        """)
        print("✅ Created compliance_checks table")

        # Create decision_traces table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS decision_traces (
                trace_id UUID PRIMARY KEY,
                loan_id VARCHAR(255) NOT NULL,
                decision_id VARCHAR(255) NOT NULL,
                decision_type VARCHAR(100),
                decision_node JSONB,
                factors JSONB,
                explanations JSONB,
                stakeholder_views JSONB,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );

            CREATE INDEX IF NOT EXISTS idx_traces_loan_id ON decision_traces(loan_id);
            CREATE INDEX IF NOT EXISTS idx_traces_decision_id ON decision_traces(decision_id);
        """)
        print("✅ Created decision_traces table")

        # Create lending_sessions table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS lending_sessions (
                session_id UUID PRIMARY KEY,
                loan_id VARCHAR(255) UNIQUE NOT NULL,
                borrower_address VARCHAR(255) NOT NULL,
                loan_amount NUMERIC(20,6),
                interest_rate NUMERIC(5,2),
                duration_days INTEGER,
                collateral_amount NUMERIC(20,6),
                status VARCHAR(50),
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                completed_at TIMESTAMPTZ,
                metadata JSONB
            );

            CREATE INDEX IF NOT EXISTS idx_sessions_borrower ON lending_sessions(borrower_address);
            CREATE INDEX IF NOT EXISTS idx_sessions_status ON lending_sessions(status);
        """)
        print("✅ Created lending_sessions table")

        # Create agent_metrics table for performance tracking
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_metrics (
                metric_id UUID PRIMARY KEY,
                agent_name VARCHAR(255) NOT NULL,
                action VARCHAR(255) NOT NULL,
                execution_time_ms INTEGER,
                success BOOLEAN,
                error_details TEXT,
                loan_id VARCHAR(255),
                timestamp TIMESTAMPTZ DEFAULT NOW()
            );

            CREATE INDEX IF NOT EXISTS idx_metrics_agent ON agent_metrics(agent_name);
            CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON agent_metrics(timestamp);
        """)
        print("✅ Created agent_metrics table")

        # Create real_time_events table for WebSocket streaming
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS real_time_events (
                event_id UUID PRIMARY KEY,
                event_type VARCHAR(100) NOT NULL,
                payload JSONB NOT NULL,
                broadcast_to TEXT[],
                broadcasted BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );

            CREATE INDEX IF NOT EXISTS idx_realtime_broadcasted ON real_time_events(broadcasted);
            CREATE INDEX IF NOT EXISTS idx_realtime_created ON real_time_events(created_at);
        """)
        print("✅ Created real_time_events table")

        print("\n🎉 All tables created successfully!")

        # Verify tables
        tables = await conn.fetch("""
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename;
        """)

        print("\n📋 Available tables:")
        for table in tables:
            print(f"   • {table['tablename']}")

    finally:
        await conn.close()


async def create_sample_data():
    """Insert sample data for testing"""

    print("\n📝 Creating Sample Data")
    print("=" * 50)

    conn = await asyncpg.connect(DATABASE_URL)

    try:
        # Insert sample lending session
        await conn.execute("""
            INSERT INTO lending_sessions (
                session_id, loan_id, borrower_address,
                loan_amount, interest_rate, duration_days,
                collateral_amount, status, metadata
            ) VALUES (
                gen_random_uuid(),
                'DEMO_LOAN_001',
                'DEMO_BORROWER_ADDRESS_123',
                50.0,
                7.2,
                60,
                65.0,
                'pending_approval',
                '{"purpose": "business_expansion", "risk_score": 75}'::jsonb
            ) ON CONFLICT (loan_id) DO NOTHING;
        """)
        print("✅ Created sample lending session")

        # Insert sample audit events
        await conn.execute("""
            INSERT INTO audit_events (
                event_id, event_type, user_id, loan_id,
                agent_name, details
            ) VALUES (
                gen_random_uuid(),
                'loan_request_created',
                'demo_user',
                'DEMO_LOAN_001',
                'coordination_agent',
                '{"action": "loan_request_initialized", "amount": 50.0}'::jsonb
            );
        """)
        print("✅ Created sample audit events")

        # Insert sample compliance check
        await conn.execute("""
            INSERT INTO compliance_checks (
                check_id, loan_id, check_type,
                decision_data, compliance_score, bias_score,
                passed
            ) VALUES (
                gen_random_uuid(),
                'DEMO_LOAN_001',
                'interest_rate_fairness',
                '{"rate": 7.2, "market_rate": 7.5}'::jsonb,
                95.0,
                5.0,
                true
            );
        """)
        print("✅ Created sample compliance check")

        print("\n✅ Sample data created successfully!")

    finally:
        await conn.close()


async def verify_setup():
    """Verify database setup and connectivity"""

    print("\n🔍 Verifying Database Setup")
    print("=" * 50)

    conn = await asyncpg.connect(DATABASE_URL)

    try:
        # Check row counts
        tables = ['audit_events', 'compliance_checks', 'lending_sessions']

        for table in tables:
            count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
            print(f"✅ {table}: {count} rows")

        # Test query performance
        import time
        start = time.time()
        result = await conn.fetch("""
            SELECT * FROM audit_events
            WHERE loan_id = 'DEMO_LOAN_001'
            LIMIT 10
        """)
        elapsed = (time.time() - start) * 1000
        print(f"\n⚡ Query performance: {elapsed:.2f}ms for {len(result)} rows")

        print("\n🎉 Database setup verified successfully!")

    finally:
        await conn.close()


async def main():
    """Main setup function"""

    print("🚀 LENDING PLATFORM DATABASE SETUP")
    print("=" * 60)
    print(f"Database URL: {DATABASE_URL}")
    print()

    try:
        # Create tables
        await create_audit_tables()

        # Create sample data
        await create_sample_data()

        # Verify setup
        await verify_setup()

        print("\n✅ Database setup complete!")
        print("📋 Next steps:")
        print("   1. Start API server: python src/api/server.py")
        print("   2. Run integration tests: python tests/integration/test_complete_system.py")
        print("   3. View demo: python scripts/demo/run_demo.py")

    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        print("🔧 Troubleshooting:")
        print("   1. Check PostgreSQL is running: sudo systemctl status postgresql")
        print("   2. Verify connection string in .env file")
        print("   3. Ensure database user has proper permissions")
        return False

    return True


if __name__ == "__main__":
    success = asyncio.run(main())