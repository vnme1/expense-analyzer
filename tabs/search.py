"""
검색 탭
전체 검색, 고급 필터, 즐겨찾기 통합
"""
import streamlit as st
import pandas as pd
from datetime import datetime


def render(df, search_engine, favorites_manager, advanced_filter):
    """
    검색 탭 렌더링
    
    Args:
        df: 거래내역 DataFrame
        search_engine: SearchEngine 인스턴스
        favorites_manager: FavoritesManager 인스턴스
        advanced_filter: AdvancedFilter 인스턴스
    """
    st.subheader("🔍 검색 & 즐겨찾기")
    
    # 탭 구성
    subtab1, subtab2, subtab3 = st.tabs(["🔍 검색", "⭐ 즐겨찾기", "🎯 고급 필터"])
    
    with subtab1:
        _render_search(df, search_engine)
    
    with subtab2:
        _render_favorites(favorites_manager)
    
    with subtab3:
        _render_advanced_filter(df, advanced_filter)


def _render_search(df, search_engine):
    """검색 UI"""
    st.markdown("### 🔍 전체 검색")
    
    # 검색 바
    col_search, col_options = st.columns([3, 1])
    
    with col_search:
        query = st.text_input(
            "검색어 입력",
            placeholder="예: 스타벅스, 카페, 식비 등",
            help="적요, 메모, 카테고리에서 검색합니다",
            label_visibility="collapsed"
        )
    
    with col_options:
        search_in = st.multiselect(
            "검색 범위",
            options=['적요', '메모', '분류'],
            default=['적요', '메모', '분류'],
            label_visibility="collapsed"
        )
    
    # 검색 실행
    if query:
        with st.spinner('검색 중...'):
            results = search_engine.search(df, query, search_in)
            
            st.markdown(f"### 📊 검색 결과: {len(results)}건")
            
            if len(results) > 0:
                # 요약 통계
                col_stat1, col_stat2, col_stat3 = st.columns(3)
                
                with col_stat1:
                    total_expense = results[results['구분'] == '지출']['금액_절대값'].sum()
                    st.metric("총 지출", f"{total_expense:,.0f}원")
                
                with col_stat2:
                    total_income = results[results['구분'] == '수입']['금액_절대값'].sum()
                    st.metric("총 수입", f"{total_income:,.0f}원")
                
                with col_stat3:
                    st.metric("거래 건수", f"{len(results)}건")
                
                st.markdown("---")
                
                # 결과 표시
                display_cols = ['날짜', '적요', '금액', '분류', '구분']
                if '메모' in results.columns:
                    display_cols.append('메모')
                
                st.dataframe(
                    results[display_cols].style.format({'금액': '{:,.0f}원'}),
                    use_container_width=True
                )
                
                # CSV 다운로드
                csv = results.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 검색 결과 다운로드 (CSV)",
                    data=csv,
                    file_name=f"search_{query}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            else:
                st.info("검색 결과가 없습니다")
    else:
        st.info("💡 검색어를 입력하면 적요, 메모, 카테고리에서 자동으로 검색됩니다")
        
        # 검색 이력
        history = search_engine.get_search_history()
        if history:
            st.markdown("### 🕐 최근 검색")
            cols = st.columns(5)
            for i, keyword in enumerate(history[:5]):
                with cols[i]:
                    if st.button(f"🔍 {keyword}", use_container_width=True):
                        st.session_state['search_query'] = keyword
                        st.rerun()


def _render_favorites(favorites_manager):
    """즐겨찾기 UI"""
    st.markdown("### ⭐ 즐겨찾기")
    
    favorites = favorites_manager.get_all_favorites()
    
    if not favorites:
        st.info("📝 아직 즐겨찾기가 없습니다. 자주 쓰는 거래를 추가해보세요!")
    else:
        # 빠른 사용 버튼
        st.markdown("#### 🚀 빠른 입력")
        
        most_used = favorites_manager.get_most_used(5)
        
        if most_used:
            cols = st.columns(5)
            for i, fav in enumerate(most_used):
                with cols[i]:
                    button_label = f"{fav['name']}\n{fav['amount']:,.0f}원"
                    if st.button(button_label, key=f"quick_fav_{fav['id']}", use_container_width=True):
                        result = favorites_manager.use_favorite(fav['id'])
                        if result['success']:
                            st.success(f"✅ '{fav['name']}' 거래가 추가되었습니다!")
                            st.caption("💡 새로고침하면 데이터에 반영됩니다")
        
        st.markdown("---")
        
        # 전체 즐겨찾기 목록
        st.markdown("#### 📋 전체 즐겨찾기")
        
        for fav in favorites:
            with st.expander(f"{fav['name']} ({fav['amount']:,.0f}원)", expanded=False):
                col_info, col_btn = st.columns([3, 1])
                
                with col_info:
                    st.write(f"**카테고리:** {fav['category']}")
                    st.write(f"**금액:** {fav['amount']:,.0f}원")
                    if fav.get('memo'):
                        st.write(f"**메모:** {fav['memo']}")
                    st.caption(f"사용 횟수: {fav.get('use_count', 0)}회")
                
                with col_btn:
                    if st.button("✅ 사용", key=f"use_fav_{fav['id']}", use_container_width=True):
                        result = favorites_manager.use_favorite(fav['id'])
                        if result['success']:
                            st.success("거래 추가됨")
                    
                    if st.button("🗑️ 삭제", key=f"del_fav_{fav['id']}", use_container_width=True):
                        favorites_manager.remove_favorite(fav['id'])
                        st.success("삭제됨")
                        st.rerun()
    
    st.markdown("---")
    
    # 즐겨찾기 추가
    st.markdown("### ➕ 즐겨찾기 추가")
    
    with st.form("add_favorite_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            fav_name = st.text_input("거래명", placeholder="예: 스타벅스")
            fav_amount = st.number_input(
                "금액 (지출은 음수)",
                value=-4500,
                step=1000
            )
        
        with col2:
            from utils.category_manager import CategoryManager
            category_manager = CategoryManager()
            fav_category = st.selectbox("카테고리", options=category_manager.get_all_categories())
            fav_memo = st.text_input("메모 (선택)", placeholder="아메리카노")
        
        submitted = st.form_submit_button("⭐ 즐겨찾기 추가", use_container_width=True)
        
        if submitted:
            result = favorites_manager.add_favorite(
                name=fav_name,
                amount=fav_amount,
                category=fav_category,
                memo=fav_memo
            )
            
            if result['success']:
                st.success(result['message'])
                st.rerun()
            else:
                st.error(result['message'])


def _render_advanced_filter(df, advanced_filter):
    """고급 필터 UI"""
    st.markdown("### 🎯 고급 필터")
    
    # 빠른 필터 버튼
    st.markdown("#### ⚡ 빠른 필터")
    
    quick_filters = advanced_filter.get_quick_filters()
    
    cols = st.columns(5)
    for i, qf in enumerate(quick_filters):
        with cols[i]:
            if st.button(f"{qf['icon']} {qf['name']}", key=f"quick_filter_{i}", use_container_width=True):
                st.session_state['current_filter'] = qf['config']
                st.rerun()
    
    st.markdown("---")
    
    # 상세 필터 설정
    st.markdown("#### 🔧 상세 필터 설정")
    
    with st.form("advanced_filter_form"):
        # 날짜 범위
        st.markdown("**📅 날짜 범위**")
        col_date1, col_date2 = st.columns(2)
        
        with col_date1:
            date_from = st.date_input(
                "시작 날짜",
                value=df['날짜'].min()
            )
        
        with col_date2:
            date_to = st.date_input(
                "종료 날짜",
                value=df['날짜'].max()
            )
        
        # 금액 범위
        st.markdown("**💰 금액 범위**")
        col_amount1, col_amount2 = st.columns(2)
        
        with col_amount1:
            amount_min = st.number_input(
                "최소 금액",
                min_value=0,
                value=0,
                step=10000
            )
        
        with col_amount2:
            amount_max = st.number_input(
                "최대 금액",
                min_value=0,
                value=1000000,
                step=10000
            )
        
        # 카테고리
        st.markdown("**📂 카테고리**")
        categories = st.multiselect(
            "선택",
            options=df['분류'].unique().tolist(),
            default=df['분류'].unique().tolist()
        )
        
        # 구분
        st.markdown("**📊 구분**")
        transaction_type = st.radio(
            "선택",
            options=['전체', '수입', '지출'],
            horizontal=True
        )
        
        # 검색어
        st.markdown("**🔍 검색어**")
        filter_query = st.text_input("검색어", placeholder="적요 또는 메모에서 검색")
        
        submitted = st.form_submit_button("🎯 필터 적용", use_container_width=True)
        
        if submitted:
            # 필터 설정 생성
            filter_config = {
                'date_from': date_from,
                'date_to': date_to,
                'amount_min': amount_min if amount_min > 0 else None,
                'amount_max': amount_max if amount_max < 1000000 else None,
                'categories': categories,
                'transaction_type': None if transaction_type == '전체' else transaction_type,
                'query': filter_query if filter_query else None
            }
            
            # 유효성 검사
            validation = advanced_filter.validate_filter(filter_config)
            
            if validation['valid']:
                st.session_state['current_filter'] = filter_config
                st.rerun()
            else:
                for error in validation['errors']:
                    st.error(error)
    
    # 필터 결과 표시
    if 'current_filter' in st.session_state:
        st.markdown("---")
        st.markdown("### 📊 필터 결과")
        
        filter_config = st.session_state['current_filter']
        
        # 필터 요약
        summary = advanced_filter.get_filter_summary(filter_config)
        st.info(f"**현재 필터:** {summary}")
        
        # 필터 적용
        filtered_df = advanced_filter.apply_filter(df, filter_config)
        
        st.markdown(f"**{len(filtered_df)}건의 거래**")
        
        if len(filtered_df) > 0:
            # 요약 통계
            col_s1, col_s2, col_s3 = st.columns(3)
            
            with col_s1:
                total_expense = filtered_df[filtered_df['구분'] == '지출']['금액_절대값'].sum()
                st.metric("총 지출", f"{total_expense:,.0f}원")
            
            with col_s2:
                total_income = filtered_df[filtered_df['구분'] == '수입']['금액_절대값'].sum()
                st.metric("총 수입", f"{total_income:,.0f}원")
            
            with col_s3:
                st.metric("거래 건수", f"{len(filtered_df)}건")
            
            st.markdown("---")
            
            # 데이터 표시
            display_cols = ['날짜', '적요', '금액', '분류', '구분']
            if '메모' in filtered_df.columns:
                display_cols.append('메모')
            
            st.dataframe(
                filtered_df[display_cols].style.format({'금액': '{:,.0f}원'}),
                use_container_width=True
            )
            
            # 필터 저장 & 다운로드
            col_action1, col_action2, col_action3 = st.columns(3)
            
            with col_action1:
                # CSV 다운로드
                csv = filtered_df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 CSV 다운로드",
                    data=csv,
                    file_name=f"filtered_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col_action2:
                # 필터 초기화
                if st.button("🔄 필터 초기화", use_container_width=True):
                    del st.session_state['current_filter']
                    st.rerun()
            
            with col_action3:
                # 필터 저장 (구현 예정)
                st.button("💾 필터 저장", use_container_width=True, disabled=True)
        else:
            st.info("필터 조건에 맞는 거래가 없습니다")