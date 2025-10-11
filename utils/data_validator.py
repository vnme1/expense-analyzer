"""
데이터 검증 모듈
업로드된 데이터의 오류, 이상치, 누락 항목 감지
"""
import pandas as pd
import numpy as np


class DataValidator:
    """데이터 검증 클래스"""
    
    def __init__(self):
        """검증 규칙 초기화"""
        self.validation_results = {
            'errors': [],
            'warnings': [],
            'suggestions': []
        }
    
    def validate(self, df):
        """
        전체 데이터 검증 수행
        
        Args:
            df: 검증할 DataFrame
            
        Returns:
            dict: 검증 결과 (errors, warnings, suggestions)
        """
        self.validation_results = {
            'errors': [],
            'warnings': [],
            'suggestions': []
        }
        
        # 필수 컬럼 검사
        self._check_required_columns(df)
        
        # 날짜 검사
        self._check_dates(df)
        
        # 금액 검사
        self._check_amounts(df)
        
        # 중복 검사
        self._check_duplicates(df)
        
        # 이상치 검사
        self._check_outliers(df)
        
        # 누락 항목 검사
        self._check_missing_values(df)
        
        # 카테고리 검사
        self._check_categories(df)
        
        return self.validation_results
    
    def _check_required_columns(self, df):
        """필수 컬럼 검사"""
        required = ['날짜', '금액']
        missing = [col for col in required if col not in df.columns]
        
        if missing:
            self.validation_results['errors'].append({
                'type': 'missing_columns',
                'message': f'필수 컬럼 누락: {", ".join(missing)}',
                'severity': 'critical'
            })
    
    def _check_dates(self, df):
        """날짜 유효성 검사"""
        if '날짜' not in df.columns:
            return
        
        # 미래 날짜 검사
        today = pd.Timestamp.now()
        future_dates = df[df['날짜'] > today]
        
        if len(future_dates) > 0:
            self.validation_results['warnings'].append({
                'type': 'future_dates',
                'message': f'미래 날짜 {len(future_dates)}건 발견',
                'details': future_dates[['날짜', '적요', '금액']].head().to_dict('records'),
                'severity': 'medium'
            })
        
        # 날짜 범위 검사
        date_range = (df['날짜'].max() - df['날짜'].min()).days
        if date_range > 730:  # 2년 이상
            self.validation_results['suggestions'].append({
                'type': 'large_date_range',
                'message': f'데이터 기간이 {date_range}일({date_range//365}년)로 매우 깁니다',
                'suggestion': '기간을 좁혀서 분석하면 더 정확한 인사이트를 얻을 수 있습니다',
                'severity': 'low'
            })
    
    def _check_amounts(self, df):
        """금액 유효성 검사"""
        if '금액' not in df.columns:
            return
        
        # 0원 거래 검사
        zero_amounts = df[df['금액'] == 0]
        if len(zero_amounts) > 0:
            self.validation_results['warnings'].append({
                'type': 'zero_amounts',
                'message': f'금액이 0원인 거래 {len(zero_amounts)}건 발견',
                'details': zero_amounts[['날짜', '적요', '금액']].head().to_dict('records'),
                'severity': 'low'
            })
        
        # 비정상적으로 큰 금액 검사
        expense_df = df[df['금액'] < 0]
        if len(expense_df) > 0:
            mean_expense = expense_df['금액'].abs().mean()
            std_expense = expense_df['금액'].abs().std()
            
            # 평균 + 3*표준편차 이상
            threshold = mean_expense + 3 * std_expense
            large_expenses = expense_df[expense_df['금액'].abs() > threshold]
            
            if len(large_expenses) > 0:
                self.validation_results['warnings'].append({
                    'type': 'large_amounts',
                    'message': f'비정상적으로 큰 금액 {len(large_expenses)}건 발견',
                    'details': large_expenses[['날짜', '적요', '금액']].to_dict('records'),
                    'threshold': f'{threshold:,.0f}원',
                    'severity': 'medium'
                })
    
    def _check_duplicates(self, df):
        """중복 거래 검사"""
        # 날짜, 금액, 적요가 모두 같은 경우
        if '적요' in df.columns:
            duplicates = df[df.duplicated(subset=['날짜', '금액', '적요'], keep=False)]
            
            if len(duplicates) > 0:
                dup_count = len(duplicates) // 2
                self.validation_results['warnings'].append({
                    'type': 'duplicates',
                    'message': f'중복 가능성이 있는 거래 {dup_count}건 발견',
                    'details': duplicates[['날짜', '적요', '금액']].head(10).to_dict('records'),
                    'severity': 'medium',
                    'suggestion': '같은 날짜에 동일한 금액의 거래가 여러 건 있습니다'
                })
    
    def _check_outliers(self, df):
        """이상치 검사 (통계적 방법)"""
        if '금액_절대값' not in df.columns:
            return
        
        expense_df = df[df['구분'] == '지출']
        
        if len(expense_df) > 10:
            Q1 = expense_df['금액_절대값'].quantile(0.25)
            Q3 = expense_df['금액_절대값'].quantile(0.75)
            IQR = Q3 - Q1
            
            # IQR 방법으로 이상치 탐지
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers = expense_df[
                (expense_df['금액_절대값'] < lower_bound) | 
                (expense_df['금액_절대값'] > upper_bound)
            ]
            
            if len(outliers) > 0:
                self.validation_results['suggestions'].append({
                    'type': 'statistical_outliers',
                    'message': f'통계적 이상치 {len(outliers)}건 발견',
                    'details': outliers[['날짜', '적요', '금액']].head(5).to_dict('records'),
                    'severity': 'low',
                    'suggestion': '평소 패턴과 다른 거래입니다. 확인해보세요'
                })
    
    def _check_missing_values(self, df):
        """누락 항목 검사"""
        # 적요 누락
        if '적요' in df.columns:
            missing_desc = df[df['적요'].isna() | (df['적요'] == '')]
            
            if len(missing_desc) > 0:
                self.validation_results['suggestions'].append({
                    'type': 'missing_descriptions',
                    'message': f'적요가 없는 거래 {len(missing_desc)}건',
                    'severity': 'low',
                    'suggestion': '적요를 추가하면 AI 자동 분류가 더 정확해집니다'
                })
        
        # 카테고리 누락
        if '분류' in df.columns:
            missing_cat = df[df['분류'].isna() | (df['분류'] == '') | (df['분류'] == '기타')]
            
            if len(missing_cat) > 0:
                self.validation_results['suggestions'].append({
                    'type': 'missing_categories',
                    'message': f'카테고리가 없거나 "기타"인 거래 {len(missing_cat)}건',
                    'severity': 'low',
                    'suggestion': 'AI 자동 분류 기능을 사용하거나 수동으로 카테고리를 지정하세요'
                })
    
    def _check_categories(self, df):
        """카테고리 일관성 검사"""
        if '분류' not in df.columns:
            return
        
        categories = df['분류'].unique()
        
        # 너무 많은 카테고리
        if len(categories) > 20:
            self.validation_results['suggestions'].append({
                'type': 'too_many_categories',
                'message': f'카테고리가 {len(categories)}개로 너무 많습니다',
                'severity': 'low',
                'suggestion': '카테고리를 병합하면 분석이 더 명확해집니다'
            })
        
        # 비슷한 카테고리 탐지
        similar_pairs = self._find_similar_categories(categories)
        
        if similar_pairs:
            self.validation_results['suggestions'].append({
                'type': 'similar_categories',
                'message': f'비슷한 카테고리 {len(similar_pairs)}쌍 발견',
                'details': similar_pairs,
                'severity': 'low',
                'suggestion': '비슷한 카테고리를 병합하는 것을 고려하세요'
            })
    
    def _find_similar_categories(self, categories):
        """비슷한 카테고리 찾기"""
        similar = []
        categories = [c for c in categories if pd.notna(c) and c != '']
        
        for i, cat1 in enumerate(categories):
            for cat2 in categories[i+1:]:
                # 간단한 유사도 검사 (포함 관계)
                if cat1.lower() in cat2.lower() or cat2.lower() in cat1.lower():
                    similar.append({'cat1': cat1, 'cat2': cat2})
        
        return similar[:5]  # 최대 5개만
    
    def get_summary(self):
        """검증 결과 요약"""
        results = self.validation_results
        
        total_issues = (
            len(results['errors']) + 
            len(results['warnings']) + 
            len(results['suggestions'])
        )
        
        if total_issues == 0:
            return {
                'status': 'excellent',
                'message': '✅ 데이터가 깨끗합니다! 문제가 발견되지 않았습니다',
                'total_issues': 0
            }
        elif len(results['errors']) > 0:
            return {
                'status': 'error',
                'message': f'❌ {len(results["errors"])}개의 심각한 오류가 있습니다',
                'total_issues': total_issues
            }
        elif len(results['warnings']) > 0:
            return {
                'status': 'warning',
                'message': f'⚠️ {len(results["warnings"])}개의 경고가 있습니다',
                'total_issues': total_issues
            }
        else:
            return {
                'status': 'suggestion',
                'message': f'💡 {len(results["suggestions"])}개의 개선 제안이 있습니다',
                'total_issues': total_issues
            }