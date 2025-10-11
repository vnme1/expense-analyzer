# 💰 개인 가계부 분석기 (Expense Analyzer)

> **Python + Streamlit 기반의 개인 재무 분석 도구 + AI 자동 분류 🤖**  
> 은행 또는 카드사 거래내역 CSV 파일을 업로드하면 자동으로 **카테고리별 지출 분석**과 **월별 수입/지출 추이**를 시각화해주는 웹 대시보드입니다.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.31+-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

---

## 📘 프로젝트 개요

- **프로젝트명:** 개인 가계부 분석기 (Expense Analyzer)
- **목표:** 사용자의 실제 거래내역 데이터를 기반으로 소비 패턴을 분석하고 시각화
- **형태:** Streamlit 기반 웹 대시보드 (로컬에서 즉시 실행 가능)
- **핵심 기술:** `Python`, `pandas`, `plotly`, `streamlit`, `scikit-learn` (AI)

---

## 🎯 기획 의도

> "가계부는 있지만 분석은 귀찮다"  
> → 이 프로젝트는 CSV 파일 하나만 업로드하면 자동으로 **지출 요약, 시각화, 월별 트렌드 분석**을 해주는 개인 재무 분석 도구입니다.

### 주요 목표
- 일상 속 금융 데이터를 분석 가능한 형태로 전환
- 복잡한 엑셀 피벗 없이 웹에서 한눈에 소비 패턴 확인
- **AI 자동 분류**로 카테고리 입력 없이도 자동 분석
- 개인 맞춤형 예산 관리 및 소비 습관 개선에 도움

---

## ✨ 주요 기능

### 📊 대시보드
- 총 수입, 총 지출, 잔액 한눈에 확인
- 카테고리별 지출 비율 파이차트
- 월별 수입/지출 막대그래프

### 📈 상세 분석
- 카테고리별 지출 상세 막대그래프
- 비율(%) 포함 상세 테이블

### 📅 월별 추이
- 수입/지출/잔액 라인 차트
- 월별 상세 내역 테이블

### 🔍 데이터 탐색
- 카테고리/구분별 필터링
- 날짜/금액/카테고리 기준 정렬
- 필터링된 데이터 CSV 다운로드

### 🤖 AI 자동 분류 (NEW!)
- **'적요' 내용만으로 카테고리 자동 예측**
- 키워드 기반 규칙 + 머신러닝(TF-IDF + Naive Bayes)
- 사용자 데이터로 AI 모델 학습 가능
- 실시간 예측 테스트 기능

---

## 🛠 기술 스택

| 구분 | 사용 기술 | 설명 |
|------|------------|------|
| Language | **Python 3.10+** | 데이터 처리 및 로직 구현 |
| Framework | **Streamlit** | 웹 대시보드 프레임워크 |
| Data Handling | **pandas** | CSV 데이터 로딩, 가공 |
| Visualization | **plotly**, **matplotlib**, **seaborn** | 대화형 및 정적 그래프 시각화 |
| AI/ML | **scikit-learn** | 카테고리 자동 분류 (TF-IDF + Naive Bayes) |
| Others | **openpyxl** | 엑셀 파일 처리 |

---

## 📂 프로젝트 구조

```
expense-analyzer/
├── app.py                    # Streamlit 메인 앱 (5개 탭)
├── data/
│   └── sample.csv           # 샘플 거래내역 데이터 (17건)
├── utils/
│   ├── __init__.py          # 패키지 초기화
│   ├── preprocess.py        # 데이터 전처리 함수
│   └── ai_categorizer.py    # AI 자동 분류 모듈
├── models/                   # AI 모델 저장 폴더 (자동 생성)
│   └── category_model.pkl
├── requirements.txt         # 의존성 패키지 목록
└── README.md               # 프로젝트 문서
```

---

## ⚙️ 설치 및 실행 방법

### 1️⃣ 프로젝트 클론
```bash
git clone https://github.com/username/expense-analyzer.git
cd expense-analyzer
```

### 2️⃣ 가상환경 생성 및 활성화
```bash
# 가상환경 생성
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3️⃣ 의존성 설치
```bash
pip install -r requirements.txt
```

### 4️⃣ 앱 실행
```bash
streamlit run app.py
```

**접속:** http://localhost:8501

---

## 📊 CSV 파일 형식

### 필수 컬럼
- `날짜`: YYYY-MM-DD 형식
- `금액`: 숫자 (수입은 양수, 지출은 음수)
- `적요`: 거래 내역 설명 (AI 분류에 필수!)

### 선택 컬럼
- `분류`: 카테고리 (없으면 AI가 자동 예측)
- `메모`: 추가 메모

### 예시 1: 카테고리 포함 (일반 사용)
```csv
날짜,적요,금액,분류,메모
2025-01-02,스타벅스,-4500,카페,아메리카노
2025-01-03,월급,2500000,급여,1월 급여
2025-01-04,이마트,-75000,식비,장보기
```

### 예시 2: 카테고리 없음 (AI 자동 분류)
```csv
날짜,적요,금액,메모
2025-01-02,스타벅스,-4500,아메리카노
2025-01-03,월급,2500000,1월 급여
2025-01-04,이마트,-75000,장보기
```

---

## 🤖 AI 자동 분류 사용법

### 방법 A: 카테고리 없는 데이터 자동 분류
1. 사이드바에서 **"AI 자동 분류 사용"** 체크박스 활성화
2. 카테고리 없는 CSV 파일 업로드
3. AI가 자동으로 카테고리 예측!

### 방법 B: 기존 데이터로 AI 학습
1. 카테고리가 **포함된** CSV 파일 업로드
2. **"AI 학습"** 탭으로 이동
3. **"모델 학습 시작"** 버튼 클릭
4. 학습 완료 후 `models/` 폴더에 모델 저장
5. 이후 카테고리 없는 데이터도 자동 분류 가능!

### AI 작동 원리
1. **키워드 기반 분류** (규칙 기반)
   - "스타벅스" in 적요 → 카페
   - "이마트" in 적요 → 식비
   - "CGV" in 적요 → 여가

2. **머신러닝 분류** (학습 기반)
   - TF-IDF 벡터화 → Naive Bayes 분류
   - 사용자 데이터로 학습 가능

---

## 📸 화면 구성

### 1. 대시보드 탭
- 요약 지표 (총 수입/지출/잔액)
- 카테고리별 지출 파이차트
- 월별 수입/지출 막대그래프

### 2. 상세 분석 탭
- 카테고리별 지출 막대그래프
- 비율(%) 테이블

### 3. 월별 추이 탭
- 수입/지출/잔액 라인 차트
- 월별 상세 내역 테이블

### 4. 데이터 탐색 탭
- 필터링 (카테고리/구분)
- 정렬 (날짜/금액/분류)
- CSV 다운로드

### 5. AI 학습 탭
- 모델 상태 확인
- 모델 학습 및 평가
- 실시간 예측 테스트

---

## 🚀 향후 개발 계획

### ✅ 완료
- [x] 기본 대시보드 (4개 탭)
- [x] AI 자동 분류 기능
- [x] 실시간 예측 테스트
- [x] 모델 학습/저장/로드

### 🔜 단기 (1-2주)
- [ ] 예산 설정 및 초과 알림 기능
- [ ] 월간 PDF 리포트 자동 생성
- [ ] 엑셀 파일 업로드 지원

### 🔮 중기 (1개월)
- [ ] SQLite 데이터베이스 연동 (영구 저장)
- [ ] 사용자 인증 시스템
- [ ] 대시보드 커스터마이징

### 🎯 장기 (3개월)
- [ ] 모바일 앱 개발 (React Native)
- [ ] 은행 API 연동 (자동 데이터 수집)
- [ ] 다중 사용자 지원

---

## 🤝 기여 방법

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

---

## 📧 문의

- **개발자:** Your Name
- **이메일:** your.email@example.com
- **GitHub:** [@username](https://github.com/username)

---

## 🙏 감사의 말

- [Streamlit](https://streamlit.io/) - 빠른 웹앱 개발 프레임워크
- [Plotly](https://plotly.com/) - 인터랙티브 차트 라이브러리
- [pandas](https://pandas.pydata.org/) - 데이터 처리 라이브러리
- [scikit-learn](https://scikit-learn.org/) - 머신러닝 라이브러리

---

## 🎓 사용 예시

### 예시 1: 기본 분석
```bash
streamlit run app.py
# 1. 샘플 CSV 다운로드
# 2. 파일 업로드
# 3. 대시보드에서 지출 패턴 확인
```

### 예시 2: AI 자동 분류
```bash
streamlit run app.py
# 1. AI용 샘플 다운로드 (카테고리 없음)
# 2. "AI 자동 분류 사용" 체크
# 3. 파일 업로드
# 4. 자동으로 카테고리 예측됨!
```

### 예시 3: AI 모델 학습
```bash
streamlit run app.py
# 1. 카테고리 포함 CSV 업로드
# 2. "AI 학습" 탭으로 이동
# 3. "모델 학습 시작" 클릭
# 4. 학습 완료 후 models/ 폴더에 저장
```

---

**⭐ 이 프로젝트가 도움이 되었다면 Star를 눌러주세요!**