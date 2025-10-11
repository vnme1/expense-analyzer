# 💰 개인 가계부 분석기 (Streamlit Dashboard)

> **Python + Streamlit 기반의 개인 재무 분석 도구**  
> 은행 또는 카드사 거래내역 CSV 파일을 업로드하면 자동으로 **카테고리별 지출 분석**과 **월별 수입/지출 추이**를 시각화해주는 웹 대시보드입니다.  
> 데이터 분석, 시각화, 자동화 역량을 동시에 보여줄 수 있는 포트폴리오형 프로젝트입니다.

---

## 📘 프로젝트 개요
- **프로젝트명:** 개인 가계부 분석기 (Expense Analyzer)
- **목표:** 사용자의 실제 거래내역 데이터를 기반으로 소비 패턴을 분석하고 시각화
- **형태:** Streamlit 기반 웹 대시보드 (로컬에서 즉시 실행 가능)
- **핵심 기술:** `Python`, `pandas`, `plotly`, `streamlit`

---

## 🧠 기획 의도
> “가계부는 있지만 분석은 귀찮다”  
> → 이 프로젝트는 CSV 파일 하나만 업로드하면 자동으로 **지출 요약, 시각화, 월별 트렌드 분석**을 해주는 개인 재무 분석 도구입니다.

- 일상 속 금융 데이터를 분석 가능한 형태로 전환
- 복잡한 엑셀 피벗 없이 웹에서 한눈에 소비 패턴 확인
- 개인 맞춤형 예산 관리 및 소비 습관 개선에 도움

---

## 🛠 기술 스택
| 구분 | 사용 기술 | 설명 |
|------|------------|------|
| Language | **Python 3.10+** | 데이터 처리 및 로직 구현 |
| Framework | **Streamlit** | 웹 대시보드 프레임워크 |
| Data Handling | **pandas** | CSV 데이터 로딩, 가공 |
| Visualization | **plotly**, **matplotlib**, **seaborn** | 대화형 및 정적 그래프 시각화 |
| Others | **openpyxl** | 엑셀 저장 시 사용 가능 |

---

## 📂 프로젝트 구조
expense-analyzer/
├─ app.py # Streamlit 메인 앱
├─ data/
│ └─ sample.csv # 샘플 거래내역 데이터
├─ utils/
│ └─ preprocess.py # 데이터 전처리 함수 모음
└─ requirements.txt # 의존성 패키지 목록


---

## ⚙️ 설치 및 실행 방법

### 1️⃣ 프로젝트 클론
```bash
git clone https://github.com/username/expense-analyzer.git
cd expense-analyzer


python -m venv venv
venv\Scripts\activate          # Windows
# 또는
source venv/bin/activate       # macOS / Linux
pip install -r requirements.txt
python -m streamlit run app.py
