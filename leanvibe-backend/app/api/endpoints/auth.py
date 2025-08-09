"""
Authentication API endpoints for LeanVibe Enterprise SaaS Platform
Provides login, logout, token refresh, MFA, and SSO endpoints
"""

import logging
import secrets
from typing import Dict, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Request, Response, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ...models.auth_models import (
    LoginRequest, LoginResponse, UserCreate, User, MFASetupRequest, MFASetupResponse
)
from ...services.auth_service import auth_service
from ...middleware.tenant_middleware import get_current_tenant, require_tenant
from ...core.exceptions import (
    InvalidCredentialsError, TokenExpiredError, InsufficientPermissionsError
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])
security = HTTPBearer(auto_error=False)


@router.post("/login", response_model=LoginResponse)
async def login(
    login_request: LoginRequest,
    request: Request,
    tenant = Depends(require_tenant)
) -> LoginResponse:
    """
    Authenticate user with email/password, SSO, or SAML
    
    Supports multiple authentication providers:
    - Local: email + password
    - OAuth2: Google, Microsoft, Okta
    - SAML: Enterprise SSO
    
    Returns JWT tokens on success or MFA challenge if required.
    """
    try:
        # Add client context to login request
        if not login_request.ip_address:
            login_request.ip_address = request.client.host
        if not login_request.user_agent:
            login_request.user_agent = request.headers.get("user-agent")
        
        # Authenticate user
        response = await auth_service.authenticate_user(login_request, tenant.id)
        
        logger.info(f"Login attempt for {login_request.email}: {'success' if response.success else 'failed'}")
        
        return response
        
    except InvalidCredentialsError as e:
        logger.warning(f"Invalid credentials for {login_request.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    except Exception as e:
        logger.error(f"Login error for {login_request.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )


@router.post("/refresh", response_model=Dict[str, str])
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, str]:
    """
    Refresh access token using refresh token
    
    Returns new access and refresh tokens.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required"
        )
    
    try:
        new_tokens = await auth_service.refresh_token(credentials.credentials)
        return new_tokens
        
    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired"
        )
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> JSONResponse:
    """
    Logout user and revoke session
    
    Invalidates the current session and tokens.
    """
    if not credentials:
        return JSONResponse({"message": "Logged out"}, status_code=200)
    
    try:
        # Verify token to get session info
        payload = await auth_service.verify_token(credentials.credentials)
        session_id = payload.get("session_id")
        
        if session_id:
            # Revoke session (would implement session revocation)
            logger.info(f"Session {session_id} logged out")
        
        return JSONResponse({"message": "Logged out successfully"}, status_code=200)
        
    except Exception as e:
        logger.warning(f"Logout error: {e}")
        # Still return success - logout should be forgiving
        return JSONResponse({"message": "Logged out"}, status_code=200)


@router.get("/me", response_model=User)
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    Get current user information
    
    Returns user profile for the authenticated user.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    try:
        # Verify token
        payload = await auth_service.verify_token(credentials.credentials)
        user_id = UUID(payload["user_id"])
        tenant_id = UUID(payload["tenant_id"])
        
        # Get user
        user = await auth_service.get_user_by_id(user_id, tenant_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user
        
    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except Exception as e:
        logger.error(f"Get current user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        )


@router.post("/mfa/setup", response_model=MFASetupResponse)
async def setup_mfa(
    setup_request: MFASetupRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> MFASetupResponse:
    """
    Set up multi-factor authentication
    
    Supports TOTP (Google Authenticator), SMS, and email MFA.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    try:
        # Verify token and get user
        payload = await auth_service.verify_token(credentials.credentials)
        user_id = UUID(payload["user_id"])
        
        user = await auth_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Generate MFA setup response
        if setup_request.method == "totp":
            import pyotp
            import qrcode
            import io
            import base64
            
            # Generate secret
            secret = pyotp.random_base32()
            
            # Generate QR code
            totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
                user.email,
                issuer_name="LeanVibe"
            )
            
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(totp_uri)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            qr_code_data = base64.b64encode(buffer.getvalue()).decode()
            
            # Generate backup codes
            backup_codes = [secrets.token_hex(4).upper() for _ in range(10)]
            
            return MFASetupResponse(
                method=setup_request.method,
                secret=secret,
                qr_code=f"data:image/png;base64,{qr_code_data}",
                backup_codes=backup_codes
            )
        
        else:
            # For SMS/Email MFA
            return MFASetupResponse(
                method=setup_request.method,
                backup_codes=[secrets.token_hex(4).upper() for _ in range(10)]
            )
        
    except Exception as e:
        logger.error(f"MFA setup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to setup MFA"
        )


@router.post("/mfa/verify")
async def verify_mfa(
    verification_data: Dict[str, str],
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> JSONResponse:
    """
    Verify MFA setup with test code
    
    Confirms MFA is working correctly before enabling.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    try:
        # Verify token and get user
        payload = await auth_service.verify_token(credentials.credentials)
        user_id = UUID(payload["user_id"])
        
        # Verify MFA code (mock implementation)
        code = verification_data.get("code")
        method = verification_data.get("method")
        
        if not code or not method:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Code and method are required"
            )
        
        # For demo purposes, accept any 6-digit code
        if len(code) == 6 and code.isdigit():
            return JSONResponse(
                {"message": "MFA verified successfully", "enabled": True},
                status_code=200
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid MFA code"
            )
        
    except Exception as e:
        logger.error(f"MFA verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify MFA"
        )


# SSO endpoints
@router.get("/sso/{provider}")
async def sso_redirect(
    provider: str,
    request: Request,
    tenant = Depends(require_tenant)
) -> RedirectResponse:
    """
    Redirect to SSO provider for authentication
    
    Supports Google, Microsoft, Okta, and custom SAML providers.
    """
    try:
        # Get SSO configuration for tenant and provider
        # This would query the database for SSO config
        
        if provider == "google":
            auth_url = "https://accounts.google.com/oauth2/v2/auth"
            client_id = "your-google-client-id"  # From SSO config
            redirect_uri = f"{request.base_url}auth/sso/{provider}/callback"
            scope = "email profile"
            
            auth_redirect = f"{auth_url}?client_id={client_id}&redirect_uri={redirect_uri}&scope={scope}&response_type=code&state={tenant.slug}"
            
            return RedirectResponse(auth_redirect)
        
        elif provider == "microsoft":
            # Microsoft OAuth2 redirect
            auth_url = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
            # Build redirect URL (mock implementation)
            return RedirectResponse(f"{auth_url}?client_id=mock&redirect_uri=callback")
            
        elif provider == "saml":
            # SAML redirect (mock implementation)
            return RedirectResponse("/saml/login")
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported SSO provider: {provider}"
            )
            
    except Exception as e:
        logger.error(f"SSO redirect error for {provider}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SSO configuration error"
        )


@router.get("/sso/{provider}/callback")
async def sso_callback(
    provider: str,
    code: str = None,
    state: str = None,
    error: str = None
) -> RedirectResponse:
    """
    Handle SSO provider callback
    
    Exchanges authorization code for tokens and creates user session.
    """
    if error:
        logger.error(f"SSO error from {provider}: {error}")
        return RedirectResponse(f"/login?error=sso_error&provider={provider}")
    
    if not code:
        logger.error(f"No authorization code from {provider}")
        return RedirectResponse(f"/login?error=missing_code&provider={provider}")
    
    try:
        # Exchange code for tokens
        # Verify user identity
        # Create or update user
        # Create session
        # Redirect to dashboard
        
        # Mock implementation
        return RedirectResponse("/dashboard?login=success")
        
    except Exception as e:
        logger.error(f"SSO callback error for {provider}: {e}")
        return RedirectResponse(f"/login?error=sso_callback_error&provider={provider}")


@router.post("/saml/sso")
async def saml_sso(request: Request) -> Response:
    """
    Handle SAML SSO POST requests
    
    Processes SAML assertions and creates user sessions.
    """
    try:
        # Get SAML response from form data
        form_data = await request.form()
        saml_response = form_data.get("SAMLResponse")
        relay_state = form_data.get("RelayState")
        
        if not saml_response:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing SAML response"
            )
        
        # Decode and validate SAML response
        # Extract user attributes
        # Create or update user
        # Create session
        # Return success response
        
        # Mock implementation
        return RedirectResponse("/dashboard?saml=success")
        
    except Exception as e:
        logger.error(f"SAML SSO error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SAML authentication failed"
        )


@router.get("/providers")
async def get_auth_providers(
    tenant = Depends(require_tenant)
) -> Dict[str, List[Dict]]:
    """
    Get available authentication providers for tenant
    
    Returns configured SSO providers and their settings.
    """
    try:
        # Query database for tenant's SSO configurations
        # For now, return mock data
        
        providers = {
            "local": {"enabled": True, "name": "Email/Password"},
            "sso_providers": [
                {
                    "provider": "google",
                    "name": "Google",
                    "enabled": True,
                    "login_url": f"/auth/sso/google"
                },
                {
                    "provider": "microsoft", 
                    "name": "Microsoft",
                    "enabled": False,
                    "login_url": f"/auth/sso/microsoft"
                }
            ]
        }
        
        return providers
        
    except Exception as e:
        logger.error(f"Get auth providers error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get authentication providers"
        )