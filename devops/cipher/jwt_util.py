"""
pip install PyJWT
"""
import time
import jwt


def gen_hs256_token(sub: str, secret: str = "your-jwt-secret-key-minimum-32-characters-long", exp_days: int = 30) -> str:
    """生成 HS256 JWT token"""
    now = int(time.time())
    payload = {
        "sub": sub,
        "iat": now,
        "exp": now + exp_days * 24 * 3600
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def validate_hs256_token(token: str, secret: str = "your-jwt-secret-key-minimum-32-characters-long") -> dict:
    """验证并解析 HS256 JWT token"""
    try:
        return jwt.decode(token, secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise ValueError("Token 已过期")
    except jwt.InvalidTokenError:
        raise ValueError("无效的 Token")
    

if __name__ == "__main__":
    token = gen_hs256_token(sub="liuzhenghua-jk", exp_days=3650)
    print(token)
    print(validate_hs256_token(token))