# 💰 Expense Analyzer 설치 가이드

## 📋 시스템 요구사항

- **Python**: 3.10 이상
- **운영체제**: Windows, macOS, Linux
- **메모리**: 최소 2GB RAM
- **디스크 공간**: 최소 500MB

---

## 🚀 빠른 시작 (3단계)

### 1️⃣ 프로젝트 다운로드

```bash
# Git Clone (권장)
git clone https://github.com/username/expense-analyzer.git
cd expense-analyzer

# 또는 ZIP 다운로드 후 압축 해제
```

### 2️⃣ 가상환경 생성 및 패키지 설치

**Windows:**
```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화
venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt
```

**macOS / Linux:**
```bash
# 가상환경 생성
python3 -m venv venv

# 가상환경 활성화
source venv/bin/activate

# 패키지 설치
pip install -r requirements.txt
```

### 3️⃣ 앱 실행

```bash
streamlit run app.py
```

브라우저가 자동으로 열리며 `http://localhost:8501`로 접속됩니다.

---

## ⚠️ 문제 해결 (Troubleshooting)

### 문제 1: kaleido 설치 오류 (PDF 생성 실패)

**증상:**
```
ERROR: Could not build wheels for kaleido
```

**해결 방법 A (권장):**
```bash
# pip 업그레이드 후 재설치
pip install --upgrade pip
pip install kaleido==0.2.1
```

**해결 방법 B (대체 설치):**
```bash
# conda 사용 (Anaconda 환경)
conda install -c conda-forge python-kaleido
```

**해결 방법 C (수동 설치):**
```bash
# 플랫폼별 수동 설치
# Windows
pip install kaleido==0.2.1 --no-cache-dir

# macOS (M1/M2)
pip install kaleido --no-binary kaleido
```

**임시 우회:**
- kaleido 없이도 앱은 정상 작동합니다
- PDF 생성 시 차트만 제외되고 나머지는 정상 생성됩니다

---

### 문제 2: ModuleNotFoundError

**증상:**
```python
ModuleNotFoundError: No module named 'streamlit'
```

**해결:**
```bash
# 가상환경이 활성화되었는지 확인
# 프롬프트에 (venv) 표시가 있어야 함

# 패키지 재설치
pip install -r requirements.txt --force-reinstall
```

---

### 문제 3: 한글 깨짐 (CSV 업로드 시)

**해결:**
- CSV 파일을 **UTF-8 인코딩**으로 저장해주세요
- Excel에서 저장 시: "CSV UTF-8 (쉼표로 분리)" 선택

**Excel에서 UTF-8 CSV 만들기:**
1. 엑셀에서 데이터 작성
2. 파일 → 다른 이름으로 저장
3. 파일 형식: **CSV UTF-8 (쉼표로 분리) (*.csv)** 선택
4. 저장

---

### 문제 4: 포트 충돌 (8501 포트 사용 중)

**증상:**
```
OSError: [Errno 48] Address already in use
```

**해결:**
```bash
# 다른 포트로 실행
streamlit run app.py --server.port 8502
```

---

### 문제 5: AI 모델 학습 오류

**증상:**
```
ValueError: n_samples=17 should be >= n_classes=10
```

**원인:** 학습 데이터가 너무 적습니다 (17건 < 카테고리 10개)

**해결:**
- 최소 **50건 이상**의 다양한 데이터로 학습해주세요
- 샘플 데이터는 테스트용이며, 실제 학습에는 부족합니다

---

## 📦 의존성 패키지 상세

| 패키지 | 버전 | 용도 |
|--------|------|------|
| streamlit | 1.31+ | 웹 대시보드 프레임워크 |
| pandas | 2.2+ | 데이터 처리 |
| plotly | 5.18+ | 인터랙티브 차트 |
| scikit-learn | 1.4+ | AI 자동 분류 |
| reportlab | 4.0+ | PDF 생성 |
| kaleido | 0.2.1+ | PDF 차트 이미지 변환 |

---

## 🧪 설치 확인

설치가 완료되었는지 확인하려면:

```bash
# Python 버전 확인
python --version
# 출력: Python 3.10.x 이상

# 패키지 확인
pip list | grep streamlit
# 출력: streamlit    1.31.x

# 앱 실행 테스트
streamlit run app.py
# 브라우저가 열리면 성공!
```

---

## 🔄 업데이트 방법

```bash
# Git으로 최신 버전 받기
git pull origin main

# 패키지 업데이트
pip install -r requirements.txt --upgrade
```

---

## 🆘 여전히 문제가 있나요?

1. **GitHub Issues**: 버그 리포트 및 질문
2. **이메일**: your.email@example.com
3. **Discord**: [커뮤니티 링크]

---

## 💡 추가 팁

### 개발 모드로 실행
```bash
# 자동 리로드 활성화
streamlit run app.py --server.runOnSave true
```

### 데이터 폴더 생성
```bash
# 자동 생성되지만, 수동 생성도 가능
mkdir -p data models
```

### 로그 확인
```bash
# Streamlit 로그 출력
streamlit run app.py --logger.level=debug
```

---
