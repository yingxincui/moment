#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全球股市轮动页面
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

# 导入PDF报告工具
from pdf_report_utils import generate_and_download_report

# 页面配置
st.set_page_config(
    page_title="全球股市轮动 - 大类资产轮动",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 页面标题
st.title(" 全球股市轮动")

# 策略说明 - 可折叠组件
with st.expander(" 策略说明", expanded=False):
    st.markdown("""
    **策略说明**
    
    **动量策略逻辑：**
    - 动量计算: 计算各ETF在20天内的价格变化百分比
    - 趋势过滤: 使用28天移动平均线过滤下跌趋势
    - 持仓选择: 选择动量最强（涨幅最大）且趋势向上的ETF
    - 动态调整: 定期重新计算并调整持仓
    
    **当前参数设置：**
    - 动量周期：20天（计算价格变化百分比）
    - 均线周期：28天（趋势过滤）
    - 最大持仓：2只
    """)

st.markdown("---")

# 获取全球股市轮动组合配置
config = ETF_POOLS_CONFIG['global']
all_etfs = config['pool']
etf_list = list(all_etfs.keys())
default = list(all_etfs.keys())  # 默认选择所有ETF

st.markdown(f"**{config['name']}ETF池：**")
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
            selected_etfs_result, all_etfs_result = select_etfs(selected_etfs, all_etfs, momentum_period, ma_period)
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
    'etf_pool': 'global'
}

# 如果参数发生变化或没有缓存结果，则重新计算
if ('momentum_params' not in st.session_state or 
    st.session_state.momentum_params != current_params or
    'momentum_results' not in st.session_state):
    
    st.session_state.momentum_params = current_params
    selected_etfs_result, all_etfs_result = auto_calculate_momentum()
    st.session_state.momentum_results = {
        'selected_etfs_result': selected_etfs_result,
        'all_etfs_result': all_etfs_result
    }
else:
    # 使用缓存的结果
    selected_etfs_result = st.session_state.momentum_results['selected_etfs_result']
    all_etfs_result = st.session_state.momentum_results['all_etfs_result']

# 显示结果
if selected_etfs_result is not None and all_etfs_result is not None:
    # 显示基础动量结果
    render_momentum_results(selected_etfs_result, all_etfs_result, all_etfs, momentum_period, ma_period, max_positions)
    
    # 添加Bias分析
    st.markdown("---")
    st.subheader(" Bias分析")
    render_simplified_bias_table(selected_etfs, all_etfs)
    
    # 显示趋势图
    st.markdown("---")
    render_all_etfs_trend_charts(selected_etfs, all_etfs)

    # 添加PDF报告下载功能
    st.markdown("---")
    st.subheader(" PDF报告下载")

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
        
        # 生成PDF报告
        if st.button("�� 生成PDF分析报告", type="primary", use_container_width=True):
            try:
                generate_and_download_report(
                    etf_pool_name=etf_pool_name,
                    momentum_results=selected_etfs_result,
                    bias_results=bias_results,
                    trend_summary=trend_summary,
                    selected_etfs=selected_etfs_list
                )
            except Exception as e:
                st.error(f"生成PDF报告失败: {e}")
                st.info("请确保已安装所需的依赖包：pip install reportlab")
    else:
        st.info("请先进行动量分析，然后才能生成PDF报告")


# 侧边栏
st.sidebar.subheader(" ETF组合说明")
st.sidebar.markdown(f"""
**{config['name']}：**
- 300ETF(510300)、中概互联网ETF(513050)、纳指ETF(159941)
- 日经ETF(513520)、德国ETF(513030)、东南亚科技ETF(513730)、沙特ETF(159329)

 **使用说明：**
- 覆盖中美欧日等主要市场
- 支持全球资产配置
- 选择ETF后自动进行分析
""")

# 显示缓存信息
cache_meta = load_cache_meta()
render_cache_info(cache_meta)

# 手动刷新按钮
if st.button(" 手动刷新数据"):
    if 'momentum_results' in st.session_state:
        del st.session_state.momentum_results
    if 'momentum_params' in st.session_state:
        del st.session_state.momentum_params
    st.rerun()
