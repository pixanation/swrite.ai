import requests
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User

security = HTTPBearer()

# Cache JWKS
JWKS_CACHE = None

def get_jwks():
    global JWKS_CACHE
    if JWKS_CACHE is None:
        jwks_url = f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json"
        try:
            response = requests.get(jwks_url)
            response.raise_for_status()
            JWKS_CACHE = response.json()
            print("Fetched JWKS keys")
        except Exception as e:
            print(f"Failed to fetch JWKS: {e}")
            raise HTTPException(status_code=500, detail="Could not verify token configuration")
    return JWKS_CACHE

def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Verifies the Supabase JWT.
    Supports HS256 (Secret) and RS256/ES256 (JWKS).
    """
    token = credentials.credentials
    try:
        header = jwt.get_unverified_header(token)
        alg = header.get('alg')
        
        # 1. Verification Key Selection
        if alg == 'HS256':
            key = settings.SUPABASE_JWT_SECRET
        elif alg in ['RS256', 'ES256']:
            jwks = get_jwks()
            key = jwks # python-jose handles JWKS dict directly usually, or we pass keys
            # jose.jwt.decode can accept the JWKS dict in simple cases, 
            # or we might need to find the specific key. 
            # python-jose 'decode' usually needs the specific key or full JWKS if it supports it.
            # Let's try passing the full JWKS dict, python-jose supports it for 'hmac' not always others.
            # Actually standard python-jose usage for JWKS is:
            # key = next(k for k in jwks['keys'] if k['kid'] == header['kid'])
            # But let's try the library's ability to pick from list/dict first or write simple picker.
            pass # See logic below
        else:
            raise HTTPException(status_code=401, detail=f"Unsupported algorithm: {alg}")

        # 2. Decode
        if alg == 'HS256':
             payload = jwt.decode(
                token, 
                key, 
                algorithms=[alg],
                audience="authenticated"
            )
        else:
            # For RS256/ES256 with JWKS
            # Simple manual key lookup
            jwks = get_jwks()
            # python-jose doesn't auto-lookup from a dict in `decode` typically unless configured.
            # We find the matching key manually.
            rsa_key = {}
            for k in jwks['keys']:
                if k['kid'] == header['kid']:
                    rsa_key = k
                    break
            if not rsa_key:
                raise HTTPException(status_code=401, detail="Invalid token kid")
                
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=[alg],
                audience="authenticated"
            )

        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return user_id
        
    except JWTError as e:
        print(f"JWT Verification Error: {str(e)}")
        # print(f"Token Header: {jwt.get_unverified_header(token)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Validation Failed. Error: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(
    user_id: str = Depends(get_current_user_id), 
    db: Session = Depends(get_db)
) -> User:
    """
    Gets the user from the local DB.
    If Supabase user exists but local user doesn't, we might need to sync or create.
    For Phase 1, we assume the user is created in public.users trigger or we lazy-create.
    Let's lazy-create for simplicity if strict syncing isn't set up.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        # Option: Lazy create if they authenticated with Supabase but aren't in our table
        # We need their email. It's usually in the JWT metadata.
        # But to be clean, let's just return 404 or creating strictly.
        # Strict logic: User should exist. 
        # But for Phase 1 dev speed, I will handle lazy creation if I can access email from token.
        pass
    
    if not user:
        # Fallback: Just return the ID wrapped if we treat Auth as source of truth
        # But models require a DB instance.
        raise HTTPException(status_code=404, detail="User not found in local DB")
    return user
