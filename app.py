"""Expense Analyzer"""
import streamlit as st
from io import BytesIO
import os
import pandas as pd
from datetime import datetime
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
from utils.auto_save import AutoSaveManager
from utils.search_engine import SearchEngine
from utils.favorites_manager import FavoritesManager
from utils.advanced_filter import AdvancedFilter
from tabs import search

st.set_page_config(page_title="Expense Analyzer", page_icon="💰", layout="wide")

if 'uploaded_file_data' not in st.session_state:
    st.session_state['uploaded_file_data'] = None
if 'uploaded_file_name' not in st.session_state:
    st.session_state['uploaded_file_name'] = None
if 'use_sample' not in st.session_state:
    st.session_state['use_sample'] = False

@st.cache_resource
def get_managers():
    classifier = CategoryClassifier()
    classifier.load_model()
    return {
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
        'auto_save': AutoSaveManager(),
        'search_engine': SearchEngine(),
        'favorites_manager': FavoritesManager(),
        'advanced_filter': AdvancedFilter()
    }

managers = get_managers()
theme_manager = managers['theme_manager']
auto_save = managers['auto_save']

if theme_manager.get_theme_name() == 'dark':
    theme_manager.apply_theme()

st.title("💰 개인 가계부 분석기")

with st.sidebar:
    st.header("📂 파일 업로드")
    uploaded_file = st.file_uploader("CSV/Excel", type=['csv', 'xlsx', 'xls'])
    if uploaded_file:
        st.session_state['uploaded_file_data'] = uploaded_file.getvalue()
        st.session_state['uploaded_file_name'] = uploaded_file.name
    
    # 저장된 데이터 정보 표시
    if auto_save.has_saved_data():
        info = auto_save.get_data_info()
        if info:
            with st.expander("💾 저장된 데이터", expanded=False):
                st.caption(f"📊 {info['record_count']}건")
                st.caption(f"📅 {info['date_range']}")
                st.caption(f"🕐 {info['last_modified']}")
                
                if st.button("🔄 저장된 데이터 사용", use_container_width=True):
                    st.session_state['use_saved'] = True
                    st.rerun()
    
    st.markdown("---")
    use_ai = st.checkbox("AI 자동 분류", value=False)
    
    st.markdown("---")
    st.markdown("### ⚡ 빠른 거래 입력")
    
    with st.expander("➕ 새 거래 추가", expanded=False):
        with st.form("quick_add_transaction", clear_on_submit=True):
            add_date = st.date_input(
                "날짜",
                value=datetime.now(),
                help="거래 날짜를 선택하세요"
            )
            
            add_desc = st.text_input(
                "적요",
                placeholder="예: 스타벅스",
                help="거래 내역 설명"
            )
            
            col_amount, col_type = st.columns([2, 1])
            
            with col_amount:
                add_amount = st.number_input(
                    "금액",
                    min_value=0,
                    step=1000,
                    help="거래 금액 (양수로 입력)"
                )
            
            with col_type:
                add_type = st.selectbox(
                    "구분",
                    options=["지출", "수입"]
                )
            
            if use_ai and add_desc:
                predicted_cat = managers['classifier'].predict(add_desc)
                add_category = st.text_input("카테고리", value=predicted_cat)
            else:
                categories = managers['category_manager'].get_all_categories()
                add_category = st.selectbox("카테고리", options=categories)
            
            add_memo = st.text_input(
                "메모 (선택)",
                placeholder="추가 메모",
                help="선택사항"
            )
            
            submitted = st.form_submit_button("💾 거래 추가", use_container_width=True)
            
            if submitted:
                if not add_desc or add_amount == 0:
                    st.error("❌ 적요와 금액을 입력해주세요")
                else:
                    try:
                        final_amount = -add_amount if add_type == "지출" else add_amount
                        
                        new_row = pd.DataFrame({
                            '날짜': [add_date],
                            '적요': [add_desc],
                            '금액': [final_amount],
                            '분류': [add_category],
                            '메모': [add_memo]
                        })
                        
                        existing_df = auto_save.load_saved_data()
                        if existing_df is not None:
                            updated_df = pd.concat([existing_df, new_row], ignore_index=True)
                        else:
                            updated_df = new_row
                        
                        result = auto_save.save_data(updated_df)
                        
                        if result['success']:
                            st.success("✅ 거래가 추가되었습니다!")
                            auto_save.create_backup()
                            st.rerun()
                        else:
                            st.error(result['message'])
                        
                    except Exception as e:
                        st.error(f"❌ 저장 실패: {str(e)}")
    
    # 백업 관리
    st.markdown("---")
    with st.expander("🗄️ 백업 관리", expanded=False):
        backups = auto_save.get_backup_list()
        
        if backups:
            st.caption(f"백업 파일: {len(backups)}개")
            
            for backup in backups[:5]:
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.caption(f"📁 {backup['date']}")
                
                with col2:
                    if st.button("복원", key=f"restore_{backup['filename']}", use_container_width=True):
                        result = auto_save.restore_from_backup(backup['filename'])
                        if result['success']:
                            st.success(result['message'])
                            st.rerun()
                        else:
                            st.error(result['message'])
                
                with col3:
                    if st.button("삭제", key=f"delete_{backup['filename']}", use_container_width=True):
                        result = auto_save.delete_backup(backup['filename'])
                        if result['success']:
                            st.success(result['message'])
                            st.rerun()
                        else:
                            st.error(result['message'])
        else:
            st.info("백업 파일이 없습니다")
        
        if st.button("💾 지금 백업 생성", use_container_width=True):
            result = auto_save.create_backup()
            if result['success']:
                if not result.get('skipped'):
                    st.success(result['message'])
                else:
                    st.info(result['message'])
            else:
                st.error(result['message'])

if uploaded_file is None and st.session_state['uploaded_file_data'] is None:
    if st.session_state.get('use_saved') or auto_save.has_saved_data():
        st.info("💾 저장된 데이터를 불러왔습니다")
    else:
        st.info("파일을 업로드해주세요")
        if st.button("샘플 데이터로 체험"):
            st.session_state['use_sample'] = True
            st.rerun()
        st.stop()

try:
    if st.session_state.get('use_sample') and uploaded_file is None:
        with open('data/sample.csv', 'r', encoding='utf-8-sig') as f:
            df = load_data(f)
        st.success(f"✅ 샘플 데이터 ({len(df)}건)")
    
    elif uploaded_file or st.session_state['uploaded_file_data']:
        if uploaded_file:
            uploaded_df = load_data(uploaded_file)
        else:
            file_data = BytesIO(st.session_state['uploaded_file_data'])
            file_data.name = st.session_state['uploaded_file_name']
            uploaded_df = load_data(file_data)
        
        # 병합
        df = auto_save.merge_data(uploaded_df)
        
        # 저장 후 다시 load_data로 처리 (타입 변환)
        auto_save.save_data(df)
        
        # 🔥 수정: 저장된 파일을 다시 load_data로 읽기
        with open('data/user_expenses.csv', 'r', encoding='utf-8-sig') as f:
            df = load_data(f)
        
        st.success(f"✅ {len(df)}건 로드 (병합 및 저장 완료)")
    
    elif auto_save.has_saved_data():
        # 🔥 수정: 직접 load_data로 읽기
        with open('data/user_expenses.csv', 'r', encoding='utf-8-sig') as f:
            df = load_data(f)
        st.success(f"✅ 저장된 데이터 ({len(df)}건)")
    
    else:
        st.error("데이터를 찾을 수 없습니다")
        st.stop()
    
    if use_ai:
        with st.spinner('🤖 AI가 카테고리를 분석 중입니다...'):
            df = managers['classifier'].auto_categorize_dataframe(df)
            
            if '분류_AI' in df.columns:
                df['분류'] = df['분류_AI']
                st.success(f"✅ AI 분류 완료")
            else:
                st.warning("⚠️ AI 분류에 실패했습니다")
        
except Exception as e:
    st.error(f"오류: {e}")
    st.stop()

from tabs import dashboard, analysis, monthly_trend, budget, statistics, data_explorer, category_tab, validator, ai_learning, savings_goal, recurring, prediction

tabs = st.tabs(["📊 대시보드", "📈 분석", "📅 월별", "💰 예산", "📉 통계", "🔍 탐색", "📁 카테고리", "✅ 검증", "🤖 AI", "🎯 저축", "🔄 반복", "🔮 예측", "🔍 검색"])

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
    data_explorer.render(df)
with tabs[6]:
    category_tab.render(df, managers['category_manager'])
with tabs[7]:
    validator.render(df, managers['data_validator'])
with tabs[8]:
    ai_learning.render(df, managers['classifier'])
with tabs[9]:
    savings_goal.render(df, managers['savings_goal_manager'])
with tabs[10]:
    recurring.render(df, managers['recurring_manager'], managers['category_manager'])
with tabs[11]:
    prediction.render(df, managers['budget_manager'])

st.caption("Expense Analyzer v2.5 | 💾 자동 저장 활성화")