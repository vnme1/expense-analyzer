"""
데이터 내보내기 모듈
통계 데이터 Excel 내보내기, 차트 이미지 저장
"""
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO
from datetime import datetime


class ExportManager:
    """데이터 내보내기 클래스"""
    
    def __init__(self):
        """초기화"""
        pass
    
    def export_statistics_to_excel(self, df, stats_dict):
        """
        통계 데이터를 Excel로 내보내기
        
        Args:
            df: 거래내역 DataFrame
            stats_dict: get_statistics()에서 반환된 통계 딕셔너리
            
        Returns:
            BytesIO: Excel 파일 바이너리
        """
        buffer = BytesIO()
        
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            # 시트 1: 요약 통계
            summary_data = {
                '항목': [
                    '총 수입', '총 지출', '순수익', '잔액',
                    '월평균 수입', '월평균 지출', '평균 거래 금액',
                    '최대 지출', '최소 지출', '저축률',
                    '총 거래 건수', '수입 건수', '지출 건수',
                    '카테고리 수', '최다 지출 카테고리', '최대 지출 항목'
                ],
                '값': [
                    f"{stats_dict['총_수입']:,.0f}원",
                    f"{stats_dict['총_지출']:,.0f}원",
                    f"{stats_dict['순수익']:,.0f}원",
                    f"{stats_dict['총_수입'] - stats_dict['총_지출']:,.0f}원",
                    f"{stats_dict['월평균_수입']:,.0f}원",
                    f"{stats_dict['월평균_지출']:,.0f}원",
                    f"{stats_dict['평균_지출']:,.0f}원",
                    f"{stats_dict['최대_지출']:,.0f}원",
                    f"{stats_dict['최소_지출']:,.0f}원",
                    f"{stats_dict['저축률']:.1f}%",
                    f"{stats_dict['총_거래건수']}건",
                    f"{stats_dict['수입_건수']}건",
                    f"{stats_dict['지출_건수']}건",
                    f"{stats_dict['카테고리_수']}개",
                    stats_dict['최다_지출_카테고리'],
                    stats_dict['최대_지출_항목']
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='요약통계', index=False)
            
            # 시트 2: 카테고리별 지출
            expense_df = df[df['구분'] == '지출']
            category_spending = expense_df.groupby('분류')['금액_절대값'].agg([
                ('지출액', 'sum'),
                ('거래건수', 'count'),
                ('평균금액', 'mean'),
                ('최대금액', 'max'),
                ('최소금액', 'min')
            ]).round(0)
            
            total_expense = category_spending['지출액'].sum()
            category_spending['비율(%)'] = (category_spending['지출액'] / total_expense * 100).round(1)
            
            category_spending = category_spending.sort_values('지출액', ascending=False)
            category_spending.to_excel(writer, sheet_name='카테고리별지출')
            
            # 시트 3: 월별 추이
            monthly = df.groupby(['년월', '구분'])['금액_절대값'].sum().unstack(fill_value=0)
            if '수입' not in monthly.columns:
                monthly['수입'] = 0
            if '지출' not in monthly.columns:
                monthly['지출'] = 0
            monthly['잔액'] = monthly['수입'] - monthly['지출']
            monthly.to_excel(writer, sheet_name='월별추이')
            
            # 시트 4: 요일별 지출
            expense_df_copy = expense_df.copy()
            expense_df_copy['요일'] = expense_df_copy['날짜'].dt.day_name()
            weekday_map = {
                'Monday': '월', 'Tuesday': '화', 'Wednesday': '수',
                'Thursday': '목', 'Friday': '금', 'Saturday': '토', 'Sunday': '일'
            }
            expense_df_copy['요일_한글'] = expense_df_copy['요일'].map(weekday_map)
            
            weekday_stats = expense_df_copy.groupby('요일_한글')['금액_절대값'].agg([
                ('총지출', 'sum'),
                ('거래건수', 'count'),
                ('평균지출', 'mean')
            ]).round(0)
            
            weekday_stats.to_excel(writer, sheet_name='요일별지출')
            
            # 시트 5: 전체 거래내역
            export_cols = ['날짜', '적요', '금액', '분류', '구분']
            if '메모' in df.columns:
                export_cols.append('메모')
            
            df[export_cols].to_excel(writer, sheet_name='전체거래내역', index=False)
        
        buffer.seek(0)
        return buffer
    
    def export_chart_to_image(self, fig, width=1200, height=800):
        """
        Plotly 차트를 PNG 이미지로 내보내기
        
        Args:
            fig: Plotly Figure 객체
            width: 이미지 너비
            height: 이미지 높이
            
        Returns:
            BytesIO: PNG 이미지 바이너리
        """
        try:
            img_bytes = fig.to_image(
                format="png",
                width=width,
                height=height,
                engine="kaleido"
            )
            return BytesIO(img_bytes)
        except Exception as e:
            print(f"차트 내보내기 오류: {e}")
            return None
    
    def create_comprehensive_excel(self, df, stats_dict, budget_manager=None):
        """
        종합 분석 Excel 파일 생성 (예산 포함)
        
        Args:
            df: 거래내역 DataFrame
            stats_dict: 통계 딕셔너리
            budget_manager: BudgetManager 객체 (선택)
            
        Returns:
            BytesIO: Excel 파일 바이너리
        """
        buffer = BytesIO()
        
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            # 기본 통계 시트들
            self._write_basic_stats(writer, df, stats_dict)
            
            # 예산 시트 (예산이 있는 경우)
            if budget_manager and budget_manager.budgets:
                self._write_budget_analysis(writer, df, budget_manager)
        
        buffer.seek(0)
        return buffer
    
    def _write_basic_stats(self, writer, df, stats_dict):
        """기본 통계 시트 작성"""
        # 요약 통계
        summary_data = {
            '지표': [
                '분석 기간',
                '총 수입', '총 지출', '순수익',
                '월평균 수입', '월평균 지출',
                '저축률', '총 거래 건수'
            ],
            '값': [
                f"{df['날짜'].min().strftime('%Y-%m-%d')} ~ {df['날짜'].max().strftime('%Y-%m-%d')}",
                f"{stats_dict['총_수입']:,.0f}",
                f"{stats_dict['총_지출']:,.0f}",
                f"{stats_dict['순수익']:,.0f}",
                f"{stats_dict['월평균_수입']:,.0f}",
                f"{stats_dict['월평균_지출']:,.0f}",
                f"{stats_dict['저축률']:.1f}%",
                f"{stats_dict['총_거래건수']}"
            ]
        }
        pd.DataFrame(summary_data).to_excel(writer, sheet_name='📊요약', index=False)
        
        # 카테고리별 지출
        expense_df = df[df['구분'] == '지출']
        category_df = expense_df.groupby('분류')['금액_절대값'].agg([
            ('지출액', 'sum'),
            ('건수', 'count'),
            ('평균', 'mean')
        ]).sort_values('지출액', ascending=False)
        
        category_df['비율(%)'] = (category_df['지출액'] / category_df['지출액'].sum() * 100).round(1)
        category_df.to_excel(writer, sheet_name='📈카테고리')
        
        # 월별 추이
        monthly = df.groupby(['년월', '구분'])['금액_절대값'].sum().unstack(fill_value=0)
        if '수입' not in monthly.columns:
            monthly['수입'] = 0
        if '지출' not in monthly.columns:
            monthly['지출'] = 0
        monthly['잔액'] = monthly['수입'] - monthly['지출']
        monthly.to_excel(writer, sheet_name='📅월별')
    
    def _write_budget_analysis(self, writer, df, budget_manager):
        """예산 분석 시트 작성"""
        analysis = budget_manager.analyze_spending(df)
        
        if not analysis.empty:
            analysis.to_excel(writer, sheet_name='💰예산현황', index=False)
    
    def get_filename_with_timestamp(self, prefix='expense_data'):
        """타임스탬프가 포함된 파일명 생성"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{prefix}_{timestamp}"