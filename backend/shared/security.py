"""
Security - JWT authentication & password hashing
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta

# ========== JWT 配置 ==========
_jwt_secret = os.getenv("JWT_SECRET", "")
if not _jwt_secret or _jwt_secret == "mechai-dev-secret-change-in-production":
    _is_production = os.getenv("ENV", "").lower() in ("production", "prod")
    if _is_production:
        raise RuntimeError(
            "JWT_SECRET 未配置或使用了默认值！"
            "生产环境必须设置一个安全的随机密钥。"
        )
    # 开发环境自动生成随机 secret（每次重启变化，仅限本地开发）
    _jwt_secret = secrets.token_hex(32)

SECRET_KEY = _jwt_secret
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 72

security = HTTPBearer()


# ========== JWT Token ==========
def create_access_token(user_id: int, username: str, role: str = "user") -> str:
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Extract user from JWT token"""
    payload = decode_token(credentials.credentials)
    user_id = int(payload.get("sub", 0))
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    return type("User", (), {
        "id": user_id,
        "username": payload.get("username", ""),
        "role": payload.get("role", "user"),
    })()


# ========== Password Hashing (PBKDF2-SHA256) ==========
# 使用 PBKDF2 替代明文 SHA256，无需额外依赖 bcrypt
_HASH_ITERATIONS = 260_000  # OWASP 推荐值
_HASH_ALGO = "sha256"


def get_password_hash(password: str) -> str:
    """生成密码哈希（PBKDF2-SHA256）"""
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac(_HASH_ALGO, password.encode(), salt.encode(), _HASH_ITERATIONS)
    return f"pbkdf2:{_HASH_ALGO}:{_HASH_ITERATIONS}:{salt}:{dk.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> str:
    """验证密码"""
    # 兼容旧的 SHA256 格式
    if not hashed_password.startswith("pbkdf2:"):
        return hmac.compare_digest(
            hashlib.sha256(plain_password.encode()).hexdigest(),
            hashed_password,
        )
    try:
        _, algo, iterations, salt, dk_hex = hashed_password.split(":", 4)
        dk = hashlib.pbkdf2_hmac(algo, plain_password.encode(), salt.encode(), int(iterations))
        return hmac.compare_digest(dk.hex(), dk_hex)
    except (ValueError, TypeError):
        return False
