"""
Expense Analyzer - 개인 가계부 분석 대시보드
v3.0 - SQLite 데이터베이스 통합
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO
import os

# 유틸리티 임포트
from utils.database import ExpenseDatabase
from utils.preprocess import load_data
from utils.ai_categorizer import CategoryClassifier
from utils.budget_manager import BudgetManager
from utils.theme_manager import ThemeManager
from utils.pdf_generator import PDFReportGenerator
from utils.category_manager import CategoryManager
from utils.data_validator import DataValidator
from utils.export_manager import ExportManager
from utils.savings_goal import SavingsGoalManager
from utils.recurring_transactions import RecurringTransactionManager
from utils.tag_manager import TagManager
from utils.comparison_analyzer import ComparisonAnalyzer
from utils.expense_predictor import ExpensePredictor
from utils.search_engine import SearchEngine
from utils.favorites_manager import FavoritesManager
from utils.advanced_filter import AdvancedFilter

# 페이지 설정
st.set_page_config(
    page_title="Expense Analyzer",
    page_icon="💰",
    layout="wide"
)

# 세션 상태 초기화
if 'show_budget_settings' not in st.session_state:
    st.session_state['show_budget_settings'] = False

if 'use_sample' not in st.session_state:
    st.session_state['use_sample'] = False

if 'suggested_budgets' not in st.session_state:
    st.session_state['suggested_budgets'] = None

if 'quick_filter' not in st.session_state:
    st.session_state['quick_filter'] = None

if 'db_migrated' not in st.session_state:
    st.session_state['db_migrated'] = False

# 관리자 객체 캐싱
@st.cache_resource
def get_managers():
    """모든 관리자 객체 싱글톤"""
    classifier = CategoryClassifier()
    classifier.load_model()
    
    return {
        'database': ExpenseDatabase(),
        'classifier': classifier,
        'budget_manager': BudgetManager(),
        'theme_manager': ThemeManager(),
        'pdf_generator': PDFReportGenerator(),
        'category_manager': CategoryManager(),
        'data_validator': DataValidator(),
        'export_manager': ExportManager(),
        'savings_goal_manager': SavingsGoalManager(),
        'recurring_manager': RecurringTransactionManager(),
        'tag_manager': TagManager(),
        'comparison_analyzer': ComparisonAnalyzer(),
        'expense_predictor': ExpensePredictor(),
        'search_engine': SearchEngine(),
        'favorites_manager': FavoritesManager(),
        'advanced_filter': AdvancedFilter()
    }

managers = get_managers()
db = managers['database']
theme_manager = managers['theme_manager']

# 테마 적용
if theme_manager.get_theme_name() == 'dark':
    theme_manager.apply_theme()

# 타이틀
st.title("💰 개인 가계부 분석기")
st.markdown("**v3.0 - SQLite 데이터베이스 통합 🚀**")

# ===== 사이드바 =====
with st.sidebar:
    st.header("📂 데이터 관리")
    
    # 테마 토글
    st.markdown("### 🎨 테마")
    current_theme = theme_manager.get_theme_name()
    
    col_theme1, col_theme2 = st.columns([3, 1])
    with col_theme1:
        st.caption(f"{'🌙 다크' if current_theme == 'dark' else '☀️라이트'} 모드")
    with col_theme2:
        if st.button("🔄", help="테마 변경", use_container_width=True):
            theme_manager.toggle_theme()
            st.rerun()
    
    st.markdown("---")
    
    # 🔥 중요: 파일 업로드 + 자동 저장
    st.markdown("### 📥 파일 업로드")
    uploaded_file = st.file_uploader(
        "CSV/Excel",
        type=['csv', 'xlsx', 'xls'],
        help="업로드 시 자동으로 SQLite에 저장됩니다"
    )
    
    # 업로드 즉시 처리
    if uploaded_file is not None:
        # 세션에 업로드 파일 저장 (재실행 시에도 유지)
        if 'last_uploaded_file' not in st.session_state or \
           st.session_state['last_uploaded_file'] != uploaded_file.name:
            
            with st.spinner('📥 파일을 SQLite에 저장하는 중...'):
                try:
                    # 임시 파일로 저장
                    temp_path = f'data/temp_{uploaded_file.name}'
                    os.makedirs('data', exist_ok=True)
                    
                    with open(temp_path, 'wb') as f:
                        f.write(uploaded_file.getvalue())
                    
                    # SQLite로 가져오기
                    result = db.import_from_csv(temp_path)
                    
                    if result['success']:
                        st.success(f"✅ {result['message']}")
                        st.session_state['last_uploaded_file'] = uploaded_file.name
                        st.balloons()
                        
                        # 임시 파일 삭제
                        os.remove(temp_path)
                        
                        # 데이터 새로고침 플래그
                        st.session_state['data_refreshed'] = True
                    else:
                        st.error(f"❌ {result['message']}")
                
                except Exception as e:
                    st.error(f"❌ 업로드 실패: {str(e)}")
    
    st.markdown("---")
    
    # 기존 CSV 데이터 마이그레이션
    st.markdown("### 🔄 데이터 마이그레이션")
    
    csv_path = 'data/user_expenses.csv'
    
    if os.path.exists(csv_path):
        st.info("💾 기존 CSV 데이터 발견!")
        
        if st.button("📥 CSV → SQLite 이동", use_container_width=True):
            with st.spinner('마이그레이션 중...'):
                result = db.import_from_csv(csv_path)
                
                if result['success']:
                    st.success(result['message'])
                    
                    # CSV 백업
                    backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                    os.rename(csv_path, f'data/{backup_name}')
                    
                    st.info(f"✅ 기존 CSV는 {backup_name}로 백업됨")
                    st.balloons()
                    st.session_state['data_refreshed'] = True
                    st.rerun()
                else:
                    st.error(result['message'])
    
    st.markdown("---")
    
    # AI 설정
    st.header("🤖 AI 설정")
    use_ai = st.checkbox("AI 자동 분류", value=False)
    
    st.markdown("---")
    
    # 빠른 거래 입력
    st.markdown("### ⚡ 빠른 거래 입력")
    
    with st.expander("➕ 새 거래 추가", expanded=False):
        with st.form("quick_add_transaction", clear_on_submit=True):
            add_date = st.date_input("날짜", value=datetime.now())
            
            add_desc = st.text_input("적요", placeholder="예: 스타벅스")
            
            col_amount, col_type = st.columns([2, 1])
            
            with col_amount:
                add_amount = st.number_input("금액", min_value=0, step=1000)
            
            with col_type:
                add_type = st.selectbox("구분", ["지출", "수입"])
            
            # AI 자동 분류
            if use_ai and add_desc:
                predicted_cat = managers['classifier'].predict(add_desc)
                add_category = st.text_input("카테고리", value=predicted_cat)
            else:
                categories = managers['category_manager'].get_all_categories()
                add_category = st.selectbox("카테고리", options=categories)
            
            add_memo = st.text_input("메모 (선택)", placeholder="추가 메모")
            
            submitted = st.form_submit_button("💾 추가", use_container_width=True)
            
            if submitted:
                if not add_desc or add_amount == 0:
                    st.error("❌ 적요와 금액을 입력해주세요")
                else:
                    try:
                        final_amount = -add_amount if add_type == "지출" else add_amount
                        
                        # SQLite에 저장
                        result = db.add_transaction(
                            date=add_date.strftime('%Y-%m-%d'),
                            description=add_desc,
                            amount=final_amount,
                            category=add_category,
                            memo=add_memo
                        )
                        
                        if result['success']:
                            st.success("✅ 저장됨!")
                            st.session_state['data_refreshed'] = True
                            st.rerun()
                        else:
                            st.error(result['message'])
                    
                    except Exception as e:
                        st.error(f"❌ 저장 실패: {str(e)}")
    
    st.markdown("---")
    
    # 데이터베이스 정보
    with st.expander("💾 데이터베이스 정보", expanded=False):
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM transactions")
        total_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT date FROM transactions ORDER BY date DESC LIMIT 1")
        recent = cursor.fetchone()
        recent_date = recent[0] if recent else "-"
        
        conn.close()
        
        st.caption(f"📊 총 거래: {total_count}건")
        st.caption(f"📅 최근: {recent_date}")
        st.caption(f"📁 위치: data/expense.db")
        
        # 백업
        if st.button("🗄️ 백업", use_container_width=True):
            result = db.create_backup()
            if result['success']:
                st.success("✅ 백업 완료")
                st.caption(f"📁 {result['path']}")
            else:
                st.error(result['message'])
# ===== 메인 영역 =====

st.markdown("---")

# 데이터 로드
@st.cache_data(ttl=60)  # 60초 캐시
def load_data_from_db():
    """SQLite에서 데이터 로드 (캐싱)"""
    df_raw = db.get_all_transactions()
    
    if df_raw.empty:
        return pd.DataFrame()
    
    # 전처리
    df = df_raw.copy()
    
    if '날짜' not in df.columns and 'date' in df.columns:
        df['날짜'] = pd.to_datetime(df['date'])
        df['적요'] = df['description']
        df['금액'] = df['amount']
        df['분류'] = df['category']
        df['메모'] = df.get('memo', '')
    
    df['년월'] = df['날짜'].dt.to_period('M').astype(str)
    df['구분'] = df['금액'].apply(lambda x: '수입' if x > 0 else '지출')
    df['금액_절대값'] = df['금액'].abs()
    
    return df

try:
    # 데이터 새로고침이 필요하면 캐시 무효화
    if st.session_state.get('data_refreshed', False):
        st.cache_data.clear()
        st.session_state['data_refreshed'] = False
    
    # 데이터 로드
    df = load_data_from_db()
    
    if df.empty:
        st.info("📝 데이터가 없습니다")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 1️⃣ 샘플 데이터로 시작")
            if st.button("🚀 샘플 데이터 로드", type="primary", use_container_width=True):
                sample_path = 'data/sample.csv'
                
                if os.path.exists(sample_path):
                    result = db.import_from_csv(sample_path)
                    if result['success']:
                        st.success(result['message'])
                        st.session_state['data_refreshed'] = True
                        st.rerun()
                    else:
                        st.error(result['message'])
                else:
                    st.error("샘플 파일이 없습니다")
        
        with col2:
            st.markdown("### 2️⃣ 파일 업로드")
            st.info("👈 왼쪽 사이드바에서 CSV/Excel 파일을 업로드하세요")
        
        st.stop()
    
    # AI 자동 분류 (필요 시)
    if use_ai and '분류' in df.columns:
        missing_category = df['분류'].isna() | (df['분류'] == '기타')
        
        if missing_category.any():
            with st.spinner('🤖 AI 분류 중...'):
                df_ai = managers['classifier'].auto_categorize_dataframe(df[missing_category])
                
                if '분류_AI' in df_ai.columns:
                    df.loc[missing_category, '분류'] = df_ai['분류_AI'].values
                    st.success("✅ AI 분류 완료")
    
    # 상태 표시
    col_status1, col_status2, col_status3 = st.columns(3)
    
    with col_status1:
        st.metric("💾 데이터 소스", "SQLite DB")
    
    with col_status2:
        st.metric("📊 총 거래", f"{len(df)}건")
    
    with col_status3:
        period = f"{df['날짜'].min().strftime('%Y-%m-%d')} ~ {df['날짜'].max().strftime('%Y-%m-%d')}"
        st.metric("📅 기간", period)

except Exception as e:
    st.error(f"❌ 데이터 로드 오류: {str(e)}")
    st.stop()

st.markdown("---")
# ===== 탭 구성 =====
from tabs import (
    dashboard, analysis, monthly_trend, budget, statistics,
    data_explorer, category_tab, validator, ai_learning,
    savings_goal, recurring, prediction, search
)

tabs = st.tabs([
    "📊 대시보드",
    "📈 분석",
    "📅 월별",
    "💰 예산",
    "📉 통계",
    "🔍 검색",
    "⚙️ 설정",
    "🤖 AI",
    "🎯 스마트",
    "📄 리포트"
])

with tabs[0]:
    dashboard.render(df, managers['budget_manager'])

with tabs[1]:
    analysis.render(df)

with tabs[2]:
    monthly_trend.render(df)

with tabs[3]:
    budget.render(df, managers['budget_manager'])

with tabs[4]:
    statistics.render(df)

with tabs[5]:
    subtab1, subtab2 = st.tabs(["🔍 검색", "🗂️ 탐색"])
    
    with subtab1:
        search.render(
            df,
            managers['search_engine'],
            managers['favorites_manager'],
            managers['advanced_filter']
        )
    
    with subtab2:
        data_explorer.render(df)

with tabs[6]:
    subtab1, subtab2 = st.tabs(["📁 카테고리", "✅ 검증"])
    
    with subtab1:
        category_tab.render(df, managers['category_manager'])
    
    with subtab2:
        validator.render(df, managers['data_validator'])

with tabs[7]:
    ai_learning.render(df, managers['classifier'])

with tabs[8]:
    subtab1, subtab2, subtab3 = st.tabs(["🎯 저축 목표", "🔄 반복 거래", "🔮 예측 & 비교"])
    
    with subtab1:
        savings_goal.render(df, managers['savings_goal_manager'])
    
    with subtab2:
        recurring.render(df, managers['recurring_manager'], managers['category_manager'])
    
    with subtab3:
        prediction.render(df, managers['budget_manager'])

with tabs[9]:
    st.subheader("📄 데이터 내보내기")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Excel 내보내기")
        if st.button("📊 통계 Excel 다운로드", use_container_width=True):
            from utils.preprocess import get_statistics
            
            with st.spinner("Excel 생성 중..."):
                stats = get_statistics(df)
                excel_buffer = managers['export_manager'].export_statistics_to_excel(df, stats)
                
                st.download_button(
                    label="📥 Excel 파일 다운로드",
                    data=excel_buffer,
                    file_name=f"expense_statistics_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
    
    with col2:
        st.markdown("### PDF 리포트")
        if st.button("📄 PDF 리포트 생성", use_container_width=True):
            with st.spinner("PDF 생성 중..."):
                try:
                    pdf_buffer = managers['pdf_generator'].generate_report(df, managers['budget_manager'])
                    
                    st.download_button(
                        label="📥 PDF 다운로드",
                        data=pdf_buffer,
                        file_name=f"expense_report_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"PDF 생성 실패: {str(e)}")
    
    st.markdown("---")
    
    # 데이터베이스 백업 다운로드
    st.markdown("### 데이터베이스 백업")
    
    col3, col4 = st.columns(2)
    
    with col3:
        if st.button("💾 SQLite 백업 파일 생성", use_container_width=True):
            result = db.create_backup()
            if result['success']:
                st.success(f"✅ 백업 완료: {result['path']}")
            else:
                st.error(result['message'])
    
    with col4:
        if st.button("📤 CSV로 내보내기", use_container_width=True):
            result = db.export_to_csv('data/full_export.csv')
            if result['success']:
                st.success("✅ data/full_export.csv 생성")
                
                # 다운로드 버튼
                with open('data/full_export.csv', 'rb') as f:
                    st.download_button(
                        label="📥 CSV 다운로드",
                        data=f,
                        file_name=f"expense_export_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
            else:
                st.error(result['message'])

# 푸터
st.markdown("---")
st.caption("💰 Expense Analyzer v3.0 | SQLite 데이터베이스 통합 🚀")