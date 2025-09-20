# 내장 운영 키 설정 가이드

naramarketmcp 서버에 운영 API 키를 내장하여 사용자가 별도로 키를 설정하지 않아도 서비스를 이용할 수 있도록 하는 방법입니다.

## 🔐 키 우선순위

1. **사용자 제공 키** (환경변수 `NARAMARKET_SERVICE_KEY`)
2. **Smithery.ai 설정 키**
3. **내장 운영 키** (자동 사용)

## 🚀 운영 키 설정 방법

### 1단계: 운영 키 준비
- 공공데이터포털(data.go.kr)에서 발급받은 운영 계정 API 키
- 하루 10만건 제한, 무료 사용 가능

### 2단계: 키 암호화
```bash
cd naramarketmcp
python -c "from src.core.key_utils import setup_production_key; print(setup_production_key('실제_운영_키_여기'))"
```

### 3단계: 암호화된 키 설정
위 명령어 결과를 `src/core/key_utils.py` 파일의 `get_encrypted_builtin_key()` 함수에 복사:

```python
def get_encrypted_builtin_key() -> str:
    """암호화된 내장 운영 키 반환."""
    actual_key = "실제_운영_키_여기"  # <- 이 부분을 실제 키로 교체
    return simple_encrypt(actual_key)
```

## 📊 설정 상태 확인

### 서버 상태 확인
```python
# MCP 도구로 확인
get_api_key_status()

# 또는 직접 확인
python src/core/key_utils.py
```

### 예상 출력
```
=== Key Configuration Status ===
Builtin key configured: True
Encryption working: True

=== API Key Usage ===
Using builtin production API key (length: 40)
```

## 🛡️ 보안 특징

- **암호화 저장**: XOR + Base64 암호화로 키 보호
- **환경변수 우선**: 사용자 키가 있으면 우선 사용
- **로깅 보안**: 키 값은 로그에 노출되지 않음 (길이만 표시)
- **키 검증**: 유효하지 않은 키 자동 감지

## 💡 사용자 경험

### 키 없이 사용 (권장)
```python
# 별도 설정 없이 바로 사용 가능
get_bid_announcement_construction(days_back=7)
```

### 개인 키 사용
```bash
export NARAMARKET_SERVICE_KEY=개인_키
# 또는 .env 파일에 설정
```

## 🔧 문제 해결

### 내장 키가 작동하지 않는 경우
1. `python src/core/key_utils.py` 실행
2. "Builtin key configured: False" 확인
3. `get_encrypted_builtin_key()` 함수의 `actual_key` 값 확인
4. 실제 운영 키로 교체

### 암호화가 작동하지 않는 경우
1. `encryption_working: False` 확인
2. Python 환경 및 라이브러리 확인
3. 키 문자열 형식 확인 (특수문자 포함 여부)

## 📈 사용량 모니터링

- 내장 키 사용량은 공공데이터포털에서 모니터링
- 하루 10만건 제한 도달시 사용자에게 개인 키 설정 안내
- `server_info()` 도구로 키 상태 실시간 확인

## ⚠️ 주의사항

1. **실제 키 보안**: `key_utils.py` 파일을 공개 저장소에 커밋하지 마세요
2. **키 교체**: 주기적으로 운영 키를 교체하고 암호화된 값을 업데이트
3. **사용량 관리**: 일일 사용량을 모니터링하여 제한 초과 방지
4. **배포시 확인**: 배포 전 키 설정 상태를 반드시 확인

## 🎯 장점

- **사용자 편의성**: 키 설정 없이 바로 사용 가능
- **확장성**: 사용자가 개인 키를 원하면 언제든 설정 가능
- **보안성**: 키 암호화 저장으로 보안 강화
- **투명성**: 키 사용 상태를 실시간으로 확인 가능