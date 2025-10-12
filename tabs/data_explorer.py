"""
데이터 탐색 탭
필터링, 정렬, 빠른 필터, 편집 모드
"""
import streamlit as st
import pandas as pd
import os


def render(df):
    """
    데이터 탐색 탭 렌더링
    
    Args:
        df: 거래내역 DataFrame
    """
    st.subheader("🔍 원본 데이터 탐색")
    
    # 빠른 필터
    filtered_quick = _render_quick_filters(df)
    
    st.markdown("---")
    
    # 상세 필터
    st.markdown("### 🔧 상세 필터")
    filtered_df = _render_detailed_filters(filtered_quick)
    
    # 정렬
    sorted_df = _render_sorting(filtered_df)
    
    st.markdown(f"**{len(sorted_df)}건의 거래 내역**")
    
    # 편집 모드
    _render_data_table(sorted_df)
    
    # CSV 다운로드
    csv = sorted_df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="📥 필터링된 데이터 다운로드 (CSV)",
        data=csv,
        file_name="filtered_expense.csv",
        mime="text/csv"
    )


def _render_quick_filters(df):
    """빠른 필터"""
    st.markdown("### ⭐ 빠른 필터")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("📅 이번 달", use_container_width=True):
            st.session_state['quick_filter'] = {
                'type': 'month',
                'value': pd.Timestamp.now().strftime('%Y-%m')
            }
    
    with col2:
        if st.button("☕ 카페 지출", use_container_width=True):
            st.session_state['quick_filter'] = {
                'type': 'category',
                'value': '카페'
            }
    
    with col3:
        if st.button("🍔 식비 전체", use_container_width=True):
            st.session_state['quick_filter'] = {
                'type': 'category',
                'value': '식비'
            }
    
    with col4:
        if st.button("💳 고액 거래", use_container_width=True):
            st.session_state['quick_filter'] = {
                'type': 'amount',
                'value': 100000
            }
    
    with col5:
        if st.button("🔄 초기화", use_container_width=True):
            st.session_state['quick_filter'] = None
    
    # 필터 적용
    if 'quick_filter' in st.session_state and st.session_state['quick_filter']:
        filter_info = st.session_state['quick_filter']
        
        if filter_info['type'] == 'month':
            filtered = df[df['년월'] == filter_info['value']]
            st.info(f"📅 필터 적용: {filter_info['value']} ({len(filtered)}건)")
        elif filter_info['type'] == 'category':
            filtered = df[df['분류'] == filter_info['value']]
            st.info(f"📂 필터 적용: {filter_info['value']} ({len(filtered)}건)")
        elif filter_info['type'] == 'amount':
            filtered = df[df['금액_절대값'] >= filter_info['value']]
            st.info(f"💰 필터 적용: {filter_info['value']:,}원 이상 ({len(filtered)}건)")
        else:
            filtered = df
        
        return filtered
    
    return df


def _render_detailed_filters(df):
    """상세 필터"""
    col1, col2 = st.columns(2)
    
    with col1:
        available_categories = df['분류'].unique()
        filter_category = st.multiselect(
            "카테고리 필터",
            options=available_categories,
            default=available_categories
        )
    
    with col2:
        filter_type = st.multiselect(
            "구분 필터",
            options=['수입', '지출'],
            default=['수입', '지출']
        )
    
    filtered = df[
        (df['분류'].isin(filter_category)) & 
        (df['구분'].isin(filter_type))
    ]
    
    return filtered


def _render_sorting(df):
    """정렬"""
    sort_column = st.selectbox(
        "정렬 기준",
        options=['날짜', '금액_절대값', '분류'],
        index=0
    )
    
    sort_order = st.radio("정렬 순서", ['내림차순', '오름차순'], horizontal=True)
    ascending = (sort_order == '오름차순')
    
    return df.sort_values(sort_column, ascending=ascending)


def _render_data_table(df):
    """데이터 테이블 (편집 모드 포함)"""
    col_edit1, col_edit2 = st.columns([1, 4])
    
    with col_edit1:
        edit_mode = st.checkbox("✏️ 편집 모드", help="메모를 직접 수정할 수 있습니다")
    
    with col_edit2:
        if edit_mode:
            st.info("💡 메모 칸을 더블클릭하여 수정한 후 엔터를 누르세요")
    
    display_cols = ['날짜', '적요', '금액', '분류', '구분']
    if '분류_AI' in df.columns:
        display_cols.append('분류_AI')
    if '메모' in df.columns:
        display_cols.append('메모')
    
    if edit_mode and '메모' in df.columns:
        edited_df = st.data_editor(
            df[display_cols],
            use_container_width=True,
            num_rows="fixed",
            disabled=(['날짜', '적요', '금액', '분류', '구분', '분류_AI'] if '분류_AI' in display_cols else ['날짜', '적요', '금액', '분류', '구분']),
            column_config={
                "날짜": st.column_config.DateColumn(
                    "날짜",
                    format="YYYY-MM-DD",
                ),
                "금액": st.column_config.NumberColumn(
                    "금액",
                    format="%d원",
                ),
                "메모": st.column_config.TextColumn(
                    "메모",
                    help="더블클릭하여 수정",
                    max_chars=100,
                )
            },
            key="editable_table"
        )
        
        col_save1, col_save2 = st.columns([1, 4])
        
        with col_save1:
            if st.button("💾 변경사항 저장", type="primary", use_container_width=True):
                try:
                    csv_path = 'data/user_expenses.csv'
                    os.makedirs('data', exist_ok=True)
                    edited_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                    st.success("✅ 저장되었습니다!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 저장 실패: {str(e)}")
        
        with col_save2:
            st.caption("⚠️ 저장하지 않으면 변경사항이 사라집니다")
    
    else:
        st.dataframe(
            df[display_cols].style.format({'금액': '{:,.0f}원'}),
            use_container_width=True
        )