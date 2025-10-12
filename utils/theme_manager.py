"""
테마 관리 모듈
라이트/다크 모드 설정 및 적용
"""
import streamlit as st
import json
import os
from pathlib import Path


class ThemeManager:
    """테마 관리 클래스"""
    
    LIGHT_THEME = {
        'name': 'light',
        'background': '#ffffff',
        'secondary_bg': '#f8fafc',
        'text': '#1f2937',
        'text_secondary': '#6b7280',
        'border': '#e5e7eb',
        'primary': '#3b82f6',
        'success': '#10b981',
        'warning': '#f59e0b',
        'error': '#ef4444'
    }
    
    DARK_THEME = {
        'name': 'dark',
        'background': '#1a1a1a',
        'secondary_bg': '#2d2d2d',
        'text': '#e5e7eb',
        'text_secondary': '#9ca3af',
        'border': '#374151',
        'primary': '#60a5fa',
        'success': '#34d399',
        'warning': '#fbbf24',
        'error': '#f87171'
    }
    
    def __init__(self, settings_file='data/theme_settings.json'):
        """초기화"""
        self.project_root = Path(__file__).parent.parent
        self.settings_file = self.project_root / settings_file
        self.current_theme = self.load_theme()
    
    def load_theme(self):
        """저장된 테마 로드"""
        if self.settings_file.exists():
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                theme_name = data.get('theme', 'light')
                return self.DARK_THEME if theme_name == 'dark' else self.LIGHT_THEME
        
        return self.LIGHT_THEME
    
    def save_theme(self, theme_name):
        """테마 설정 저장"""
        self.settings_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.settings_file, 'w', encoding='utf-8') as f:
            json.dump({'theme': theme_name}, f, ensure_ascii=False, indent=2)
        
        self.current_theme = self.DARK_THEME if theme_name == 'dark' else self.LIGHT_THEME
    
    def get_theme_name(self):
        """현재 테마명 반환"""
        return self.current_theme['name']
    
    def toggle_theme(self):
        """테마 토글"""
        new_theme = 'dark' if self.current_theme['name'] == 'light' else 'light'
        self.save_theme(new_theme)
        return new_theme
    
    def apply_theme(self):
        """Streamlit에 테마 적용 (CSS 주입)"""
        theme = self.current_theme
        
        # 라이트 모드일 때는 CSS 적용 안 함
        if theme['name'] == 'light':
            return
        
        css = f"""
        <style>
        /* 전역 배경색 */
        .stApp {{
            background-color: {theme['background']};
            color: {theme['text']};
        }}
    
        
        /* 사이드바 */
        section[data-testid="stSidebar"] {{
            background-color: {theme['secondary_bg']};
            border-right: 1px solid {theme['border']};
        }}
        
        /* 카드 스타일 */
        .stMetric {{
            background-color: {theme['secondary_bg']};
            padding: 1rem;
            border-radius: 0.5rem;
            border: 1px solid {theme['border']};
        }}
        
        /* 테이블 */
        .stDataFrame {{
            background-color: {theme['secondary_bg']};
            border: 1px solid {theme['border']};
        }}
        
        /* 버튼 */
        .stButton>button {{
            background-color: {theme['primary']};
            color: white;
            border: none;
        }}
        
        .stButton>button:hover {{
            opacity: 0.9;
        }}
        
        /* 텍스트 입력 */
        .stTextInput>div>div>input {{
            background-color: {theme['secondary_bg']};
            color: {theme['text']};
            border: 1px solid {theme['border']};
        }}
        
        /* 선택 박스 */
        .stSelectbox>div>div>div {{
            background-color: {theme['secondary_bg']};
            color: {theme['text']};
            border: 1px solid {theme['border']};
        }}
        
        /* 탭 */
        .stTabs [data-baseweb="tab-list"] {{
            background-color: {theme['secondary_bg']};
            border-bottom: 1px solid {theme['border']};
        }}
        
        .stTabs [data-baseweb="tab"] {{
            color: {theme['text_secondary']};
        }}
        
        .stTabs [aria-selected="true"] {{
            color: {theme['primary']};
            border-bottom: 2px solid {theme['primary']};
        }}
        
        /* 차트 배경 */
        .js-plotly-plot .plotly {{
            background-color: {theme['secondary_bg']} !important;
        }}
        
        /* 알림 메시지 */
        .stAlert {{
            background-color: {theme['secondary_bg']};
            border: 1px solid {theme['border']};
            color: {theme['text']};
        }}
        
        /* 헤더 */
        h1, h2, h3, h4, h5, h6 {{
            color: {theme['text']};
        }}
        
        /* 일반 텍스트 */
        p, span, div {{
            color: {theme['text']};
        }}
        </style>
        """
        
        st.markdown(css, unsafe_allow_html=True)
    
    def get_plotly_template(self):
        """Plotly 차트용 테마 템플릿"""
        theme = self.current_theme
        
        if theme['name'] == 'dark':
            return 'plotly_dark'
        else:
            return 'plotly_white'