#!/usr/bin/env python3
"""
🏢 LeanVibe Enterprise Demo Setup Script

This script creates a complete enterprise SaaS demonstration environment with:
- Multi-tenant organizations with realistic data
- Enterprise authentication demo users
- Billing plans and subscription samples
- AI development tasks for showcase
- Monitoring and analytics sample data
"""

import sys
import os
import uuid
import bcrypt
from datetime import datetime, timedelta
from decimal import Decimal

# Add app directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.tenant_models import Tenant, TenantUser
    from app.models.billing_models import SubscriptionPlan, TenantSubscription, UsageRecord
    from app.models.task_models import DevelopmentTask, AIAgent, TaskStatus, TaskPriority
    from app.models.auth_models import SSOProvider, MFAToken
    from app.core.database import Base
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("⚠️  Continuing without database setup - models may not be available")

def get_database_session():
    """Get database session for demo setup"""
    # Use SQLite for demo simplicity
    database_url = "sqlite:///./leanvibe_demo.db"
    engine = create_engine(database_url, connect_args={"check_same_thread": False})
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def create_demo_tenants(db):
    """Create demo tenant organizations"""
    print("🏢 Creating demo tenants...")
    
    demo_tenants = [
        {
            "id": "acme-corp-" + str(uuid.uuid4())[:8],
            "organization_name": "Acme Corporation",
            "subdomain": "acme-corp",
            "plan": "enterprise",
            "billing_email": "billing@acme-corp.com",
            "settings": {
                "industry": "Technology",
                "employees": "1000+",
                "sso_enabled": True,
                "mfa_required": True,
                "custom_branding": True
            }
        },
        {
            "id": "techstart-" + str(uuid.uuid4())[:8],
            "organization_name": "TechStart Inc",
            "subdomain": "techstart",
            "plan": "professional",
            "billing_email": "billing@techstart.com",
            "settings": {
                "industry": "SaaS",
                "employees": "50-100",
                "sso_enabled": True,
                "mfa_required": False,
                "growth_stage": "Series A"
            }
        },
        {
            "id": "global-enterprises-" + str(uuid.uuid4())[:8],
            "organization_name": "Global Enterprises",
            "subdomain": "global-ent",
            "plan": "enterprise",
            "billing_email": "procurement@global-enterprises.com",
            "settings": {
                "industry": "Financial Services",
                "employees": "10000+",
                "sso_enabled": True,
                "mfa_required": True,
                "compliance": ["SOC2", "GDPR", "HIPAA"],
                "custom_contract": True
            }
        }
    ]
    
    created_tenants = []
    for tenant_data in demo_tenants:
        # Check if tenant already exists
        existing = db.query(Tenant).filter(Tenant.subdomain == tenant_data["subdomain"]).first()
        if existing:
            print(f"   ⚠️  Tenant {tenant_data['organization_name']} already exists, skipping...")
            created_tenants.append(existing)
            continue
            
        tenant = Tenant(
            id=tenant_data["id"],
            organization_name=tenant_data["organization_name"],
            subdomain=tenant_data["subdomain"],
            plan=tenant_data["plan"],
            billing_email=tenant_data["billing_email"],
            settings=tenant_data["settings"]
        )
        db.add(tenant)
        created_tenants.append(tenant)
        print(f"   ✅ Created tenant: {tenant_data['organization_name']} ({tenant_data['subdomain']})")
    
    db.commit()
    return created_tenants

def create_demo_users(db, tenants):
    """Create demo users for each tenant"""
    print("👥 Creating demo users...")
    
    demo_users = [
        {
            "tenant": tenants[0],  # Acme Corp
            "email": "admin@acme-corp.com",
            "username": "acme_admin",
            "role": "admin",
            "full_name": "John Smith",
            "password": "enterprise_demo"
        },
        {
            "tenant": tenants[0],  # Acme Corp
            "email": "developer@acme-corp.com", 
            "username": "acme_dev",
            "role": "developer",
            "full_name": "Sarah Johnson",
            "password": "enterprise_demo"
        },
        {
            "tenant": tenants[1],  # TechStart
            "email": "user@techstart.com",
            "username": "techstart_user",
            "role": "user",
            "full_name": "Mike Wilson",
            "password": "professional_demo"
        },
        {
            "tenant": tenants[2],  # Global Enterprises
            "email": "enterprise@global.com",
            "username": "global_admin",
            "role": "admin", 
            "full_name": "Lisa Chen",
            "password": "custom_demo"
        }
    ]
    
    created_users = []
    for user_data in demo_users:
        # Check if user already exists
        existing = db.query(TenantUser).filter(
            TenantUser.email == user_data["email"],
            TenantUser.tenant_id == user_data["tenant"].id
        ).first()
        if existing:
            print(f"   ⚠️  User {user_data['email']} already exists, skipping...")
            created_users.append(existing)
            continue
            
        # Hash password
        hashed_password = bcrypt.hashpw(
            user_data["password"].encode('utf-8'), 
            bcrypt.gensalt()
        ).decode('utf-8')
        
        user = TenantUser(
            tenant_id=user_data["tenant"].id,
            email=user_data["email"],
            username=user_data["username"],
            role=user_data["role"],
            full_name=user_data.get("full_name", ""),
            hashed_password=hashed_password
        )
        db.add(user)
        created_users.append(user)
        print(f"   ✅ Created user: {user_data['email']} ({user_data['role']})")
    
    db.commit()
    return created_users

def create_subscription_plans(db):
    """Create demo subscription plans"""
    print("💳 Creating subscription plans...")
    
    demo_plans = [
        {
            "id": "developer_plan_demo",
            "name": "Developer",
            "description": "Perfect for individual developers and small projects",
            "base_price": Decimal("50.00"),
            "billing_interval": "month",
            "currency": "usd",
            "features": {
                "users": 1,
                "projects": 5,
                "ai_requests_monthly": 10000,
                "storage_gb": 1,
                "support": "email",
                "sso": False,
                "api_access": True
            },
            "usage_limits": {
                "api_calls_monthly": 100000,
                "bandwidth_gb_monthly": 10
            }
        },
        {
            "id": "professional_plan_demo", 
            "name": "Professional",
            "description": "For growing teams and professional development",
            "base_price": Decimal("200.00"),
            "billing_interval": "month",
            "currency": "usd",
            "features": {
                "users": 10,
                "projects": 50,
                "ai_requests_monthly": 100000,
                "storage_gb": 10,
                "support": "priority",
                "sso": True,
                "api_access": True,
                "webhooks": True
            },
            "usage_limits": {
                "api_calls_monthly": 1000000,
                "bandwidth_gb_monthly": 100
            }
        },
        {
            "id": "enterprise_plan_demo",
            "name": "Enterprise",
            "description": "For large organizations with advanced requirements",
            "base_price": Decimal("800.00"),
            "billing_interval": "month", 
            "currency": "usd",
            "features": {
                "users": "unlimited",
                "projects": "unlimited", 
                "ai_requests_monthly": 1000000,
                "storage_gb": 1000,
                "support": "dedicated",
                "sso": True,
                "saml": True,
                "mfa": True,
                "api_access": True,
                "webhooks": True,
                "custom_branding": True,
                "sla": "99.95%"
            },
            "usage_limits": {
                "api_calls_monthly": "unlimited",
                "bandwidth_gb_monthly": "unlimited"
            }
        }
    ]
    
    created_plans = []
    for plan_data in demo_plans:
        # Check if plan already exists
        existing = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_data["id"]).first()
        if existing:
            print(f"   ⚠️  Plan {plan_data['name']} already exists, skipping...")
            created_plans.append(existing)
            continue
            
        plan = SubscriptionPlan(
            id=plan_data["id"],
            name=plan_data["name"],
            description=plan_data["description"],
            base_price=plan_data["base_price"],
            billing_interval=plan_data["billing_interval"],
            currency=plan_data["currency"],
            features=plan_data["features"],
            usage_limits=plan_data["usage_limits"]
        )
        db.add(plan)
        created_plans.append(plan)
        print(f"   ✅ Created plan: {plan_data['name']} (${plan_data['base_price']}/month)")
    
    db.commit()
    return created_plans

def create_demo_subscriptions(db, tenants, plans):
    """Create demo subscriptions for tenants"""
    print("📊 Creating demo subscriptions...")
    
    # Map tenants to plans
    tenant_plan_mapping = [
        (tenants[0], plans[2], "stripe_sub_acme_demo"),     # Acme Corp -> Enterprise
        (tenants[1], plans[1], "stripe_sub_techstart_demo"), # TechStart -> Professional  
        (tenants[2], plans[2], "stripe_sub_global_demo")     # Global -> Enterprise
    ]
    
    created_subscriptions = []
    for tenant, plan, stripe_id in tenant_plan_mapping:
        # Check if subscription already exists
        existing = db.query(TenantSubscription).filter(
            TenantSubscription.tenant_id == tenant.id
        ).first()
        if existing:
            print(f"   ⚠️  Subscription for {tenant.organization_name} already exists, skipping...")
            created_subscriptions.append(existing)
            continue
            
        subscription = TenantSubscription(
            tenant_id=tenant.id,
            stripe_subscription_id=stripe_id,
            stripe_customer_id=f"cus_demo_{tenant.subdomain}",
            plan_id=plan.id,
            status="active",
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=30)
        )
        db.add(subscription)
        created_subscriptions.append(subscription)
        print(f"   ✅ Created subscription: {tenant.organization_name} -> {plan.name}")
    
    db.commit()
    return created_subscriptions

def create_demo_usage_records(db, tenants):
    """Create sample usage records for analytics"""
    print("📈 Creating demo usage records...")
    
    import random
    
    usage_metrics = [
        "api_calls",
        "ai_requests", 
        "storage_gb",
        "users_active",
        "projects_created"
    ]
    
    created_records = 0
    for tenant in tenants:
        # Create usage records for the past 30 days
        for days_ago in range(30):
            date = datetime.utcnow() - timedelta(days=days_ago)
            
            for metric in usage_metrics:
                # Generate realistic usage based on tenant plan
                if tenant.plan == "enterprise":
                    base_usage = {"api_calls": 50000, "ai_requests": 5000, "storage_gb": 100, "users_active": 50, "projects_created": 3}
                elif tenant.plan == "professional":
                    base_usage = {"api_calls": 15000, "ai_requests": 1500, "storage_gb": 5, "users_active": 8, "projects_created": 1}
                else:
                    base_usage = {"api_calls": 3000, "ai_requests": 300, "storage_gb": 0.5, "users_active": 2, "projects_created": 0.2}
                
                # Add some randomness
                base_value = base_usage.get(metric, 100)
                quantity = max(0, base_value * (0.8 + random.random() * 0.4))  # ±20% variation
                
                usage_record = UsageRecord(
                    tenant_id=tenant.id,
                    metric_name=metric,
                    quantity=Decimal(str(round(quantity, 2))),
                    timestamp=date,
                    metadata={
                        "source": "demo_data",
                        "tenant_plan": tenant.plan
                    }
                )
                db.add(usage_record)
                created_records += 1
    
    db.commit()
    print(f"   ✅ Created {created_records} usage records across all tenants")

def create_demo_ai_tasks(db, tenants, users):
    """Create demo AI development tasks"""
    print("🤖 Creating demo AI development tasks...")
    
    demo_tasks = [
        {
            "tenant": tenants[0],  # Acme Corp
            "user": users[0],      # admin
            "title": "User Authentication API Endpoints",
            "description": "Create comprehensive authentication system with JWT tokens, password reset, and session management for our enterprise application.",
            "priority": TaskPriority.HIGH,
            "status": TaskStatus.COMPLETED,
            "requirements": {
                "features": ["jwt_auth", "password_reset", "session_management", "mfa_support"],
                "security": ["bcrypt_hashing", "rate_limiting", "input_validation"],
                "performance": "sub_200ms_response"
            }
        },
        {
            "tenant": tenants[0],  # Acme Corp
            "user": users[1],      # developer
            "title": "Real-time Analytics Dashboard",
            "description": "Build a real-time analytics dashboard with WebSocket connections for live data updates and interactive charts.",
            "priority": TaskPriority.MEDIUM,
            "status": TaskStatus.IN_PROGRESS,
            "requirements": {
                "features": ["websocket_connections", "real_time_updates", "interactive_charts"],
                "technologies": ["fastapi", "websockets", "chart.js"],
                "performance": "handle_1000_concurrent_users"
            }
        },
        {
            "tenant": tenants[1],  # TechStart
            "user": users[2],      # user
            "title": "Payment Processing Integration",
            "description": "Integrate Stripe payment processing with subscription management, webhook handling, and invoice generation.",
            "priority": TaskPriority.HIGH,
            "status": TaskStatus.PENDING,
            "requirements": {
                "integrations": ["stripe_api", "webhook_handling", "invoice_generation"],
                "compliance": ["pci_compliance", "gdpr_compliance"],
                "features": ["subscription_management", "payment_retry_logic"]
            }
        },
        {
            "tenant": tenants[2],  # Global Enterprises
            "user": users[3],      # admin
            "title": "Enterprise SSO Integration",
            "description": "Implement enterprise single sign-on with SAML 2.0 support, Active Directory integration, and multi-factor authentication.",
            "priority": TaskPriority.URGENT,
            "status": TaskStatus.COMPLETED,
            "requirements": {
                "protocols": ["saml_2.0", "active_directory", "mfa"],
                "security": ["enterprise_grade", "audit_logging", "session_management"],
                "compliance": ["soc2", "iso27001"]
            }
        }
    ]
    
    created_tasks = []
    for task_data in demo_tasks:
        task = DevelopmentTask(
            tenant_id=task_data["tenant"].id,
            user_id=task_data["user"].id,
            title=task_data["title"],
            description=task_data["description"],
            priority=task_data["priority"],
            status=task_data["status"],
            requirements=task_data["requirements"],
            estimated_hours=random.randint(4, 16),
            progress_percentage=100 if task_data["status"] == TaskStatus.COMPLETED else random.randint(0, 80)
        )
        
        if task_data["status"] == TaskStatus.COMPLETED:
            task.completed_at = datetime.utcnow() - timedelta(days=random.randint(1, 10))
            # Add sample generated code for completed tasks
            task.code_generated = f'# Generated code for: {task_data["title"]}\n# This is demo code showing AI capabilities\n\nfrom fastapi import FastAPI, HTTPException\nfrom pydantic import BaseModel\n\nclass {task_data["title"].replace(" ", "")}API:\n    def __init__(self):\n        self.app = FastAPI()\n        self.setup_routes()\n    \n    def setup_routes(self):\n        # Demo implementation\n        pass'
            task.tests_generated = f'# Generated tests for: {task_data["title"]}\nimport pytest\nfrom fastapi.testclient import TestClient\n\ndef test_{task_data["title"].lower().replace(" ", "_")}():\n    # Demo test implementation\n    assert True'
        
        db.add(task)
        created_tasks.append(task)
        print(f"   ✅ Created task: {task_data['title']} ({task_data['status'].value})")
    
    db.commit()
    return created_tasks

def create_demo_ai_agents(db, tenants):
    """Create demo AI agents for each tenant"""
    print("🧠 Creating demo AI agents...")
    
    created_agents = []
    for tenant in tenants:
        agent = AIAgent(
            id=f"l3-agent-{tenant.subdomain}-{str(uuid.uuid4())[:8]}",
            tenant_id=tenant.id,
            name=f"L3 Coding Agent - {tenant.organization_name}",
            agent_type="l3_coder",
            model_config={
                "model_name": "phi-3-mini",
                "temperature": 0.1,
                "max_tokens": 4000,
                "specialized_for": ["python", "fastapi", "react", "typescript"]
            },
            capabilities=[
                "code_generation",
                "test_creation", 
                "documentation",
                "debugging",
                "refactoring",
                "architecture_design"
            ],
            performance_metrics={
                "tasks_completed": random.randint(15, 50),
                "average_completion_time_hours": round(random.uniform(2.5, 6.0), 1),
                "success_rate": round(random.uniform(0.85, 0.95), 2),
                "code_quality_score": round(random.uniform(8.5, 9.5), 1)
            }
        )
        db.add(agent)
        created_agents.append(agent)
        print(f"   ✅ Created AI agent: {agent.name}")
    
    db.commit()
    return created_agents

def create_demo_sso_providers(db, tenants):
    """Create demo SSO provider configurations"""
    print("🔐 Creating demo SSO providers...")
    
    # Only create SSO for enterprise tenants
    enterprise_tenants = [t for t in tenants if t.plan == "enterprise"]
    
    sso_providers = [
        {
            "provider_type": "google",
            "provider_name": "Google Workspace",
            "client_id": "demo_google_client_id",
            "settings": {
                "domain": "acme-corp.com",
                "auto_provision": True,
                "default_role": "user"
            }
        },
        {
            "provider_type": "microsoft", 
            "provider_name": "Microsoft Azure AD",
            "client_id": "demo_microsoft_client_id",
            "settings": {
                "tenant_id": "demo_azure_tenant_id",
                "auto_provision": True,
                "group_mapping": {
                    "LeanVibe Admins": "admin",
                    "LeanVibe Users": "user"
                }
            }
        },
        {
            "provider_type": "okta",
            "provider_name": "Okta Enterprise",
            "client_id": "demo_okta_client_id",
            "settings": {
                "okta_domain": "demo-company.okta.com",
                "auto_provision": True,
                "mfa_required": True
            }
        }
    ]
    
    created_providers = []
    for tenant in enterprise_tenants:
        for provider_data in sso_providers:
            provider = SSOProvider(
                tenant_id=tenant.id,
                provider_type=provider_data["provider_type"],
                provider_name=provider_data["provider_name"],
                client_id=provider_data["client_id"],
                client_secret="demo_client_secret_encrypted",
                settings=provider_data["settings"]
            )
            db.add(provider)
            created_providers.append(provider)
            print(f"   ✅ Created SSO provider: {provider_data['provider_name']} for {tenant.organization_name}")
    
    db.commit()
    return created_providers

def setup_enterprise_demo_data():
    """Main function to set up complete enterprise demo environment"""
    print("🚀 Setting up LeanVibe Enterprise Demo Environment...")
    print("=" * 60)
    
    try:
        # Get database session
        db = get_database_session()
        
        # Create all demo data
        tenants = create_demo_tenants(db)
        users = create_demo_users(db, tenants)
        plans = create_subscription_plans(db)
        subscriptions = create_demo_subscriptions(db, tenants, plans)
        create_demo_usage_records(db, tenants)
        tasks = create_demo_ai_tasks(db, tenants, users)
        agents = create_demo_ai_agents(db, tenants)
        sso_providers = create_demo_sso_providers(db, tenants)
        
        db.close()
        
        print("=" * 60)
        print("🎉 Enterprise Demo Environment Setup Complete!")
        print("")
        print("📊 Demo Summary:")
        print(f"   • {len(tenants)} Enterprise Tenants")
        print(f"   • {len(users)} Demo Users")
        print(f"   • {len(plans)} Subscription Plans") 
        print(f"   • {len(subscriptions)} Active Subscriptions")
        print(f"   • {len(tasks)} AI Development Tasks")
        print(f"   • {len(agents)} AI Coding Agents")
        print(f"   • {len(sso_providers)} SSO Provider Configurations")
        print("")
        print("🔗 Access Your Demo:")
        print("   Web: http://localhost:8000")
        print("   API: http://localhost:8000/docs")
        print("   Health: http://localhost:8000/health/enterprise")
        print("")
        print("🔑 Demo Login Credentials:")
        print("   admin@acme-corp.com / enterprise_demo")
        print("   user@techstart.com / professional_demo") 
        print("   enterprise@global.com / custom_demo")
        
    except Exception as e:
        print(f"❌ Error setting up demo environment: {e}")
        print("⚠️  Some demo features may not be available")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    setup_enterprise_demo_data()