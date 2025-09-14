"""
Authentication and Authorization for Lending API
Clean auth implementation
"""

import os
import jwt
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from fastapi import HTTPException, Depends, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging
import httpx

logger = logging.getLogger(__name__)

security = HTTPBearer()


class AuthConfig:
    """Authentication configuration"""
    def __init__(self):
        self.jwt_secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
        self.access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        self.adk_web_base_url = os.getenv("ADK_WEB_BASE_URL", "http://localhost:8000")
        self.algorithm = "HS256"


class AuthHandler:
    """Authentication handler for the lending API"""

    def __init__(self):
        self.config = AuthConfig()
        logger.info("AuthHandler initialized")

    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return user info"""
        try:
            # Decode the JWT token
            payload = jwt.decode(
                token,
                self.config.jwt_secret_key,
                algorithms=[self.config.algorithm]
            )

            # Check expiration
            exp = payload.get("exp")
            if exp and datetime.utcnow().timestamp() > exp:
                logger.warning("Token expired")
                return None

            # Extract user information
            user_info = {
                "user_id": payload.get("sub"),
                "email": payload.get("email"),
                "algorand_address": payload.get("algorand_address"),
                "roles": payload.get("roles", []),
                "exp": exp
            }

            return user_info

        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return None

    async def verify_adk_web_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify token against ADK-Web authentication service"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.config.adk_web_base_url}/api/auth/verify",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10.0
                )

                if response.status_code == 200:
                    user_data = response.json()
                    return {
                        "user_id": user_data.get("user_id"),
                        "email": user_data.get("email"),
                        "algorand_address": user_data.get("algorand_address"),
                        "roles": user_data.get("roles", []),
                        "verified_by": "adk_web"
                    }
                else:
                    logger.warning(f"ADK-Web token verification failed: {response.status_code}")
                    return None

        except httpx.TimeoutException:
            logger.error("ADK-Web authentication service timeout")
            return None
        except Exception as e:
            logger.error(f"ADK-Web token verification error: {e}")
            return None

    def create_access_token(self, user_data: Dict[str, Any]) -> str:
        """Create JWT access token"""
        expire = datetime.utcnow() + timedelta(minutes=self.config.access_token_expire_minutes)

        payload = {
            "sub": user_data.get("user_id"),
            "email": user_data.get("email"),
            "algorand_address": user_data.get("algorand_address"),
            "roles": user_data.get("roles", []),
            "iat": datetime.utcnow().timestamp(),
            "exp": expire.timestamp()
        }

        token = jwt.encode(payload, self.config.jwt_secret_key, algorithm=self.config.algorithm)
        return token

    def has_role(self, user: Dict[str, Any], required_role: str) -> bool:
        """Check if user has required role"""
        user_roles = user.get("roles", [])
        return required_role in user_roles

    def has_any_role(self, user: Dict[str, Any], required_roles: list) -> bool:
        """Check if user has any of the required roles"""
        user_roles = user.get("roles", [])
        return any(role in user_roles for role in required_roles)


# Global auth handler instance
auth_handler = AuthHandler()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> Dict[str, Any]:
    """Dependency to get current authenticated user"""
    try:
        token = credentials.credentials

        # First, try standard JWT verification
        user = await auth_handler.verify_token(token)

        # If that fails, try ADK-Web verification
        if not user:
            user = await auth_handler.verify_adk_web_token(token)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_admin_user(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Dependency to get admin user"""
    if not auth_handler.has_role(user, "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user


async def get_lender_user(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Dependency to get lender user"""
    if not auth_handler.has_any_role(user, ["lender", "admin"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Lender access required"
        )
    return user


def create_demo_token() -> str:
    """Create a demo token for testing"""
    demo_user = {
        "user_id": "demo_user_123",
        "email": "demo@example.com",
        "algorand_address": "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q",
        "roles": ["borrower"]
    }

    return auth_handler.create_access_token(demo_user)


if __name__ == "__main__":
    # Generate demo token for testing
    demo_token = create_demo_token()
    print(f"Demo token: {demo_token}")
    print("Use this token in Authorization header: Bearer <token>")