"""
태그 관리 모듈
거래에 다중 태그 추가 및 태그별 분석
"""
import json
import os
from pathlib import Path
import pandas as pd


class TagManager:
    """태그 관리 클래스"""
    
    # 미리 정의된 태그 (빠른 선택용)
    PRESET_TAGS = [
        '주말', '평일', '회식', '데이트', '가족',
        '필수', '선택', '충동구매', '계획구매',
        '할인', '정가', '온라인', '오프라인',
        '아침', '점심', '저녁', '야식'
    ]
    
    def __init__(self, tags_file='data/transaction_tags.json'):
        """초기화"""
        self.project_root = Path(__file__).parent.parent
        self.tags_file = self.project_root / tags_file
        self.tags_data = self.load_tags()
    
    def load_tags(self):
        """저장된 태그 불러오기"""
        if self.tags_file.exists():
            with open(self.tags_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'transaction_tags': {},  # {transaction_id: [tags]}
            'custom_tags': []        # 사용자 정의 태그
        }
    
    def save_tags(self):
        """태그 저장하기"""
        self.tags_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.tags_file, 'w', encoding='utf-8') as f:
            json.dump(self.tags_data, f, ensure_ascii=False, indent=2)
    
    def add_tag_to_transaction(self, transaction_id, tags):
        """
        거래에 태그 추가
        
        Args:
            transaction_id: 거래 ID (날짜+적요+금액 조합)
            tags: 태그 리스트
            
        Returns:
            dict: 성공 여부
        """
        if not tags:
            return {'success': False, 'message': '태그를 선택해주세요'}
        
        # 태그 정규화 (#제거, 소문자 변환)
        normalized_tags = [self._normalize_tag(tag) for tag in tags]
        
        # 기존 태그에 추가 (중복 제거)
        existing = set(self.tags_data['transaction_tags'].get(transaction_id, []))
        existing.update(normalized_tags)
        
        self.tags_data['transaction_tags'][transaction_id] = list(existing)
        
        # 커스텀 태그 등록
        for tag in normalized_tags:
            if tag not in self.PRESET_TAGS and tag not in self.tags_data['custom_tags']:
                self.tags_data['custom_tags'].append(tag)
        
        self.save_tags()
        
        return {'success': True, 'message': f'{len(normalized_tags)}개 태그가 추가되었습니다'}
    
    def remove_tag_from_transaction(self, transaction_id, tag):
        """거래에서 태그 제거"""
        if transaction_id in self.tags_data['transaction_tags']:
            normalized = self._normalize_tag(tag)
            
            if normalized in self.tags_data['transaction_tags'][transaction_id]:
                self.tags_data['transaction_tags'][transaction_id].remove(normalized)
                self.save_tags()
                return {'success': True, 'message': '태그가 제거되었습니다'}
        
        return {'success': False, 'message': '태그를 찾을 수 없습니다'}
    
    def get_transaction_tags(self, transaction_id):
        """특정 거래의 태그 조회"""
        return self.tags_data['transaction_tags'].get(transaction_id, [])
    
    def get_all_tags(self):
        """모든 태그 조회 (프리셋 + 커스텀)"""
        return sorted(set(self.PRESET_TAGS + self.tags_data['custom_tags']))
    
    def get_popular_tags(self, top_n=10):
        """인기 태그 조회"""
        tag_counts = {}
        
        for tags in self.tags_data['transaction_tags'].values():
            for tag in tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        return [(tag, count) for tag, count in sorted_tags[:top_n]]
    
    def add_tags_to_dataframe(self, df):
        """
        DataFrame에 태그 컬럼 추가
        
        Args:
            df: 거래내역 DataFrame
            
        Returns:
            pd.DataFrame: 태그 컬럼이 추가된 DataFrame
        """
        df_copy = df.copy()
        
        # 거래 ID 생성 (날짜+적요+금액)
        df_copy['transaction_id'] = (
            df_copy['날짜'].astype(str) + '_' +
            df_copy['적요'].astype(str) + '_' +
            df_copy['금액'].astype(str)
        )
        
        # 태그 추가
        df_copy['태그'] = df_copy['transaction_id'].apply(
            lambda x: ', '.join(self.get_transaction_tags(x)) if self.get_transaction_tags(x) else '-'
        )
        
        return df_copy
    
    def filter_by_tags(self, df, tags, match_all=False):
        """
        태그로 거래 필터링
        
        Args:
            df: DataFrame (태그 컬럼 포함)
            tags: 필터링할 태그 리스트
            match_all: True면 모든 태그 포함, False면 하나라도 포함
            
        Returns:
            pd.DataFrame: 필터링된 DataFrame
        """
        if '태그' not in df.columns:
            df = self.add_tags_to_dataframe(df)
        
        normalized_tags = [self._normalize_tag(tag) for tag in tags]
        
        def has_tags(tag_str):
            if tag_str == '-':
                return False
            
            transaction_tags = [t.strip() for t in tag_str.split(',')]
            
            if match_all:
                return all(tag in transaction_tags for tag in normalized_tags)
            else:
                return any(tag in transaction_tags for tag in normalized_tags)
        
        return df[df['태그'].apply(has_tags)]
    
    def get_tag_statistics(self, df):
        """
        태그별 통계
        
        Args:
            df: DataFrame
            
        Returns:
            pd.DataFrame: 태그별 통계
        """
        df_with_tags = self.add_tags_to_dataframe(df)
        
        stats = []
        
        for tag in self.get_all_tags():
            tagged_df = self.filter_by_tags(df_with_tags, [tag])
            
            if len(tagged_df) > 0:
                expense_df = tagged_df[tagged_df['구분'] == '지출']
                
                stats.append({
                    '태그': tag,
                    '거래 건수': len(tagged_df),
                    '총 지출': expense_df['금액_절대값'].sum() if len(expense_df) > 0 else 0,
                    '평균 지출': expense_df['금액_절대값'].mean() if len(expense_df) > 0 else 0
                })
        
        if not stats:
            return pd.DataFrame()
        
        stats_df = pd.DataFrame(stats)
        return stats_df.sort_values('총 지출', ascending=False)
    
    def suggest_tags(self, transaction_text):
        """
        거래 내용 기반 태그 추천
        
        Args:
            transaction_text: 거래 적요
            
        Returns:
            list: 추천 태그
        """
        text_lower = transaction_text.lower()
        suggestions = []
        
        # 키워드 기반 추천
        keywords = {
            '주말': ['토요일', '일요일', '주말'],
            '회식': ['회식', '술', '맥주', '소주', '치맥'],
            '데이트': ['데이트', '영화', '카페'],
            '온라인': ['쿠팡', '네이버', '카카오', '배달'],
            '할인': ['할인', '세일', '특가', '이벤트'],
            '충동구매': ['충동', '갑자기'],
            '필수': ['병원', '약국', '마트', '장보기']
        }
        
        for tag, words in keywords.items():
            if any(word in text_lower for word in words):
                suggestions.append(tag)
        
        return suggestions[:5]  # 최대 5개
    
    def bulk_tag_by_category(self, df, category, tag):
        """
        특정 카테고리의 모든 거래에 태그 일괄 추가
        
        Args:
            df: DataFrame
            category: 카테고리명
            tag: 추가할 태그
            
        Returns:
            dict: 결과
        """
        filtered = df[df['분류'] == category]
        
        count = 0
        for _, row in filtered.iterrows():
            transaction_id = f"{row['날짜']}_{row['적요']}_{row['금액']}"
            result = self.add_tag_to_transaction(transaction_id, [tag])
            if result['success']:
                count += 1
        
        return {'success': True, 'count': count, 'message': f'{count}건에 태그가 추가되었습니다'}
    
    def _normalize_tag(self, tag):
        """태그 정규화 (# 제거, 공백 제거)"""
        return tag.strip().replace('#', '').strip()
    
    def clear_all_tags(self):
        """모든 태그 데이터 삭제"""
        self.tags_data = {
            'transaction_tags': {},
            'custom_tags': []
        }
        self.save_tags()
        return {'success': True, 'message': '모든 태그가 삭제되었습니다'}