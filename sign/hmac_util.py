import base64
import hashlib
import hmac
import urllib.parse


def hmac_sha256(key: str, data: str):
    hmac_code = hmac.new(
        key.encode("utf-8"),
        data.encode("utf-8"),
        hashlib.sha256
    ).digest()
    # Base64 URL-safe 编码
    base64_encoded = base64.urlsafe_b64encode(hmac_code)
    # URL 编码
    result = urllib.parse.quote(base64_encoded.decode('utf-8'))
    return result
