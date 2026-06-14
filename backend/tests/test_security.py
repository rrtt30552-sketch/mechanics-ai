"""
Tests for shared/security.py
"""
import os
import sys

# Ensure backend is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Set test env before importing
os.environ["JWT_SECRET"] = "test-secret-key-for-unit-tests"

from shared.security import (
    create_access_token,
    decode_token,
    get_password_hash,
    verify_password,
)


def test_jwt_roundtrip():
    """JWT 创建和解析"""
    token = create_access_token(user_id=42, username="testuser", role="student")
    payload = decode_token(token)
    assert payload["sub"] == "42"
    assert payload["username"] == "testuser"
    assert payload["role"] == "student"


def test_password_hashing():
    """密码哈希和验证"""
    password = "my_secure_password_123"
    hashed = get_password_hash(password)

    # 哈希应该包含 pbkdf2 标记
    assert hashed.startswith("pbkdf2:")

    # 验证正确密码
    assert verify_password(password, hashed) is True

    # 验证错误密码
    assert verify_password("wrong_password", hashed) is False


def test_password_different_hashes():
    """相同密码应该生成不同的哈希（因为随机 salt）"""
    pw = "same_password"
    h1 = get_password_hash(pw)
    h2 = get_password_hash(pw)
    assert h1 != h2
    # 但都能验证
    assert verify_password(pw, h1) is True
    assert verify_password(pw, h2) is True


def test_legacy_sha256_compat():
    """兼容旧的 SHA256 格式"""
    import hashlib
    old_hash = hashlib.sha256("old_password".encode()).hexdigest()
    assert verify_password("old_password", old_hash) is True
    assert verify_password("wrong_password", old_hash) is False


if __name__ == "__main__":
    test_jwt_roundtrip()
    test_password_hashing()
    test_password_different_hashes()
    test_legacy_sha256_compat()
    print("✅ All security tests passed!")
