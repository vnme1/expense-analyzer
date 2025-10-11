"""
PDF 리포트 생성 모듈 (한글 지원)
월간 가계부 분석 리포트를 PDF로 자동 생성
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO
import tempfile
import os
import platform


class PDFReportGenerator:
    """PDF 리포트 생성 클래스 (한글 지원)"""
    
    def __init__(self):
        """스타일 초기화 및 한글 폰트 설정"""
        self.styles = getSampleStyleSheet()
        self._register_korean_font()
        self._setup_custom_styles()
    
    def _register_korean_font(self):
        """한글 폰트 등록"""
        try:
            system = platform.system()
            
            # 시스템별 기본 한글 폰트 경로
            font_paths = {
                'Windows': [
                    'C:/Windows/Fonts/malgun.ttf',  # 맑은 고딕
                    'C:/Windows/Fonts/gulim.ttc',   # 굴림
                ],
                'Darwin': [  # macOS
                    '/System/Library/Fonts/AppleSDGothicNeo.ttc',
                    '/Library/Fonts/AppleGothic.ttf',
                ],
                'Linux': [
                    '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',
                    '/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf',
                ]
            }
            
            # 폰트 등록 시도
            for font_path in font_paths.get(system, []):
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont('Korean', font_path))
                        self.korean_font = 'Korean'
                        print(f"✅ 한글 폰트 등록 성공: {font_path}")
                        return
                    except:
                        continue
            
            # 폰트를 찾지 못한 경우 기본 폰트 사용
            print("⚠️ 한글 폰트를 찾을 수 없습니다. Helvetica 사용 (한글이 깨질 수 있습니다)")
            self.korean_font = 'Helvetica'
            
        except Exception as e:
            print(f"⚠️ 폰트 등록 오류: {e}")
            self.korean_font = 'Helvetica'
    
    def _setup_custom_styles(self):
        """커스텀 스타일 설정"""
        # 제목 스타일
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f2937'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName=self.korean_font
        )
        
        # 부제목 스타일
        self.subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#4b5563'),
            spaceAfter=20,
            alignment=TA_LEFT,
            fontName=self.korean_font
        )
        
        # 본문 스타일
        self.body_style = ParagraphStyle(
            'CustomBody',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#374151'),
            alignment=TA_LEFT,
            fontName=self.korean_font
        )
    
    def generate_report(self, df, budget_manager=None):
        """
        월간 리포트 생성
        
        Args:
            df: 거래내역 DataFrame
            budget_manager: BudgetManager 객체 (선택)
            
        Returns:
            BytesIO: PDF 파일 바이너리
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            topMargin=2*cm,
            bottomMargin=2*cm,
            leftMargin=2*cm,
            rightMargin=2*cm
        )
        
        story = []
        
        # 1. 표지
        story.extend(self._create_cover(df))
        
        # 2. 요약 지표
        story.extend(self._create_summary(df))
        story.append(Spacer(1, 1*cm))
        
        # 3. 카테고리별 지출
        story.extend(self._create_category_analysis(df))
        story.append(Spacer(1, 1*cm))
        
        # 4. 월별 추이
        story.extend(self._create_monthly_trend(df))
        story.append(PageBreak())
        
        # 5. 예산 현황 (있는 경우)
        if budget_manager and budget_manager.budgets:
            story.extend(self._create_budget_status(df, budget_manager))
            story.append(Spacer(1, 1*cm))
        
        # 6. 상세 거래 내역
        story.extend(self._create_transaction_list(df))
        
        # 7. 푸터
        story.extend(self._create_footer())
        
        # PDF 생성
        doc.build(story)
        buffer.seek(0)
        
        return buffer
    
    def _create_cover(self, df):
        """표지 생성"""
        story = []
        
        story.append(Paragraph("월간 지출 리포트", self.title_style))
        story.append(Spacer(1, 0.5*cm))
        
        start_date = df['날짜'].min().strftime('%Y-%m-%d')
        end_date = df['날짜'].max().strftime('%Y-%m-%d')
        
        period_text = f"분석 기간: {start_date} ~ {end_date}"
        story.append(Paragraph(period_text, self.body_style))
        story.append(Spacer(1, 0.3*cm))
        
        generated_text = f"생성 일시: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        story.append(Paragraph(generated_text, self.body_style))
        story.append(Spacer(1, 2*cm))
        
        return story
    
    def _create_summary(self, df):
        """요약 지표 생성"""
        story = []
        
        story.append(Paragraph("요약", self.subtitle_style))
        
        total_income = df[df['구분'] == '수입']['금액_절대값'].sum()
        total_expense = df[df['구분'] == '지출']['금액_절대값'].sum()
        balance = total_income - total_expense
        
        data = [
            ['항목', '금액'],
            ['총 수입', f'{total_income:,.0f}원'],
            ['총 지출', f'{total_expense:,.0f}원'],
            ['잔액', f'{balance:,.0f}원'],
            ['거래 건수', f'{len(df)}건']
        ]
        
        table = Table(data, colWidths=[8*cm, 8*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), self.korean_font),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))
        
        story.append(table)
        
        return story
    
    def _create_category_analysis(self, df):
        """카테고리별 분석"""
        story = []
        
        story.append(Paragraph("카테고리별 분석", self.subtitle_style))
        
        expense_df = df[df['구분'] == '지출']
        category_summary = expense_df.groupby('분류')['금액_절대값'].sum().sort_values(ascending=False)
        
        if category_summary.empty:
            story.append(Paragraph("지출 데이터가 없습니다", self.body_style))
            return story
        
        chart_buffer = self._create_pie_chart(category_summary)
        
        if chart_buffer:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
                tmp.write(chart_buffer.getvalue())
                tmp_path = tmp.name
            
            img = Image(tmp_path, width=14*cm, height=10*cm)
            story.append(img)
            
            try:
                os.unlink(tmp_path)
            except:
                pass
        
        story.append(Spacer(1, 0.5*cm))
        
        total = category_summary.sum()
        data = [['카테고리', '금액', '비율']]
        
        for cat, amount in category_summary.items():
            percentage = (amount / total * 100) if total > 0 else 0
            data.append([cat, f'{amount:,.0f}원', f'{percentage:.1f}%'])
        
        table = Table(data, colWidths=[6*cm, 5*cm, 5*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), self.korean_font),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        
        return story
    
    def _create_monthly_trend(self, df):
        """월별 추이"""
        story = []
        
        story.append(Paragraph("월별 추이", self.subtitle_style))
        
        monthly = df.groupby(['년월', '구분'])['금액_절대값'].sum().unstack(fill_value=0)
        
        if '수입' not in monthly.columns:
            monthly['수입'] = 0
        if '지출' not in monthly.columns:
            monthly['지출'] = 0
        
        chart_buffer = self._create_bar_chart(monthly)
        
        if chart_buffer:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
                tmp.write(chart_buffer.getvalue())
                tmp_path = tmp.name
            
            img = Image(tmp_path, width=14*cm, height=10*cm)
            story.append(img)
            
            try:
                os.unlink(tmp_path)
            except:
                pass
        
        return story
    
    def _create_budget_status(self, df, budget_manager):
        """예산 현황"""
        story = []
        
        story.append(Paragraph("예산 현황", self.subtitle_style))
        
        analysis = budget_manager.analyze_spending(df)
        
        if analysis.empty:
            story.append(Paragraph("예산 데이터가 없습니다", self.body_style))
            return story
        
        data = [['카테고리', '예산', '지출', '잔여', '사용률', '상태']]
        
        for _, row in analysis.iterrows():
            data.append([
                row['카테고리'],
                f"{row['예산']:,.0f}",
                f"{row['지출']:,.0f}",
                f"{row['잔여']:,.0f}",
                f"{row['사용률(%)']:.1f}%",
                row['상태']
            ])
        
        table = Table(data, colWidths=[3*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 3*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), self.korean_font),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        
        return story
    
    def _create_transaction_list(self, df):
        """거래 내역 목록"""
        story = []
        
        story.append(Paragraph("최근 거래 내역 (20건)", self.subtitle_style))
        
        recent_df = df.sort_values('날짜', ascending=False).head(20)
        
        data = [['날짜', '적요', '금액', '카테고리']]
        
        for _, row in recent_df.iterrows():
            data.append([
                row['날짜'].strftime('%Y-%m-%d'),
                str(row.get('적요', '-'))[:20],
                f"{row['금액']:,.0f}원",
                row['분류']
            ])
        
        table = Table(data, colWidths=[3*cm, 6*cm, 4*cm, 3*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), self.korean_font),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        
        return story
    
    def _create_footer(self):
        """푸터 생성"""
        story = []
        
        story.append(Spacer(1, 2*cm))
        
        footer_style = ParagraphStyle(
            'Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#9ca3af'),
            alignment=TA_CENTER,
            fontName=self.korean_font
        )
        
        story.append(Paragraph("Expense Analyzer로 생성됨", footer_style))
        story.append(Paragraph("Powered by Streamlit & ReportLab", footer_style))
        
        return story
    
    def _create_pie_chart(self, data):
        """파이 차트 생성"""
        try:
            fig = go.Figure(data=[go.Pie(
                labels=data.index,
                values=data.values,
                hole=0.3
            )])
            
            fig.update_layout(
                showlegend=True,
                width=700,
                height=500,
                margin=dict(l=20, r=20, t=40, b=20),
                font=dict(family="Malgun Gothic, Arial", size=12)
            )
            
            img_bytes = fig.to_image(format="png", engine="kaleido")
            return BytesIO(img_bytes)
        except:
            return None
    
    def _create_bar_chart(self, data):
        """막대 차트 생성 (월별만 표시)"""
        try:
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=data.index,  # "2025-01" 형식
                y=data['수입'],
                name='수입',
                marker_color='#4CAF50'
            ))
            
            fig.add_trace(go.Bar(
                x=data.index,
                y=data['지출'],
                name='지출',
                marker_color='#FF5252'
            ))
            
            fig.update_layout(
                barmode='group',
                width=700,
                height=500,
                xaxis_title="월",
                yaxis_title="금액 (원)",
                showlegend=True,
                margin=dict(l=60, r=20, t=40, b=60),
                font=dict(family="Malgun Gothic, Arial", size=12)
            )
            
            # x축 포맷 설정 (월별만 표시)
            fig.update_xaxes(
                tickformat="%Y-%m",
                dtick="M1"
            )
            
            img_bytes = fig.to_image(format="png", engine="kaleido")
            return BytesIO(img_bytes)
        except:
            return None