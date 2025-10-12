"""
저축 목표 탭
목표 설정, 진행률 추적, 달성 예측
"""
import streamlit as st
from datetime import datetime, timedelta


def render(df, savings_goal_manager):
    """
    저축 목표 탭 렌더링
    
    Args:
        df: 거래내역 DataFrame
        savings_goal_manager: SavingsGoalManager 인스턴스
    """
    st.subheader("🎯 저축 목표 관리")
    
    st.markdown("""
    장기적인 재무 목표를 설정하고 진행 상황을 추적하세요.
    """)
    
    st.markdown("---")
    
    # 목표 추가
    _render_add_goal(savings_goal_manager)
    
    st.markdown("---")
    
    # 활성 목표 목록
    active_goals = savings_goal_manager.get_active_goals()
    
    if not active_goals:
        st.info("📝 아직 설정된 목표가 없습니다. 위에서 새 목표를 추가해보세요!")
    else:
        _render_goal_list(df, savings_goal_manager)


def _render_add_goal(savings_goal_manager):
    """목표 추가"""
    with st.expander("➕ 새 목표 추가", expanded=False):
        with st.form("add_goal_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                goal_name = st.text_input("목표 이름", placeholder="예: 여행 자금")
                goal_amount = st.number_input("목표 금액 (원)", min_value=0, step=100000, value=3000000)
            
            with col2:
                goal_date = st.date_input(
                    "목표 날짜",
                    value=datetime.now() + timedelta(days=365),
                    min_value=datetime.now()
                )
                goal_desc = st.text_area("설명 (선택)", placeholder="목표에 대한 간단한 설명")
            
            submitted = st.form_submit_button("💾 목표 추가", use_container_width=True)
            
            if submitted:
                result = savings_goal_manager.add_goal(
                    name=goal_name,
                    target_amount=goal_amount,
                    target_date=goal_date,
                    description=goal_desc
                )
                
                if result['success']:
                    st.success(result['message'])
                    st.balloons()
                    st.rerun()
                else:
                    st.error(result['message'])


def _render_goal_list(df, savings_goal_manager):
    """목표 목록"""
    st.markdown("### 📋 현재 목표")
    
    for goal_data in savings_goal_manager.get_all_progress(df):
        goal = goal_data['goal']
        progress = goal_data['progress']
        
        with st.container():
            st.markdown(f"#### {goal['name']}")
            
            if goal.get('description'):
                st.caption(goal['description'])
            
            # 진행률 표시
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "현재 저축액",
                    f"{progress['current_savings']:,.0f}원",
                    f"{progress['progress_rate']:.1f}%"
                )
            
            with col2:
                st.metric(
                    "목표 금액",
                    f"{progress['target_amount']:,.0f}원",
                    f"D-{progress['remaining_days']}"
                )
            
            with col3:
                st.metric("남은 금액", f"{progress['remaining_amount']:,.0f}원")
            
            with col4:
                st.metric("일일 저축 필요액", f"{progress['daily_need']:,.0f}원")
            
            # 프로그레스 바
            st.progress(min(progress['progress_rate'] / 100, 1.0))
            
            # 달성 가능성
            if progress['estimated_date']:
                if progress['is_achievable']:
                    st.success(f"✅ 현재 속도로 {progress['estimated_date'].strftime('%Y-%m-%d')}에 달성 가능합니다!")
                else:
                    st.warning(f"⚠️ 현재 속도로는 {progress['estimated_date'].strftime('%Y-%m-%d')}에 달성됩니다.")
            else:
                st.info("💡 더 많은 데이터가 쌓이면 달성 예측이 표시됩니다")
            
            # 월별 권장 저축액
            monthly_need = savings_goal_manager.suggest_monthly_savings(goal, progress['current_savings'])
            st.info(f"📅 **월별 권장 저축액**: {monthly_need:,.0f}원")
            
            # 관리 버튼
            col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 3])
            
            with col_btn1:
                if progress['progress_rate'] >= 100:
                    if st.button("🎉 완료", key=f"complete_{goal['id']}", use_container_width=True):
                        savings_goal_manager.mark_as_completed(goal['id'])
                        st.success("목표를 달성했습니다! 🎉")
                        st.rerun()
            
            with col_btn2:
                if st.button("🗑️ 삭제", key=f"delete_goal_{goal['id']}", use_container_width=True):
                    savings_goal_manager.delete_goal(goal['id'])
                    st.success("목표가 삭제되었습니다")
                    st.rerun()
            
            st.markdown("---")