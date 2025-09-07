#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
明总定制组合页面
"""

import streamlit as st
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# 导入认证工具
from auth_utils import require_authentication

# 要求用户必须通过认证
require_authentication()

from etf_pools import ETF_POOLS_CONFIG

from core_strategy import (
    render_momentum_results, render_cache_info, small_log, load_cache_meta,
    fetch_etf_data, calculate_momentum_and_ma, select_etfs,
    render_simplified_bias_table, render_all_etfs_trend_charts
)

# 导入页面缓存工具
from page_cache_utils import render_cache_management_ui, clear_page_cache

# 已改为使用Excel报告工具，不再需要PDF报告工具

# 页面配置
st.set_page_config(
    page_title="明总定制组合 - 大类资产轮动",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 页面标题
st.title(" 明总定制组合")

# 策略说明 - 可折叠组件
with st.expander(" 策略说明", expanded=False):
    st.markdown("""
    **策略说明**
    
    **动量策略逻辑：**
    - 动量计算: 计算各ETF在20天内的价格变化百分比
    - 趋势过滤: 使用28天移动平均线过滤下跌趋势
    - 持仓选择: 选择动量最强（涨幅最大）且趋势向上的ETF
    - 动态调整: 定期重新计算并调整持仓
    
    **明总定制组合特色：**
    - 在默认组合基础上增加科创创业ETF(159781)和科创50ETF(588000)
    - 更全面的科技创新配置，覆盖A股、美股、黄金、债券等主要资产类别
    - 特别强化科技创新板块的配置权重
    
    **当前参数设置：**
    - 动量周期：20天（计算价格变化百分比）
    - 均线周期：28天（趋势过滤）
    - 最大持仓：2只
    """)

st.markdown("---")

# 获取明总定制组合配置
config = ETF_POOLS_CONFIG['mingzong']
all_etfs = config['pool']
etf_list = list(all_etfs.keys())
default = list(all_etfs.keys())

st.markdown(f"**{config['name']}ETF池：**")

# 导入页面缓存工具
from page_cache_utils import render_cache_management_ui, clear_page_cache
st.info(config['description'])

# ETF选择
selected_etfs = st.multiselect(
    "选择ETF（可多选）：",
    options=list(all_etfs.keys()),
    default=default,
    format_func=lambda x: f"{x} - {all_etfs.get(x, x)}"
)

# 策略参数
st.markdown("**策略参数配置：**")
col1, col2, col3 = st.columns(3)
with col1:
    momentum_period = st.number_input("动量周期", min_value=5, max_value=60, value=20)
with col2:
    ma_period = st.number_input("均线周期", min_value=5, max_value=60, value=28)
with col3:
    max_positions = st.number_input("最大持仓数量", min_value=1, max_value=5, value=2)

# 自动计算逻辑
def auto_calculate_momentum():
    """自动计算动量策略结果"""
    if len(selected_etfs) < 2:
        st.warning("请至少选择2只ETF")
        return None, None
    
    with st.spinner("正在获取ETF数据并计算持仓..."):
        try:
            selected_etfs_result, all_etfs_result = select_etfs(
                selected_etfs, all_etfs, momentum_period, ma_period, 
                use_cache=True, page_name="mingzong"
            )
            return selected_etfs_result, all_etfs_result
        except Exception as e:
            st.error(f"计算失败: {e}")
            import traceback
            st.markdown("<div style='font-size:12px; color:#888;'>" + traceback.format_exc().replace('\n', '<br>') + "</div>", unsafe_allow_html=True)
            return None, None

# 检查是否需要重新计算
current_params = {
    'selected_etfs': tuple(sorted(selected_etfs)) if selected_etfs else (),
    'momentum_period': momentum_period,
    'ma_period': ma_period,
    'max_positions': max_positions,
    'etf_pool': 'mingzong'
}

# 如果参数发生变化或没有缓存结果，则重新计算
if ('mingzong_momentum_params' not in st.session_state or 
    st.session_state.mingzong_momentum_params != current_params or
    'mingzong_momentum_results' not in st.session_state):
    
    st.session_state.mingzong_momentum_params = current_params
    selected_etfs_result, all_etfs_result = auto_calculate_momentum()
    st.session_state.mingzong_momentum_results = {
        'selected_etfs_result': selected_etfs_result,
        'all_etfs_result': all_etfs_result
    }
else:
    # 使用缓存的结果
    selected_etfs_result = st.session_state.mingzong_momentum_results['selected_etfs_result']
    all_etfs_result = st.session_state.mingzong_momentum_results['all_etfs_result']

# 显示结果
if selected_etfs_result is not None and all_etfs_result is not None:
    # 先获取Bias分析数据（不显示，只用于AI分析）
    bias_results = []
    try:
        # 静默获取Bias数据
        import core_strategy
        bias_results = core_strategy.render_simplified_bias_table(selected_etfs, all_etfs, page_name="mingzong", show_ui=False)
    except:
        pass
    
    # 显示基础动量结果（包含Bias数据）
    render_momentum_results(selected_etfs_result, all_etfs_result, all_etfs, momentum_period, ma_period, max_positions, page_name="mingzong", bias_results=bias_results)
    
    # 添加Bias分析
    st.markdown("---")
    st.subheader(" Bias分析")
    render_simplified_bias_table(selected_etfs, all_etfs, page_name="mingzong")
    
    # 显示趋势图
    st.markdown("---")
    render_all_etfs_trend_charts(selected_etfs, all_etfs, page_name="mingzong")

    # 添加Excel报告下载功能
    st.markdown("---")
    st.subheader("📊 Excel报告下载")

    # 检查是否有分析结果
    if 'selected_etfs_result' in locals() and selected_etfs_result is not None and len(selected_etfs_result) > 0:
        # 准备报告数据
        etf_pool_name = config['name']
        
        # 获取Bias分析结果（如果有的话）
        bias_results = None
        try:
            # 这里可以调用Bias分析函数获取结果
            # bias_results = get_bias_analysis_results(selected_etfs)
            pass
        except:
            pass
        
        # 获取趋势分析汇总（如果有的话）
        trend_summary = None
        try:
            # 这里可以调用趋势分析函数获取结果
            # trend_summary = get_trend_summary(selected_etfs)
            pass
        except:
            pass
        
        # 获取选中的ETF列表
        selected_etfs_list = None
        if 'selected_etfs_result' in locals() and selected_etfs_result:
            selected_etfs_list = selected_etfs_result
        
        # 生成Excel报告
        if st.button("📊 生成Excel分析报告", type="primary", use_container_width=True):
            try:
                from excel_report_utils import download_excel_report_button
                download_excel_report_button(
                    selected_etfs_result=selected_etfs_result,
                    all_etfs_result=all_etfs_result,
                    etf_pool=all_etfs,
                    momentum_period=momentum_period,
                    ma_period=ma_period,
                    max_positions=max_positions,
                    button_text="📊 下载Excel分析报告"
                )
            except Exception as e:
                st.error(f"生成Excel报告失败: {e}")
                st.info("请确保已安装所需的依赖包：pip install openpyxl")
    else:
        st.info("请先进行动量分析，然后才能生成Excel报告")

# 侧边栏
st.sidebar.subheader(" 明总定制组合说明")
st.sidebar.markdown(f"""
**{config['name']}：**
- 300ETF(510300)、创业板(159915)、中概互联网ETF(513050)
- 纳指ETF(159941)、黄金ETF(518880)、30年国债(511090)
- 科创创业ETF(159781)、科创50ETF(588000)

 **使用说明：**
- 选择ETF后自动进行分析
- 支持自定义策略参数
- 实时获取最新数据
- 特别强化科技创新板块配置
""")

# 显示缓存信息
cache_meta = load_cache_meta()
render_cache_info(cache_meta)

# 添加缓存管理界面
st.sidebar.markdown("---")
render_cache_management_ui()

# 手动刷新按钮
if st.button(" 手动刷新数据"):
    if 'mingzong_momentum_results' in st.session_state:
        del st.session_state.mingzong_momentum_results
    if 'mingzong_momentum_params' in st.session_state:
        del st.session_state.mingzong_momentum_params
    st.rerun()