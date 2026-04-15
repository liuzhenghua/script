import time
from utils.sign.hmac_util import hmac_sha256


def test_hmac_sha256_with_timestamp_and_secret():
    """测试 hmac_sha256 方法，使用 timestamp 和 secret"""
    timestamp = str(int(time.time() * 1000))
    secret = "2ce6584e4fbd4a69800642fa02324e50ef78ea70463b438788bcdc60373bfd8b"
    string_to_sign = f"{timestamp}\n{secret}"

    result = hmac_sha256(secret, string_to_sign)

    print(f"timestamp={timestamp}&sign={result}")

    # 验证返回结果是 URL 编码后的字符串
    assert isinstance(result, str)
    assert len(result) > 0
    # URL 编码结果中不应包含需要编码的字符
    assert "+" not in result
    assert "/" not in result
    assert "=" not in result