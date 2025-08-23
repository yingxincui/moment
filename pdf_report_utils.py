#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF报告工具模块
为ETF动量策略分析系统生成PDF格式的分析报告
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io
import base64
from reportlab.lib.pagesizes import A4, letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
import plotly.graph_objects as go
import plotly.express as px
from watermark_utils import add_watermark_to_existing_figure

class PDFReportGenerator:
    """PDF报告生成器"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """设置自定义样式"""
        # 使用支持中文的字体，尝试多个字体选项
        try:
            # 尝试使用系统中可用的中文字体
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            
            # 注册中文字体
            try:
                pdfmetrics.registerFont(TTFont('chinese', 'C:/Windows/Fonts/simsun.ttc'))
                chinese_font = 'chinese'
            except:
                try:
                    pdfmetrics.registerFont(TTFont('chinese', 'C:/Windows/Fonts/msyh.ttc'))
                    chinese_font = 'chinese'
                except:
                    chinese_font = 'Helvetica'  # 回退到默认字体
        except:
            chinese_font = 'Helvetica'  # 回退到默认字体
        
        # 标题样式
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=HexColor('#1f77b4'),
            fontName=chinese_font
        )
        
        # 副标题样式
        self.subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=18,
            spaceAfter=20,
            alignment=TA_LEFT,
            textColor=HexColor('#2e7d32'),
            fontName=chinese_font
        )
        
        # 正文样式
        self.body_style = ParagraphStyle(
            'CustomBody',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=12,
            alignment=TA_LEFT,
            textColor=HexColor('#424242'),
            fontName=chinese_font
        )
        
        # 强调样式
        self.emphasis_style = ParagraphStyle(
            'CustomEmphasis',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=12,
            alignment=TA_LEFT,
            textColor=HexColor('#d32f2f'),
            fontName=chinese_font
        )
        
        # 表格标题样式
        self.table_title_style = ParagraphStyle(
            'CustomTableTitle',
            parent=self.styles['Heading3'],
            fontSize=14,
            spaceAfter=15,
            alignment=TA_CENTER,
            textColor=HexColor('#1976d2'),
            fontName=chinese_font
        )
    
    def generate_momentum_report(self, etf_pool_name, momentum_results, bias_results, 
                                trend_summary, selected_etfs=None, backtest_results=None):
        """
        生成完整的动量策略分析报告
        
        Args:
            etf_pool_name: ETF池名称
            momentum_results: 动量分析结果
            bias_results: Bias分析结果
            trend_summary: 趋势分析汇总
            selected_etfs: 选中的ETF列表
            backtest_results: 回测结果
        
        Returns:
            bytes: PDF文件的二进制数据
        """
        # 创建内存中的PDF文档
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, 
                              topMargin=72, bottomMargin=72)
        
        # 构建报告内容
        story = []
        
        # 1. 报告标题页
        story.extend(self._create_title_page(etf_pool_name))
        story.append(PageBreak())
        
        # 2. 执行摘要
        story.extend(self._create_executive_summary(momentum_results, selected_etfs))
        story.append(PageBreak())
        
        # 3. 动量策略分析
        story.extend(self._create_momentum_analysis(momentum_results, selected_etfs))
        
        # 4. Bias分析
        if bias_results:
            story.extend(self._create_bias_analysis(bias_results))
        
        # 5. 趋势分析
        if trend_summary:
            story.extend(self._create_trend_analysis(trend_summary))
        
        # 6. 回测结果（如果有）
        if backtest_results:
            story.extend(self._create_backtest_analysis(backtest_results))
        
        # 7. 投资建议
        story.extend(self._create_investment_recommendations(momentum_results, bias_results))
        
        # 8. 风险提示
        story.extend(self._create_risk_disclaimer())
        
        # 生成PDF
        doc.build(story)
        
        # 获取PDF数据
        pdf_data = buffer.getvalue()
        buffer.close()
        
        return pdf_data
    
    def _create_title_page(self, etf_pool_name):
        """创建报告标题页"""
        elements = []
        
        # 标题
        title = Paragraph(f"ETF动量策略分析报告", self.title_style)
        elements.append(title)
        elements.append(Spacer(1, 60))
        
        # ETF池名称
        pool_name = Paragraph(f"ETF池：{etf_pool_name}", self.subtitle_style)
        elements.append(pool_name)
        elements.append(Spacer(1, 40))
        
        # 生成时间
        current_time = datetime.now().strftime("%Y年%m月%d日 %H:%M")
        time_text = Paragraph(f"报告生成时间：{current_time}", self.body_style)
        elements.append(time_text)
        elements.append(Spacer(1, 20))
        
        # 报告说明
        description = Paragraph("""
        本报告基于动量策略对ETF进行量化分析，包含动量排名、Bias分析、趋势图表等内容。
        报告数据来源于公开市场数据，仅供参考，不构成投资建议。
        """, self.body_style)
        elements.append(description)
        
        return elements
    
    def _create_executive_summary(self, momentum_results, selected_etfs):
        """创建执行摘要"""
        elements = []
        
        # 章节标题
        title = Paragraph("执行摘要", self.subtitle_style)
        elements.append(title)
        elements.append(Spacer(1, 20))
        
        # 摘要内容
        if momentum_results is not None and len(momentum_results) > 0:
            total_etfs = len(momentum_results)
            # 对于列表格式的动量结果，计算正负动量数量
            positive_momentum = sum(1 for item in momentum_results if len(item) > 4 and item[4] > 0)
            negative_momentum = total_etfs - positive_momentum
            
            summary_text = f"""
            <b>市场概况：</b>本次分析共包含{total_etfs}只ETF，其中动量为正的ETF有{positive_momentum}只，
            动量为负的ETF有{negative_momentum}只。
            """
            
            if selected_etfs:
                summary_text += f"<br/><br/><b>推荐持仓：</b>基于动量策略，推荐持有{len(selected_etfs)}只ETF。"
            
            summary = Paragraph(summary_text, self.body_style)
            elements.append(summary)
        
        return elements
    
    def _create_momentum_analysis(self, momentum_results, selected_etfs):
        """创建动量策略分析章节"""
        elements = []
        
        # 章节标题
        title = Paragraph("动量策略分析", self.subtitle_style)
        elements.append(title)
        elements.append(Spacer(1, 20))
        
        if momentum_results is not None and len(momentum_results) > 0:
            # 策略说明
            strategy_text = """
            <b>策略逻辑：</b>
            • 动量计算：基于价格变化的动量指标计算
            • 趋势过滤：使用移动平均线过滤下跌趋势
            • 持仓选择：选择动量最强且趋势向上的ETF
            • 动态调整：定期重新计算并调整持仓
            """
            strategy = Paragraph(strategy_text, self.body_style)
            elements.append(strategy)
            elements.append(Spacer(1, 20))
            
            # 推荐持仓
            if selected_etfs:
                elements.append(Paragraph("<b>推荐持仓：</b>", self.emphasis_style))
                elements.append(Spacer(1, 10))
                
                for i, etf_info in enumerate(selected_etfs, 1):
                    etf_code = etf_info[0]
                    etf_name = etf_info[1]
                    etf_text = f"{i}. {etf_code} - {etf_name}"
                    etf_para = Paragraph(etf_text, self.body_style)
                    elements.append(etf_para)
                
                elements.append(Spacer(1, 20))
            
            # 动量排名表格
            elements.append(Paragraph("<b>动量排名概览：</b>", self.emphasis_style))
            elements.append(Spacer(1, 15))
            
            # 创建表格数据
            table_data = [['排名', 'ETF代码', 'ETF名称', '动量得分', '当前价格', '涨跌幅(%)']]
            
            for i, item in enumerate(momentum_results, 1):
                if len(item) >= 6:  # 确保有足够的数据
                    table_data.append([
                        str(i),
                        item[0],  # ETF代码
                        item[1],  # ETF名称
                        f"{item[4]:.4f}" if len(item) > 4 else "N/A",  # 动量得分
                        f"{item[2]:.4f}" if len(item) > 2 else "N/A",  # 当前价格
                        f"{item[4]*100:.2f}" if len(item) > 4 else "N/A"  # 涨跌幅
                    ])
            
            # 创建表格
            table = Table(table_data, colWidths=[0.8*inch, 1.2*inch, 2.5*inch, 1.2*inch, 1.2*inch, 1.2*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
            ]))
            
            elements.append(table)
        
        return elements
    
    def _create_bias_analysis(self, bias_results):
        """创建Bias分析章节"""
        elements = []
        
        # 章节标题
        elements.append(Paragraph("Bias分析", self.subtitle_style))
        elements.append(Spacer(1, 20))
        
        if bias_results:
            # 统计信息
            overbought_count = sum(1 for r in bias_results if '超买' in r.get('超买超卖结论', ''))
            oversold_count = sum(1 for r in bias_results if '超卖' in r.get('超买超卖结论', ''))
            normal_count = len(bias_results) - overbought_count - oversold_count
            
            stats_text = f"""
            <b>市场状态统计：</b>
            • 超买标的：{overbought_count}只
            • 超卖标的：{oversold_count}只
            • 正常标的：{normal_count}只
            """
            stats = Paragraph(stats_text, self.body_style)
            elements.append(stats)
            elements.append(Spacer(1, 20))
            
            # Bias分析表格
            elements.append(Paragraph("<b>Bias分析详情：</b>", self.emphasis_style))
            elements.append(Spacer(1, 15))
            
            table_data = [['ETF代码', 'ETF名称', '6日偏离度', '12日偏离度', '24日偏离度', '结论']]
            
            for result in bias_results:
                table_data.append([
                    result['ETF代码'],
                    result['ETF名称'],
                    f"{result.get('6日偏离度', 0):.2f}",
                    f"{result.get('12日偏离度', 0):.2f}",
                    f"{result.get('24日偏离度', 0):.2f}",
                    result.get('超买超卖结论', '正常')
                ])
            
            # 创建表格
            table = Table(table_data, colWidths=[1.2*inch, 2.5*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.5*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
            ]))
            
            elements.append(table)
        
        return elements
    
    def _create_trend_analysis(self, trend_summary):
        """创建趋势分析章节"""
        elements = []
        
        # 章节标题
        elements.append(Paragraph("趋势分析", self.subtitle_style))
        elements.append(Spacer(1, 20))
        
        if trend_summary:
            # 趋势统计
            trend_text = f"""
            <b>市场趋势统计：</b>
            • 上涨标的：{trend_summary.get('上涨标的', 0)}只
            • 下跌标的：{trend_summary.get('下跌标的', 0)}只
            • 平均涨幅：{trend_summary.get('平均涨幅', 0):.2f}%
            • 平均跌幅：{trend_summary.get('平均跌幅', 0):.2f}%
            """
            trend = Paragraph(trend_text, self.body_style)
            elements.append(trend)
        
        return elements
    
    def _create_backtest_analysis(self, backtest_results):
        """创建回测分析章节"""
        elements = []
        
        # 章节标题
        elements.append(Paragraph("回测分析", self.subtitle_style))
        elements.append(Spacer(1, 20))
        
        if backtest_results:
            # 回测指标
            metrics_text = f"""
            <b>回测结果：</b>
            • 总收益率：{backtest_results.get('total_return', 0):.2f}%
            • 年化收益率：{backtest_results.get('annual_return', 0):.2f}%
            • 最大回撤：{backtest_results.get('max_drawdown', 0):.2f}%
            • 夏普比率：{backtest_results.get('sharpe_ratio', 0):.2f}
            • 交易次数：{backtest_results.get('trade_count', 0)}次
            """
            metrics = Paragraph(metrics_text, self.body_style)
            elements.append(metrics)
        
        return elements
    
    def _create_investment_recommendations(self, momentum_results, bias_results):
        """创建投资建议章节"""
        elements = []
        
        # 章节标题
        elements.append(Paragraph("投资建议", self.subtitle_style))
        elements.append(Spacer(1, 20))
        
        # 动量策略建议
        if momentum_results is not None and len(momentum_results) > 0:
            momentum_advice = """
            <b>动量策略建议：</b>
            • 关注动量排名前3的ETF，可作为主要持仓
            • 定期检查排名变化，及时调整持仓结构
            • 结合趋势过滤，避免在下跌趋势中加仓
            • 建议分散投资，控制单只ETF的仓位比例
            """
            elements.append(Paragraph(momentum_advice, self.body_style))
            elements.append(Spacer(1, 15))
        
        # Bias策略建议
        if bias_results:
            bias_advice = """
            <b>Bias策略建议：</b>
            • 超买标的：注意风险，可考虑减仓或观望
            • 超卖标的：可能存在投资机会，可逢低布局
            • 正常标的：根据其他指标灵活操作
            • 结合多周期偏离度，提高判断准确性
            """
            elements.append(Paragraph(bias_advice, self.body_style))
        
        return elements
    
    def _create_risk_disclaimer(self):
        """创建风险提示章节"""
        elements = []
        
        # 章节标题
        elements.append(Paragraph("风险提示", self.subtitle_style))
        elements.append(Spacer(1, 20))
        
        # 风险提示内容
        risk_text = """
        <b>重要声明：</b>
        
        1. <b>数据来源：</b>本报告数据来源于公开市场数据，可能存在延迟或错误
        2. <b>策略风险：</b>动量策略存在滞后性，可能错过最佳买卖时机
        3. <b>市场风险：</b>ETF投资存在市场风险，价格可能下跌
        4. <b>流动性风险：</b>部分ETF可能存在流动性不足的问题
        5. <b>免责声明：</b>本报告仅供参考，不构成投资建议，投资有风险，入市需谨慎
        
        <b>投资建议：</b>
        • 请根据自身风险承受能力进行投资决策
        • 建议进行充分的尽职调查和风险评估
        • 可考虑咨询专业投资顾问的意见
        """
        
        risk = Paragraph(risk_text, self.body_style)
        elements.append(risk)
        
        return elements
    
    def add_watermark_to_pdf(self, pdf_data, watermark_text="公众号：躺赚10研究员"):
        """
        为PDF添加水印
        
        Args:
            pdf_data: 原始PDF数据
            watermark_text: 水印文本
        
        Returns:
            bytes: 添加了水印的PDF数据
        """
        # 创建带水印的PDF
        buffer = io.BytesIO()
        
        # 读取原始PDF
        from PyPDF2 import PdfReader, PdfWriter
        
        try:
            reader = PdfReader(io.BytesIO(pdf_data))
            writer = PdfWriter()
            
            # 为每一页添加水印
            for page in reader.pages:
                # 创建水印页面
                watermark_page = self._create_watermark_page(page, watermark_text)
                page.merge_page(watermark_page)
                writer.add_page(page)
            
            # 写入新的PDF
            writer.write(buffer)
            watermarked_pdf = buffer.getvalue()
            buffer.close()
            
            return watermarked_pdf
            
        except ImportError:
            # 如果没有PyPDF2，返回原始PDF
            st.warning("未安装PyPDF2，无法添加水印，返回原始PDF")
            return pdf_data
        except Exception as e:
            st.error(f"添加水印失败: {e}")
            return pdf_data
    
    def _create_watermark_page(self, page, watermark_text):
        """创建水印页面"""
        # 这里可以实现水印添加逻辑
        # 由于复杂性，暂时返回原始页面
        return page

def create_download_button(pdf_data, filename, button_text="📥 下载PDF报告"):
    """
    创建PDF下载按钮
    
    Args:
        pdf_data: PDF文件数据
        filename: 文件名
        button_text: 按钮文本
    
    Returns:
        Streamlit下载按钮
    """
    # 编码PDF数据
    b64_pdf = base64.b64encode(pdf_data).decode()
    
    # 创建下载链接
    href = f'<a href="data:application/pdf;base64,{b64_pdf}" download="{filename}" target="_blank">{button_text}</a>'
    
    return st.markdown(href, unsafe_allow_html=True)

def generate_and_download_report(etf_pool_name, momentum_results, bias_results, 
                               trend_summary, selected_etfs=None, backtest_results=None):
    """
    生成并下载PDF报告的便捷函数
    
    Args:
        etf_pool_name: ETF池名称
        momentum_results: 动量分析结果
        bias_results: Bias分析结果
        trend_summary: 趋势分析汇总
        selected_etfs: 选中的ETF列表
        backtest_results: 回测结果
    """
    # 创建PDF生成器
    generator = PDFReportGenerator()
    
    # 生成PDF报告
    with st.spinner("正在生成PDF报告..."):
        pdf_data = generator.generate_momentum_report(
            etf_pool_name, momentum_results, bias_results, 
            trend_summary, selected_etfs, backtest_results
        )
    
    # 添加水印
    watermarked_pdf = generator.add_watermark_to_pdf(pdf_data)
    
    # 生成文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"ETF动量策略分析报告_{etf_pool_name}_{timestamp}.pdf"
    
    # 创建下载按钮
    create_download_button(watermarked_pdf, filename)
    
    st.success(f"✅ PDF报告生成完成！文件大小: {len(watermarked_pdf)/1024:.1f} KB")
    
    return watermarked_pdf, filename
