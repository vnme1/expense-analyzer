"""
반복 거래 탭
구독료, 월세 등 주기적 거래 자동 관리
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta


def render(df, recurring_manager, category_manager):
    """
    반복 거래 탭 렌더링
    
    Args:
        df: 거래내역 DataFrame
        recurring_manager: RecurringTransactionManager 인스턴스
        category_manager: CategoryManager 인스턴스
    """
    st.subheader("🔄 반복 거래 관리")
    
    st.markdown("""
    구독료, 월세, 통신비 등 주기적으로 발생하는 거래를 자동으로 관리하세요.
    """)
    
    st.markdown("---")
    
    # 반복 거래 추가
    _render_add_recurring(recurring_manager, category_manager)
    
    st.markdown("---")
    
    # 활성 반복 거래 목록
    active_recurring = recurring_manager.get_active_recurring()
    
    if not active_recurring:
        st.info("📝 등록된 반복 거래가 없습니다. 위에서 추가해보세요!")
    else:
        _render_recurring_list(active_recurring, recurring_manager)
        
        st.markdown("---")
        
        # 향후 30일 미리보기
        _render_upcoming_transactions(recurring_manager)
        
        st.markdown("---")
        
        # 반복 거래 관리
        _render_management(recurring_manager, active_recurring)
        
        st.markdown("---")
        
        # CSV 자동 추가
        _render_auto_add(recurring_manager)


def _render_add_recurring(recurring_manager, category_manager):
    """반복 거래 추가"""
    with st.expander("➕ 반복 거래 추가", expanded=False):
        with st.form("add_recurring_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                rec_name = st.text_input("거래명", placeholder="예: 넷플릭스")
                rec_amount = st.number_input(
                    "금액 (지출은 음수)",
                    value=-14500,
                    step=1000
                    help="지출: 음수, 수입: 양수"
                )
                rec_category = st.selectbox(
                    "카테고리",
                    options=category_manager.get_all_categories()
                )
            
            with col2:
                rec_frequency = st.selectbox(
                    "주기",
                    options=list(recurring_manager.FREQUENCY_TYPES.keys()),
                    format_func=lambda x: recurring_manager.FREQUENCY_TYPES[x]
                )
                
                rec_start = st.date_input("시작 날짜", value=datetime.now())
                
                if rec_frequency == 'monthly':
                    rec_day = st.number_input("매월 실행일 (1-31)", min_value=1, max_value=31, value=5)
                elif rec_frequency == 'weekly':
                    rec_day = st.selectbox(
                        "매주 실행 요일",
                        options=[0,1,2,3,4,5,6],
                        format_func=lambda x: ['월','화','수','목','금','토','일'][x]
                    )
                else:
                    rec_day = 1
            
            rec_memo = st.text_input("메모 (선택)", placeholder="월 구독료")
            
            submitted_rec = st.form_submit_button("💾 반복 거래 추가", use_container_width=True)
            
            if submitted_rec:
                result = recurring_manager.add_recurring(
                    name=rec_name,
                    amount=rec_amount,
                    category=rec_category,
                    frequency=rec_frequency,
                    start_date=rec_start,
                    day_of_execution=rec_day,
                    memo=rec_memo
                )
                
                if result['success']:
                    st.success(result['message'])
                    st.rerun()
                else:
                    st.error(result['message'])


def _render_recurring_list(active_recurring, recurring_manager):
    """반복 거래 목록"""
    st.markdown("### 📋 등록된 반복 거래")
    
    recurring_data = []
    for rec in active_recurring:
        recurring_data.append({
            'ID': rec['id'],
            '거래명': rec['name'],
            '금액': f"{rec['amount']:,.0f}원",
            '카테고리': rec['category'],
            '주기': recurring_manager.FREQUENCY_TYPES[rec['frequency']],
            '시작일': rec['start_date'],
            '상태': '🟢 활성' if rec.get('active', True) else '⚪ 비활성'
        })
    
    recurring_df = pd.DataFrame(recurring_data)
    st.dataframe(recurring_df, use_container_width=True, hide_index=True)


def _render_upcoming_transactions(recurring_manager):
    """향후 30일 미리보기"""
    st.markdown("### 📅 향후 30일 예정 거래")
    
    upcoming = recurring_manager.get_upcoming_transactions(days=30)
    
    if upcoming:
        upcoming_df = pd.DataFrame(upcoming)
        upcoming_df['날짜'] = pd.to_datetime(upcoming_df['날짜']).dt.strftime('%Y-%m-%d')
        
        display_cols = ['날짜', '적요', '금액', '분류']
        st.dataframe(
            upcoming_df[display_cols].style.format({'금액': '{:,.0f}원'}),
            use_container_width=True
        )
        
        total_expense = sum(t['금액'] for t in upcoming if t['금액'] < 0)
        total_income = sum(t['금액'] for t in upcoming if t['금액'] > 0)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("예정 지출", f"{abs(total_expense):,.0f}원")
        with col2:
            st.metric("예정 수입", f"{total_income:,.0f}원")
        with col3:
            st.metric("순예정액", f"{total_income + total_expense:,.0f}원")
    else:
        st.info("향후 30일 동안 예정된 반복 거래가 없습니다")


def _render_management(recurring_manager, active_recurring):
    """반복 거래 관리"""
    st.markdown("### ⚙️ 반복 거래 관리")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**거래 활성/비활성**")
        toggle_id = st.selectbox(
            "거래 선택",
            options=[r['id'] for r in active_recurring],
            format_func=lambda x: next(r['name'] for r in active_recurring if r['id'] == x)
        )
        
        if st.button("🔄 활성/비활성 전환", use_container_width=True):
            result = recurring_manager.toggle_active(toggle_id)
            st.success(result['message'])
            st.rerun()
    
    with col2:
        st.markdown("**거래 삭제**")
        delete_id = st.selectbox(
            "삭제할 거래",
            options=[r['id'] for r in active_recurring],
            format_func=lambda x: next(r['name'] for r in active_recurring if r['id'] == x),
            key="delete_recurring_select"
        )
        
        if st.button("🗑️ 삭제", use_container_width=True):
            result = recurring_manager.delete_recurring(delete_id)
            st.success(result['message'])
            st.rerun()


def _render_auto_add(recurring_manager):
    """CSV 자동 추가"""
    st.markdown("### 📥 CSV 파일에 반복 거래 자동 추가")
    
    col1, col2 = st.columns(2)
    
    with col1:
        auto_start = st.date_input("추가 시작일", value=datetime.now())
    
    with col2:
        auto_end = st.date_input("추가 종료일", value=datetime.now() + timedelta(days=30))
    
    if st.button("📝 user_expenses.csv에 추가", type="primary", use_container_width=True):
        csv_path = 'data/user_expenses.csv'
        result = recurring_manager.auto_add_to_csv(csv_path, auto_start, auto_end)
        
        if result['success']:
            if result['count'] > 0:
                st.success(result['message'])
                st.info("💡 페이지를 새로고침하여 변경사항을 확인하세요")
            else:
                st.info(result['message'])
        else:
            st.error(result['message'])