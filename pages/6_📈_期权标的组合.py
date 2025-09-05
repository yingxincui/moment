#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
期权标的组合页面
包含科创50、中证500、上证50、创业板、沪深300、深证100等主要期权标的ETF
"""

import streamlit as st
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# 导入必要的模块
from core_strategy import select_etfs, render_momentum_results, render_simplified_bias_table, render_all_etfs_trend_charts, load_cache_meta, render_cache_info
from etf_pools import ETF_POOLS_CONFIG
from excel_report_utils import download_excel_report_button

# 页面标题
st.title("📈 期权标的组合")

# 获取期权标的组合配置
config = ETF_POOLS_CONFIG['option']
all_etfs = config['pool']
etf_list = list(all_etfs.keys())
default = list(all_etfs.keys())

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
    'etf_pool': 'option'
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
    st.subheader("📊 Bias分析")
    render_simplified_bias_table(selected_etfs, all_etfs)
    
    # 显示趋势图
    st.markdown("---")
    render_all_etfs_trend_charts(selected_etfs, all_etfs)

# 侧边栏
st.sidebar.subheader("📈 ETF组合说明")
st.sidebar.markdown(f"""
**{config['name']}：**
- 科创50ETF(588000)、中证500ETF(510500)、上证50ETF(510050)
- 创业板ETF(159915)、沪深300ETF(510300)、深证100ETF(159901)

**使用说明：**
- 选择ETF后自动进行分析
- 支持自定义策略参数
- 实时获取最新数据
""")

# 显示缓存信息
cache_meta = load_cache_meta()
render_cache_info(cache_meta)

# 手动刷新按钮
if st.button("🔄 手动刷新数据"):
    if 'momentum_results' in st.session_state:
        del st.session_state.momentum_results
    if 'momentum_params' in st.session_state:
        del st.session_state.momentum_params
    st.rerun()

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
