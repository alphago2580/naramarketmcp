"""API 키 암호화/복호화 유틸리티."""

import base64
import logging

logger = logging.getLogger(__name__)


def simple_encrypt(text: str, key: str = "naramarket_builtin_2024") -> str:
    """간단한 XOR 기반 암호화."""
    try:
        # XOR 암호화
        encrypted_bytes = []
        for i, char in enumerate(text):
            key_char = key[i % len(key)]
            encrypted_bytes.append(ord(char) ^ ord(key_char))

        # Base64 인코딩
        encrypted_data = bytes(encrypted_bytes)
        return base64.b64encode(encrypted_data).decode('utf-8')
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        return ""


def simple_decrypt(encrypted_text: str, key: str = "naramarket_builtin_2024") -> str:
    """간단한 XOR 기반 복호화."""
    try:
        # Base64 디코딩
        encrypted_data = base64.b64decode(encrypted_text.encode('utf-8'))

        # XOR 복호화
        decrypted_chars = []
        for i, byte_val in enumerate(encrypted_data):
            key_char = key[i % len(key)]
            decrypted_chars.append(chr(byte_val ^ ord(key_char)))

        return ''.join(decrypted_chars)
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        return ""


# 운영 키를 암호화해서 저장 (실제 키는 여기서 설정)
def get_encrypted_builtin_key() -> str:
    """암호화된 내장 운영 키 반환."""
    # 이미 암호화된 형태로 직접 반환
    return "Yfm/v/3wyKFDBpePvGW971cKQuXU1plJi65t5KjzSQNO4hml/Z1u1obwVWD7Ajzux6Rdlb+uLlyB9vDhAdrZEA=="


def get_builtin_service_key() -> str:
    """내장 운영 키 복호화해서 반환."""
    encrypted_key = get_encrypted_builtin_key()
    if not encrypted_key:
        return ""

    return simple_decrypt(encrypted_key)


def setup_production_key(production_key: str) -> str:
    """실제 운영 키를 암호화해서 코드에 사용할 수 있는 형태로 변환."""
    if not production_key or production_key.strip() == "":
        return "Error: Empty key provided"

    encrypted = simple_encrypt(production_key)

    return f"""
# 다음 코드를 key_utils.py의 get_encrypted_builtin_key() 함수에 복사하세요:
actual_key = "{production_key}"  # 실제 운영 키

# 또는 이미 암호화된 형태를 직접 사용:
return "{encrypted}"
"""


def get_key_status() -> dict:
    """현재 키 설정 상태 확인."""
    builtin_available = bool(get_builtin_service_key())

    status = {
        "builtin_key_configured": builtin_available,
        "encryption_working": True
    }

    # 암호화 테스트
    try:
        test_key = "test_12345"
        encrypted = simple_encrypt(test_key)
        decrypted = simple_decrypt(encrypted)
        status["encryption_working"] = (test_key == decrypted)
    except:
        status["encryption_working"] = False

    return status


# 테스트 함수
def test_encryption():
    """암호화/복호화 테스트."""
    test_key = "test_api_key_12345"
    encrypted = simple_encrypt(test_key)
    decrypted = simple_decrypt(encrypted)

    print(f"Original: {test_key}")
    print(f"Encrypted: {encrypted}")
    print(f"Decrypted: {decrypted}")
    print(f"Match: {test_key == decrypted}")


if __name__ == "__main__":
    # 키 설정 상태 확인
    status = get_key_status()
    print("=== Key Configuration Status ===")
    print(f"Builtin key configured: {status['builtin_key_configured']}")
    print(f"Encryption working: {status['encryption_working']}")

    print("\n=== Encryption Test ===")
    test_encryption()

    # 실제 키 설정 가이드
    print("\n=== Setup Guide ===")
    print("To configure your production API key:")
    print("1. Get your production API key from data.go.kr")
    print("2. Run: python -c \"from src.core.key_utils import setup_production_key; print(setup_production_key('YOUR_ACTUAL_KEY'))\"")
    print("3. Copy the result to key_utils.py")