#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
水印工具模块
为所有图表添加水印：公众号：躺赚10研究员
"""

import plotly.graph_objects as go
import plotly.express as px

def add_watermark_to_plotly(fig, watermark_text="公众号：躺赚10研究员", position="bottom-right"):
    """
    为plotly图表添加水印
    
    Args:
        fig: plotly图表对象
        watermark_text: 水印文本
        position: 水印位置 ("top-left", "top-right", "bottom-left", "bottom-right")
    
    Returns:
        添加了水印的图表对象
    """
    # 设置水印位置
    if position == "top-left":
        x_pos, y_pos, x_anchor, y_anchor = 0.02, 0.98, "left", "top"
    elif position == "top-right":
        x_pos, y_pos, x_anchor, y_anchor = 0.98, 0.98, "right", "top"
    elif position == "bottom-left":
        x_pos, y_pos, x_anchor, y_anchor = 0.02, 0.02, "left", "bottom"
    else:  # bottom-right (默认)
        x_pos, y_pos, x_anchor, y_anchor = 0.98, 0.02, "right", "bottom"
    
    # 添加水印注释
    fig.add_annotation(
        x=x_pos,
        y=y_pos,
        xref="paper",
        yref="paper",
        text=watermark_text,
        showarrow=False,
        font=dict(
            size=12,
            color="rgba(128, 128, 128, 0.7)",
            family="Arial"
        ),
        xanchor=x_anchor,
        yanchor=y_anchor,
        bgcolor="rgba(255, 255, 255, 0.8)",
        bordercolor="rgba(128, 128, 128, 0.3)",
        borderwidth=1,
        borderpad=4,
        align="center"
    )
    
    return fig

def create_watermarked_figure(fig_type="go", *args, **kwargs):
    """
    创建带水印的plotly图表
    
    Args:
        fig_type: 图表类型 ("go" 或 "px")
        *args, **kwargs: 传递给图表创建函数的参数
    
    Returns:
        带水印的图表对象
    """
    if fig_type == "go":
        fig = go.Figure(*args, **kwargs)
    elif fig_type == "px":
        fig = px.Figure(*args, **kwargs)
    else:
        raise ValueError("fig_type 必须是 'go' 或 'px'")
    
    # 添加水印
    fig = add_watermark_to_plotly(fig)
    
    return fig

def add_watermark_to_existing_figure(fig, watermark_text="公众号：躺赚10研究员"):
    """
    为现有的plotly图表添加水印
    
    Args:
        fig: 现有的plotly图表对象
        watermark_text: 水印文本
    
    Returns:
        添加了水印的图表对象
    """
    return add_watermark_to_plotly(fig, watermark_text)

def create_watermarked_bar_chart(data, x_col, y_col, title="", **kwargs):
    """
    创建带水印的柱状图
    
    Args:
        data: 数据框
        x_col: X轴列名
        y_col: Y轴列名
        title: 图表标题
        **kwargs: 其他参数
    
    Returns:
        带水印的柱状图
    """
    fig = px.bar(data, x=x_col, y=y_col, title=title, **kwargs)
    return add_watermark_to_plotly(fig)

def create_watermarked_line_chart(data, x_col, y_col, title="", **kwargs):
    """
    创建带水印的折线图
    
    Args:
        data: 数据框
        x_col: X轴列名
        y_col: Y轴列名
        title: 图表标题
        **kwargs: 其他参数
    
    Returns:
        带水印的折线图
    """
    fig = px.line(data, x=x_col, y=y_col, title=title, **kwargs)
    return add_watermark_to_plotly(fig)

def create_watermarked_scatter_chart(data, x_col, y_col, title="", **kwargs):
    """
    创建带水印的散点图
    
    Args:
        data: 数据框
        x_col: X轴列名
        y_col: Y轴列名
        title: 图表标题
        **kwargs: 其他参数
    
    Returns:
        带水印的散点图
    """
    fig = px.scatter(data, x=x_col, y=y_col, title=title, **kwargs)
    return add_watermark_to_plotly(fig)

def create_watermarked_histogram(data, x_col, title="", **kwargs):
    """
    创建带水印的直方图
    
    Args:
        data: 数据框
        x_col: X轴列名
        title: 图表标题
        **kwargs: 其他参数
    
    Returns:
        带水印的直方图
    """
    fig = px.histogram(data, x=x_col, title=title, **kwargs)
    return add_watermark_to_plotly(fig)
