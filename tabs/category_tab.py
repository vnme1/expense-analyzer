"""
카테고리 관리 탭
카테고리 추가, 수정, 삭제, 병합
"""
import streamlit as st
import pandas as pd


def render(df, category_manager):
    """
    카테고리 관리 탭 렌더링
    
    Args:
        df: 거래내역 DataFrame
        category_manager: CategoryManager 인스턴스
    """
    st.subheader("📁 카테고리 관리")
    
    st.markdown("""
    카테고리를 추가, 수정, 삭제하거나 여러 카테고리를 하나로 병합할 수 있습니다.
    """)
    
    st.markdown("---")
    
    # 현재 카테고리 목록
    _render_category_list(df, category_manager)
    
    st.markdown("---")
    
    # 카테고리 관리 기능
    col1, col2, col3 = st.columns(3)
    
    with col1:
        _render_add_category(category_manager)
    
    with col2:
        _render_rename_category(category_manager)
    
    with col3:
        _render_delete_category(category_manager)
    
    st.markdown("---")
    
    # 카테고리 병합
    _render_merge_categories(category_manager)
    
    st.markdown("---")
    
    # 초기화
    _render_reset(category_manager)


def _render_category_list(df, category_manager):
    """현재 카테고리 목록"""
    st.markdown("### 📋 현재 카테고리")
    
    categories = category_manager.get_all_categories()
    cat_stats = category_manager.get_category_statistics(df)
    
    category_usage = []
    for cat in categories:
        usage = cat_stats.get(cat, {'count': 0, 'exists': False})
        category_usage.append({
            '카테고리': cat,
            '사용 건수': usage['count'],
            '상태': '✅ 사용중' if usage['exists'] else '⚪ 미사용'
        })
    
    usage_df = pd.DataFrame(category_usage)
    st.dataframe(usage_df, use_container_width=True, hide_index=True)


def _render_add_category(category_manager):
    """카테고리 추가"""
    st.markdown("### ➕ 카테고리 추가")
    new_category = st.text_input("새 카테고리 이름", key="new_cat")
    
    if st.button("추가", type="primary", use_container_width=True):
        result = category_manager.add_category(new_category)
        if result['success']:
            st.success(result['message'])
            st.rerun()
        else:
            st.error(result['message'])


def _render_rename_category(category_manager):
    """카테고리 이름 변경"""
    st.markdown("### ✏️ 카테고리 이름 변경")
    
    categories = category_manager.get_all_categories()
    old_cat = st.selectbox("변경할 카테고리", categories, key="old_cat")
    new_cat_name = st.text_input("새 이름", key="rename_cat")
    
    if st.button("변경", use_container_width=True):
        result = category_manager.rename_category(old_cat, new_cat_name)
        if result['success']:
            st.success(result['message'])
            st.rerun()
        else:
            st.error(result['message'])


def _render_delete_category(category_manager):
    """카테고리 삭제"""
    st.markdown("### 🗑️ 카테고리 삭제")
    
    categories = category_manager.get_all_categories()
    del_cat = st.selectbox("삭제할 카테고리", categories, key="del_cat")
    
    if st.button("삭제", use_container_width=True):
        result = category_manager.delete_category(del_cat)
        if result['success']:
            st.success(result['message'])
            st.warning(f"⚠️ 기존 '{del_cat}' 데이터는 '기타'로 변경됩니다")
            st.rerun()
        else:
            st.error(result['message'])


def _render_merge_categories(category_manager):
    """카테고리 병합"""
    st.markdown("### 🔀 카테고리 병합")
    st.caption("여러 카테고리를 하나로 합칠 수 있습니다 (예: '외식', '식당' → '식비')")
    
    categories = category_manager.get_all_categories()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        merge_sources = st.multiselect(
            "병합할 카테고리 (여러 개 선택)",
            categories,
            key="merge_sources"
        )
    
    with col2:
        merge_target = st.text_input("→ 통합될 카테고리", key="merge_target")
    
    if st.button("🔀 병합 실행", type="primary"):
        if merge_sources and merge_target:
            result = category_manager.merge_categories(merge_sources, merge_target)
            if result['success']:
                st.success(result['message'])
                st.rerun()
            else:
                st.error(result['message'])
        else:
            st.warning("병합할 카테고리와 대상 카테고리를 모두 입력해주세요")


def _render_reset(category_manager):
    """초기화"""
    st.markdown("### 🔄 기본 카테고리로 초기화")
    st.warning("⚠️ 모든 사용자 정의 카테고리가 삭제되고 기본 카테고리로 복원됩니다")
    
    if st.button("기본값으로 초기화", use_container_width=True):
        result = category_manager.reset_to_default()
        st.success(result['message'])
        st.rerun()