"""
Authentication test fixtures for comprehensive testing
Provides test data, mocks, and utilities for authentication testing
"""

import asyncio
import bcrypt
import secrets
from datetime import datetime, timedelta
from typing import AsyncGenerator, Dict, List, Optional
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.models.auth_models import (
    User, UserCreate, UserUpdate, UserSession, LoginRequest, LoginResponse,
    AuthProvider, UserStatus, UserRole, MFAMethod, SessionStatus
)
from app.models.orm_models import UserORM, UserSessionORM, TenantORM, AuthAuditLogORM
from app.services.auth_service import AuthenticationService
from app.core.database import Base


# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_auth.db"


# Removed custom event_loop fixture to avoid deprecation warnings
# pytest-asyncio will provide the default event loop


@pytest_asyncio.fixture(scope="function")
async def test_db() -> AsyncSession:
    """Create a test database session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def auth_service(test_db: AsyncSession) -> AuthenticationService:
    """Create an authentication service with test database."""
    return AuthenticationService(db=test_db)


# Tenant fixtures
@pytest_asyncio.fixture
async def test_tenant(test_db: AsyncSession) -> TenantORM:
    """Create a test tenant."""
    from app.models.tenant_models import TenantStatus, TenantPlan, TenantType
    tenant = TenantORM(
        id=uuid4(),
        tenant_type=TenantType.ENTERPRISE,
        organization_name="Test Organization",
        slug="test-org",
        admin_email="admin@test-org.com",
        status=TenantStatus.ACTIVE,
        plan=TenantPlan.ENTERPRISE
    )
    test_db.add(tenant)
    await test_db.commit()
    await test_db.refresh(tenant)
    return tenant


@pytest_asyncio.fixture
async def secondary_tenant(test_db: AsyncSession) -> TenantORM:
    """Create a secondary test tenant for isolation testing."""
    from app.models.tenant_models import TenantStatus, TenantPlan, TenantType
    tenant = TenantORM(
        id=uuid4(),
        tenant_type=TenantType.ENTERPRISE,
        organization_name="Secondary Organization",
        slug="secondary-org",
        admin_email="admin@secondary-org.com",
        status=TenantStatus.ACTIVE,
        plan=TenantPlan.TEAM
    )
    test_db.add(tenant)
    await test_db.commit()
    await test_db.refresh(tenant)
    return tenant


# User fixtures
@pytest.fixture
def valid_user_data(test_tenant: TenantORM) -> UserCreate:
    """Valid user creation data."""
    return UserCreate(
        tenant_id=test_tenant.id,
        email="testuser@example.com",
        first_name="Test",
        last_name="User",
        password="SecurePassword123!",
        role=UserRole.DEVELOPER,
        auth_provider=AuthProvider.LOCAL,
        send_invitation=False
    )


@pytest.fixture
def admin_user_data(test_tenant: TenantORM) -> UserCreate:
    """Admin user creation data."""
    return UserCreate(
        tenant_id=test_tenant.id,
        email="admin@example.com",
        first_name="Admin",
        last_name="User",
        password="AdminPassword123!",
        role=UserRole.ADMIN,
        auth_provider=AuthProvider.LOCAL,
        send_invitation=False
    )


@pytest.fixture
def sso_user_data(test_tenant: TenantORM) -> UserCreate:
    """SSO user creation data."""
    return UserCreate(
        tenant_id=test_tenant.id,
        email="sso.user@example.com",
        first_name="SSO",
        last_name="User",
        role=UserRole.DEVELOPER,
        auth_provider=AuthProvider.GOOGLE,
        send_invitation=False
    )


@pytest_asyncio.fixture
async def test_user(auth_service: AuthenticationService, valid_user_data: UserCreate) -> User:
    """Create a test user in the database."""
    user = await auth_service.create_user(valid_user_data)
    # Activate the user for testing
    test_db = await auth_service._get_db()
    await test_db.execute(
        UserORM.__table__.update()
        .where(UserORM.id == user.id)
        .values(status=UserStatus.ACTIVE)
    )
    await test_db.commit()
    user.status = UserStatus.ACTIVE
    return user


@pytest_asyncio.fixture
async def admin_user(auth_service: AuthenticationService, admin_user_data: UserCreate) -> User:
    """Create an admin test user."""
    user = await auth_service.create_user(admin_user_data)
    # Activate the user for testing
    test_db = await auth_service._get_db()
    await test_db.execute(
        UserORM.__table__.update()
        .where(UserORM.id == user.id)
        .values(status=UserStatus.ACTIVE)
    )
    await test_db.commit()
    user.status = UserStatus.ACTIVE
    return user


@pytest_asyncio.fixture
async def mfa_enabled_user(auth_service: AuthenticationService, valid_user_data: UserCreate) -> User:
    """Create a user with MFA enabled."""
    user_data = valid_user_data.copy()
    user_data.email = "mfa.user@example.com"
    user = await auth_service.create_user(user_data)
    
    # Enable MFA for the user
    test_db = await auth_service._get_db()
    await test_db.execute(
        UserORM.__table__.update()
        .where(UserORM.id == user.id)
        .values(
            status=UserStatus.ACTIVE,
            mfa_enabled=True,
            mfa_methods=["totp"],
            mfa_secret="JBSWY3DPEHPK3PXP"  # Test TOTP secret
        )
    )
    await test_db.commit()
    user.status = UserStatus.ACTIVE
    user.mfa_enabled = True
    user.mfa_methods = [MFAMethod.TOTP]
    user.mfa_secret = "JBSWY3DPEHPK3PXP"
    return user


@pytest_asyncio.fixture
async def locked_user(auth_service: AuthenticationService, valid_user_data: UserCreate) -> User:
    """Create a locked user for testing lockout scenarios."""
    user_data = valid_user_data.copy()
    user_data.email = "locked.user@example.com"
    user = await auth_service.create_user(user_data)
    
    # Lock the user
    test_db = await auth_service._get_db()
    locked_until = datetime.utcnow() + timedelta(minutes=30)
    await test_db.execute(
        UserORM.__table__.update()
        .where(UserORM.id == user.id)
        .values(
            status=UserStatus.ACTIVE,
            login_attempts=5,
            locked_until=locked_until
        )
    )
    await test_db.commit()
    user.status = UserStatus.ACTIVE
    user.login_attempts = 5
    user.locked_until = locked_until
    return user


@pytest_asyncio.fixture
async def cross_tenant_user(auth_service: AuthenticationService, secondary_tenant: TenantORM) -> User:
    """Create a user in secondary tenant for isolation testing."""
    user_data = UserCreate(
        tenant_id=secondary_tenant.id,
        email="crosstenant@example.com",
        first_name="Cross",
        last_name="Tenant",
        password="CrossTenantPass123!",
        role=UserRole.DEVELOPER,
        auth_provider=AuthProvider.LOCAL
    )
    user = await auth_service.create_user(user_data)
    
    # Activate the user
    test_db = await auth_service._get_db()
    await test_db.execute(
        UserORM.__table__.update()
        .where(UserORM.id == user.id)
        .values(status=UserStatus.ACTIVE)
    )
    await test_db.commit()
    user.status = UserStatus.ACTIVE
    return user


# Login request fixtures
@pytest.fixture
def valid_login_request(test_user: User) -> LoginRequest:
    """Valid login request."""
    return LoginRequest(
        email=test_user.email,
        password="SecurePassword123!",
        provider=AuthProvider.LOCAL,
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0 Test Browser"
    )


@pytest.fixture
def invalid_login_request(test_user: User) -> LoginRequest:
    """Invalid login request with wrong password."""
    return LoginRequest(
        email=test_user.email,
        password="WrongPassword",
        provider=AuthProvider.LOCAL,
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0 Test Browser"
    )


@pytest.fixture
def mfa_login_request(mfa_enabled_user: User) -> LoginRequest:
    """Login request for MFA-enabled user."""
    return LoginRequest(
        email=mfa_enabled_user.email,
        password="SecurePassword123!",
        provider=AuthProvider.LOCAL,
        mfa_code="123456",  # Test TOTP code
        mfa_method=MFAMethod.TOTP,
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0 Test Browser"
    )


@pytest.fixture
def oauth_login_request() -> LoginRequest:
    """OAuth login request."""
    return LoginRequest(
        email="oauth.user@example.com",
        provider=AuthProvider.GOOGLE,
        auth_code="oauth_auth_code_123",
        state="oauth_state_123",
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0 Test Browser"
    )


@pytest.fixture
def saml_login_request() -> LoginRequest:
    """SAML login request."""
    return LoginRequest(
        email="saml.user@example.com",
        provider=AuthProvider.SAML,
        saml_response="encoded_saml_response",
        relay_state="saml_relay_state",
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0 Test Browser"
    )


# Session fixtures
@pytest_asyncio.fixture
async def user_session(auth_service: AuthenticationService, test_user: User, valid_login_request: LoginRequest) -> UserSession:
    """Create a user session."""
    return await auth_service._create_user_session(test_user, valid_login_request)


@pytest_asyncio.fixture
async def expired_session(test_db: AsyncSession, test_user: User) -> UserSession:
    """Create an expired session."""
    session_orm = UserSessionORM(
        user_id=test_user.id,
        tenant_id=test_user.tenant_id,
        expires_at=datetime.utcnow() - timedelta(hours=1),  # Expired
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0 Test Browser",
        auth_method=AuthProvider.LOCAL,
        access_token_hash="expired_token_hash",
        status=SessionStatus.EXPIRED
    )
    test_db.add(session_orm)
    await test_db.commit()
    await test_db.refresh(session_orm)
    return session_orm


# Token fixtures
@pytest_asyncio.fixture
async def valid_jwt_tokens(auth_service: AuthenticationService, test_user: User, user_session: UserSession) -> Dict[str, str]:
    """Generate valid JWT tokens."""
    return await auth_service._generate_tokens(test_user, user_session)


@pytest.fixture
def expired_jwt_token() -> str:
    """Expired JWT token for testing."""
    import jwt
    from datetime import datetime, timedelta
    
    payload = {
        "user_id": str(uuid4()),
        "tenant_id": str(uuid4()),
        "exp": (datetime.utcnow() - timedelta(hours=1)).timestamp(),
        "type": "access"
    }
    return jwt.encode(payload, "test_secret", algorithm="HS256")


@pytest.fixture
def malformed_jwt_token() -> str:
    """Malformed JWT token for testing."""
    return "malformed.jwt.token"


# Password test data
@pytest.fixture
def weak_passwords() -> List[str]:
    """List of weak passwords for testing."""
    return [
        "123456",
        "password",
        "qwerty",
        "abc123",
        "letmein",
        "monkey",
        "1234567890",
        "dragon",
        "sunshine",
        "princess"
    ]


@pytest.fixture
def strong_passwords() -> List[str]:
    """List of strong passwords for testing."""
    return [
        "MyStr0ngP@ssw0rd!",
        "C0mpl3x!P@ssw0rd123",
        "S3cur3#P@ssw0rd$2023",
        "Ungu3ss@bl3!P@ss789",
        "R@nd0m&Str0ng#P@ss456"
    ]


# Attack simulation fixtures
@pytest.fixture
def sql_injection_payloads() -> List[str]:
    """SQL injection payloads for security testing."""
    return [
        "'; DROP TABLE users; --",
        "' OR '1'='1",
        "admin'--",
        "' OR 1=1--",
        "'; INSERT INTO users VALUES ('hacker', 'password'); --"
    ]


@pytest.fixture
def xss_payloads() -> List[str]:
    """XSS payloads for security testing."""
    return [
        "<script>alert('XSS')</script>",
        "javascript:alert('XSS')",
        "<img src=x onerror=alert('XSS')>",
        "<svg onload=alert('XSS')>",
        "'><script>alert('XSS')</script>"
    ]


# Rate limiting test fixtures
@pytest.fixture
def rate_limit_requests() -> List[Dict]:
    """Generate multiple requests for rate limiting tests."""
    return [
        {"email": f"user{i}@example.com", "password": "password123"}
        for i in range(50)  # Simulate 50 rapid requests
    ]


# Performance test fixtures
@pytest.fixture
def concurrent_users_data() -> List[UserCreate]:
    """Generate data for concurrent user testing."""
    return [
        UserCreate(
            tenant_id=uuid4(),
            email=f"loadtest{i}@example.com",
            first_name=f"Load{i}",
            last_name="Test",
            password="LoadTestPassword123!",
            role=UserRole.DEVELOPER
        )
        for i in range(100)
    ]


# Mock external service responses
@pytest.fixture
def mock_oauth_responses() -> Dict[str, Dict]:
    """Mock OAuth provider responses."""
    return {
        "google": {
            "access_token": "ya29.mock_google_token",
            "user_info": {
                "id": "google_123456789",
                "email": "user@gmail.com",
                "given_name": "Test",
                "family_name": "User",
                "name": "Test User",
                "picture": "https://example.com/photo.jpg"
            }
        },
        "microsoft": {
            "access_token": "EwAoA8l6BAAU_mock_ms_token",
            "user_info": {
                "id": "microsoft_987654321",
                "mail": "user@outlook.com",
                "givenName": "Test",
                "surname": "User",
                "displayName": "Test User"
            }
        }
    }


@pytest.fixture
def mock_saml_response() -> str:
    """Mock SAML response."""
    return """
    <samlp:Response xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
                    ID="response_id" Version="2.0"
                    IssueInstant="2023-01-01T00:00:00Z">
        <saml:Assertion xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion">
            <saml:Subject>
                <saml:NameID Format="urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress">
                    saml.user@example.com
                </saml:NameID>
            </saml:Subject>
            <saml:AttributeStatement>
                <saml:Attribute Name="email">
                    <saml:AttributeValue>saml.user@example.com</saml:AttributeValue>
                </saml:Attribute>
                <saml:Attribute Name="firstName">
                    <saml:AttributeValue>SAML</saml:AttributeValue>
                </saml:Attribute>
                <saml:Attribute Name="lastName">
                    <saml:AttributeValue>User</saml:AttributeValue>
                </saml:Attribute>
            </saml:AttributeStatement>
        </saml:Assertion>
    </samlp:Response>
    """


# Audit log test fixtures
@pytest.fixture
def audit_log_events() -> List[Dict]:
    """Sample audit log events for testing."""
    return [
        {
            "event_type": "user_login",
            "description": "User logged in successfully",
            "success": True,
            "ip_address": "192.168.1.100"
        },
        {
            "event_type": "user_login_failed",
            "description": "User login failed - invalid password",
            "success": False,
            "ip_address": "192.168.1.101"
        },
        {
            "event_type": "mfa_setup",
            "description": "User enabled MFA",
            "success": True,
            "ip_address": "192.168.1.100"
        }
    ]


# Test client fixtures
@pytest.fixture
def auth_test_client() -> TestClient:
    """Create a test client specifically for authentication testing."""
    from app.main import app
    return TestClient(app)


@pytest.fixture
def authenticated_headers(valid_jwt_tokens: Dict[str, str]) -> Dict[str, str]:
    """Headers with valid authentication token."""
    return {
        "Authorization": f"Bearer {valid_jwt_tokens['access_token']}",
        "Content-Type": "application/json"
    }


@pytest.fixture
def expired_auth_headers(expired_jwt_token: str) -> Dict[str, str]:
    """Headers with expired authentication token."""
    return {
        "Authorization": f"Bearer {expired_jwt_token}",
        "Content-Type": "application/json"
    }


# Utility functions for tests
def hash_password(password: str) -> str:
    """Hash a password for testing."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def generate_totp_code(secret: str = "JBSWY3DPEHPK3PXP") -> str:
    """Generate a valid TOTP code for testing."""
    import pyotp
    totp = pyotp.TOTP(secret)
    return totp.now()


def generate_test_email() -> str:
    """Generate a unique test email."""
    return f"test_{secrets.token_hex(8)}@example.com"


def generate_secure_token() -> str:
    """Generate a secure token for testing."""
    return secrets.token_urlsafe(32)