"""
Enterprise authentication service for LeanVibe SaaS Platform
Handles SSO, SAML, MFA, RBAC, and session management
"""

import hashlib
import logging
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from uuid import UUID

import bcrypt
import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_

from ..models.auth_models import (
    User, UserCreate, UserUpdate, UserSession, LoginRequest, LoginResponse,
    SSOConfiguration, MFASetupRequest, MFASetupResponse, PasswordPolicy, AuditLog,
    AuthProvider, UserStatus, UserRole, SessionStatus, MFAMethod,
    DEFAULT_PASSWORD_POLICY
)
from ..models.tenant_models import Tenant
from ..core.database import get_database_session
from ..core.exceptions import (
    InvalidCredentialsError, TokenExpiredError, InsufficientPermissionsError,
    ResourceNotFoundError, SSOConfigurationError
)
from ..config.settings import settings

logger = logging.getLogger(__name__)


class AuthenticationService:
    """Enterprise authentication service"""
    
    def __init__(self, db: AsyncSession = None):
        self.db = db
        self.jwt_secret = settings.secret_key
        self.token_expiry = 3600  # 1 hour
        self.refresh_expiry = 86400 * 30  # 30 days
    
    async def _get_db(self) -> AsyncSession:
        """Get database session"""
        if self.db:
            return self.db
        return await get_database_session()
    
    async def create_user(self, user_data: UserCreate, created_by: UUID = None) -> User:
        """Create a new user with proper password hashing"""
        db = await self._get_db()
        
        try:
            # Check if user already exists in tenant
            existing = await self.get_user_by_email(user_data.email, user_data.tenant_id)
            if existing:
                raise ValueError(f"User with email {user_data.email} already exists in tenant")
            
            # Hash password if provided
            password_hash = None
            if user_data.password and user_data.auth_provider == AuthProvider.LOCAL:
                password_hash = self._hash_password(user_data.password)
            
            # Create user instance
            user = User(
                tenant_id=user_data.tenant_id,
                email=user_data.email,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                role=user_data.role,
                auth_provider=user_data.auth_provider,
                password_hash=password_hash,
                status=UserStatus.PENDING_ACTIVATION if user_data.send_invitation else UserStatus.ACTIVE
            )
            
            # Save to database
            db.add(user)
            await db.commit()
            await db.refresh(user)
            
            # Log user creation
            await self._log_auth_event(
                user.tenant_id,
                "user_created",
                f"User {user.email} created by {created_by}",
                True,
                user_id=user.id,
                user_email=user.email,
                metadata={"created_by": str(created_by) if created_by else None}
            )
            
            logger.info(f"Created user: {user.email} in tenant {user.tenant_id}")
            return user
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to create user: {e}")
            raise
    
    async def get_user_by_id(self, user_id: UUID, tenant_id: UUID = None) -> Optional[User]:
        """Get user by ID with optional tenant validation"""
        db = await self._get_db()
        
        query = select(User).where(User.id == user_id)
        if tenant_id:
            query = query.where(User.tenant_id == tenant_id)
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_user_by_email(self, email: str, tenant_id: UUID) -> Optional[User]:
        """Get user by email within tenant"""
        db = await self._get_db()
        
        result = await db.execute(
            select(User).where(
                and_(
                    User.email == email.lower(),
                    User.tenant_id == tenant_id
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def authenticate_user(self, login_request: LoginRequest, tenant_id: UUID) -> LoginResponse:
        """Authenticate user with various providers"""
        try:
            # Get user by email
            user = await self.get_user_by_email(login_request.email, tenant_id)
            
            if not user:
                await self._log_auth_event(
                    tenant_id,
                    "login_failed",
                    f"User not found: {login_request.email}",
                    False,
                    user_email=login_request.email,
                    metadata={"reason": "user_not_found"}
                )
                raise InvalidCredentialsError("Invalid credentials")
            
            # Check user status
            if user.status != UserStatus.ACTIVE:
                await self._log_auth_event(
                    tenant_id,
                    "login_failed",
                    f"Inactive user login attempt: {user.email}",
                    False,
                    user_id=user.id,
                    user_email=user.email,
                    metadata={"reason": "user_inactive", "status": user.status}
                )
                raise InvalidCredentialsError("Account is not active")
            
            # Check account lockout
            if user.locked_until and user.locked_until > datetime.utcnow():
                await self._log_auth_event(
                    tenant_id,
                    "login_failed",
                    f"Locked account login attempt: {user.email}",
                    False,
                    user_id=user.id,
                    user_email=user.email,
                    metadata={"reason": "account_locked", "locked_until": user.locked_until.isoformat()}
                )
                raise InvalidCredentialsError("Account is temporarily locked")
            
            # Authenticate based on provider
            auth_success = False
            
            if login_request.provider == AuthProvider.LOCAL:
                auth_success = await self._authenticate_local(user, login_request.password)
            elif login_request.provider in [AuthProvider.GOOGLE, AuthProvider.MICROSOFT, AuthProvider.OKTA]:
                auth_success = await self._authenticate_oauth(user, login_request)
            elif login_request.provider == AuthProvider.SAML:
                auth_success = await self._authenticate_saml(user, login_request)
            
            if not auth_success:
                # Increment failed login attempts
                await self._handle_failed_login(user)
                raise InvalidCredentialsError("Invalid credentials")
            
            # Check MFA requirement
            if user.mfa_enabled and not login_request.mfa_code:
                return LoginResponse(
                    success=False,
                    mfa_required=True,
                    mfa_methods=user.mfa_methods,
                    mfa_challenge_id=str(user.id)  # Simplified - would use separate challenge ID
                )
            
            # Verify MFA if provided
            if user.mfa_enabled and login_request.mfa_code:
                mfa_success = await self._verify_mfa(user, login_request.mfa_code, login_request.mfa_method)
                if not mfa_success:
                    await self._log_auth_event(
                        tenant_id,
                        "mfa_failed",
                        f"MFA verification failed: {user.email}",
                        False,
                        user_id=user.id,
                        user_email=user.email,
                        metadata={"mfa_method": login_request.mfa_method}
                    )
                    raise InvalidCredentialsError("Invalid MFA code")
            
            # Create session and tokens
            session = await self._create_user_session(user, login_request)
            tokens = await self._generate_tokens(user, session)
            
            # Reset failed login attempts
            await self._reset_failed_login_attempts(user)
            
            # Log successful login
            await self._log_auth_event(
                tenant_id,
                "login_success",
                f"Successful login: {user.email}",
                True,
                user_id=user.id,
                user_email=user.email,
                ip_address=login_request.ip_address,
                metadata={
                    "provider": login_request.provider,
                    "mfa_verified": user.mfa_enabled,
                    "session_id": str(session.id)
                }
            )
            
            return LoginResponse(
                success=True,
                access_token=tokens["access_token"],
                refresh_token=tokens["refresh_token"],
                expires_in=self.token_expiry,
                user=user
            )
            
        except Exception as e:
            logger.error(f"Authentication failed for {login_request.email}: {e}")
            raise
    
    async def _authenticate_local(self, user: User, password: str) -> bool:
        """Authenticate with local password"""
        if not user.password_hash or not password:
            return False
        
        return bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8'))
    
    async def _authenticate_oauth(self, user: User, login_request: LoginRequest) -> bool:
        """Authenticate with OAuth provider"""
        # This would integrate with OAuth providers
        # For now, mock implementation
        if login_request.auth_code:
            # Verify auth code with provider
            # Exchange for user info
            # Validate user identity
            return True
        return False
    
    async def _authenticate_saml(self, user: User, login_request: LoginRequest) -> bool:
        """Authenticate with SAML provider"""
        # This would validate SAML response
        # For now, mock implementation
        if login_request.saml_response:
            # Validate SAML response signature
            # Extract user attributes
            # Validate assertion
            return True
        return False
    
    async def _verify_mfa(self, user: User, code: str, method: MFAMethod) -> bool:
        """Verify MFA code"""
        if method == MFAMethod.TOTP and user.mfa_secret:
            # Verify TOTP code
            import pyotp
            totp = pyotp.TOTP(user.mfa_secret)
            return totp.verify(code, valid_window=1)
        
        elif method == MFAMethod.SMS:
            # Verify SMS code (would integrate with SMS provider)
            return True  # Mock implementation
        
        elif method == MFAMethod.EMAIL:
            # Verify email code
            return True  # Mock implementation
        
        return False
    
    async def _create_user_session(self, user: User, login_request: LoginRequest) -> UserSession:
        """Create user session"""
        db = await self._get_db()
        
        # Calculate session expiry
        expires_at = datetime.utcnow() + timedelta(
            days=30 if login_request.remember_me else 1
        )
        
        # Generate session tokens
        access_token = secrets.token_urlsafe(32)
        refresh_token = secrets.token_urlsafe(32)
        
        session = UserSession(
            user_id=user.id,
            tenant_id=user.tenant_id,
            expires_at=expires_at,
            ip_address=login_request.ip_address,
            user_agent=login_request.user_agent,
            auth_method=login_request.provider,
            mfa_verified=user.mfa_enabled,
            access_token_hash=self._hash_token(access_token),
            refresh_token_hash=self._hash_token(refresh_token) if refresh_token else None
        )
        
        db.add(session)
        await db.commit()
        await db.refresh(session)
        
        return session
    
    async def _generate_tokens(self, user: User, session: UserSession) -> Dict[str, str]:
        """Generate JWT tokens"""
        now = datetime.utcnow()
        
        # Access token payload
        access_payload = {
            "user_id": str(user.id),
            "tenant_id": str(user.tenant_id),
            "email": user.email,
            "role": user.role,
            "permissions": user.permissions,
            "session_id": str(session.id),
            "iat": now.timestamp(),
            "exp": (now + timedelta(seconds=self.token_expiry)).timestamp(),
            "type": "access"
        }
        
        # Refresh token payload
        refresh_payload = {
            "user_id": str(user.id),
            "session_id": str(session.id),
            "iat": now.timestamp(),
            "exp": (now + timedelta(seconds=self.refresh_expiry)).timestamp(),
            "type": "refresh"
        }
        
        access_token = jwt.encode(access_payload, self.jwt_secret, algorithm="HS256")
        refresh_token = jwt.encode(refresh_payload, self.jwt_secret, algorithm="HS256")
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token
        }
    
    async def verify_token(self, token: str) -> Dict:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            
            # Check token expiry
            if payload.get("exp", 0) < datetime.utcnow().timestamp():
                raise TokenExpiredError()
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError()
        except jwt.InvalidTokenError:
            raise InvalidCredentialsError("Invalid token")
    
    async def refresh_token(self, refresh_token: str) -> Dict[str, str]:
        """Refresh access token using refresh token"""
        try:
            payload = await self.verify_token(refresh_token)
            
            if payload.get("type") != "refresh":
                raise InvalidCredentialsError("Invalid refresh token")
            
            # Get user and session
            user = await self.get_user_by_id(UUID(payload["user_id"]))
            if not user:
                raise InvalidCredentialsError("User not found")
            
            # Verify session is still active
            session = await self._get_session_by_id(UUID(payload["session_id"]))
            if not session or session.status != SessionStatus.ACTIVE:
                raise InvalidCredentialsError("Session expired")
            
            # Generate new tokens
            new_tokens = await self._generate_tokens(user, session)
            
            return new_tokens
            
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            raise
    
    async def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    async def _hash_token(self, token: str) -> str:
        """Hash token for storage"""
        return hashlib.sha256(token.encode()).hexdigest()
    
    async def _handle_failed_login(self, user: User):
        """Handle failed login attempt"""
        db = await self._get_db()
        
        user.login_attempts += 1
        
        # Get password policy
        policy = await self._get_password_policy(user.tenant_id)
        
        # Lock account if too many attempts
        if user.login_attempts >= policy.lockout_attempts:
            user.locked_until = datetime.utcnow() + timedelta(
                minutes=policy.lockout_duration_minutes
            )
            logger.warning(f"User {user.email} locked due to failed login attempts")
        
        await db.commit()
    
    async def _reset_failed_login_attempts(self, user: User):
        """Reset failed login attempts after successful login"""
        db = await self._get_db()
        
        user.login_attempts = 0
        user.locked_until = None
        user.last_login_at = datetime.utcnow()
        
        await db.commit()
    
    async def _get_password_policy(self, tenant_id: UUID) -> PasswordPolicy:
        """Get password policy for tenant"""
        # This would query the database for tenant-specific policy
        # For now, return default policy
        policy = DEFAULT_PASSWORD_POLICY.copy()
        policy.tenant_id = tenant_id
        return policy
    
    async def _get_session_by_id(self, session_id: UUID) -> Optional[UserSession]:
        """Get session by ID"""
        db = await self._get_db()
        
        result = await db.execute(
            select(UserSession).where(UserSession.id == session_id)
        )
        return result.scalar_one_or_none()
    
    async def _log_auth_event(
        self,
        tenant_id: UUID,
        event_type: str,
        description: str,
        success: bool,
        user_id: UUID = None,
        user_email: str = None,
        ip_address: str = None,
        metadata: Dict = None
    ):
        """Log authentication event"""
        db = await self._get_db()
        
        audit_log = AuditLog(
            tenant_id=tenant_id,
            event_type=event_type,
            event_description=description,
            success=success,
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            metadata=metadata or {}
        )
        
        db.add(audit_log)
        await db.commit()
        
        logger.info(f"Auth event logged: {event_type} - {description}")


# Create aliases for convenience
UserNotFoundError = ResourceNotFoundError


class MFARequiredError(Exception):
    """Raised when MFA verification is required"""
    pass


# Singleton service instance
auth_service = AuthenticationService()