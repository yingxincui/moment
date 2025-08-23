#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心策略模块
包含所有共用的策略函数和工具
"""

import streamlit as st
import pandas as pd
import numpy as np
import akshare as ak
from datetime import datetime, timedelta
import hashlib
import json
import os
import sys

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 缓存目录
CACHE_DIR = "etf_cache"
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

# 控制是否显示缓存日志
SHOW_CACHE_LOGS = False

def get_cache_file_path(symbol):
    """获取缓存文件路径"""
    return os.path.join(CACHE_DIR, f"{symbol}_data.csv")

def get_cache_meta_file_path():
    """获取缓存元数据文件路径"""
    return os.path.join(CACHE_DIR, "cache_meta.json")

def load_cache_meta():
    """加载缓存元数据"""
    meta_file = get_cache_meta_file_path()
    if os.path.exists(meta_file):
        try:
            with open(meta_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_cache_meta(meta_data):
    """保存缓存元数据"""
    meta_file = get_cache_meta_file_path()
    try:
        with open(meta_file, 'w', encoding='utf-8') as f:
            json.dump(meta_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        small_log(f"保存缓存元数据失败: {e}")

def is_cache_valid(symbol):
    """检查缓存是否有效（同一天的数据）"""
    today = datetime.now().strftime('%Y-%m-%d')
    meta_data = load_cache_meta()
    
    # 确保symbol为字符串类型
    symbol_str = str(symbol)
    if symbol_str in meta_data:
        last_update = meta_data[symbol_str].get('last_update', '')
        return last_update == today
    return False

def save_to_cache(symbol, df):
    """保存数据到缓存"""
    try:
        cache_file = get_cache_file_path(symbol)
        df.to_csv(cache_file, encoding='utf-8')
        
        # 更新元数据
        meta_data = load_cache_meta()
        # 确保symbol为字符串类型
        symbol_str = str(symbol)
        meta_data[symbol_str] = {
            'last_update': datetime.now().strftime('%Y-%m-%d'),
            'data_length': len(df),
            'latest_date': df.index[-1].strftime('%Y-%m-%d') if len(df) > 0 else ''
        }
        save_cache_meta(meta_data)
        
    except Exception as e:
        small_log(f"保存{symbol}缓存失败: {e}")

def load_from_cache(symbol):
    """从缓存加载数据"""
    try:
        cache_file = get_cache_file_path(symbol)
        if os.path.exists(cache_file):
            # 确保日期索引正确解析
            df = pd.read_csv(cache_file, index_col=0)
            df.index = pd.to_datetime(df.index)
            return df
    except Exception as e:
        small_log(f"加载{symbol}缓存失败: {e}")
    return None

def fetch_etf_data(symbol="510300"):
    """获取ETF数据的函数"""
    # 检查缓存是否有效
    if is_cache_valid(symbol):
        cached_data = load_from_cache(symbol)
        if cached_data is not None:
            small_log(f"使用{symbol}缓存数据")
            return cached_data
    
    # 缓存无效或不存在，从API获取数据
    small_log(f"从API获取{symbol}数据...")
    try:
        # 使用 akshare 的 fund_etf_hist_em 接口获取 ETF 数据
        df = ak.fund_etf_hist_em(symbol=symbol, period="daily", adjust='qfq')
        # 转换日期格式
        df['日期'] = pd.to_datetime(df['日期'])  # 假设日期列名为 '日期'
        df.set_index('日期', inplace=True)
        # 重命名列以符合标准格式
        df.rename(columns={
            '开盘': 'Open',
            '最高': 'High',
            '最低': 'Low',
            '收盘': 'Close',
            '成交量': 'Volume'
        }, inplace=True)
        
        # 确保索引是datetime类型
        df.index = pd.to_datetime(df.index)
        
        # 保存到缓存
        save_to_cache(symbol, df)
        return df
        
    except Exception as e:
        small_log(f"获取{symbol}数据失败: {e}")
        # 尝试使用缓存数据（即使不是今天的）
        cached_data = load_from_cache(symbol)
        if cached_data is not None:
            small_log(f"使用{symbol}历史缓存数据")
            return cached_data
        return pd.DataFrame()

def calculate_momentum_and_ma(df, momentum_period=20, ma_period=28):
    """计算动量和均线"""
    # 计算动量：当前收盘价与N天前收盘价的百分比变化
    df['Momentum'] = df['Close'] / df['Close'].shift(momentum_period) - 1
    # 计算移动平均线
    df['MA'] = df['Close'].rolling(window=ma_period).mean()
    return df

def calculate_annual_return(start_value, end_value, days):
    """计算年化收益率"""
    if days <= 0 or start_value <= 0:
        return 0
    years = days / 365.25
    # 使用更稳定的年化收益率计算方法
    if years > 0:
        return ((end_value / start_value) ** (1 / years) - 1) * 100
    else:
        return 0

def calculate_max_drawdown(values):
    """计算最大回撤"""
    if len(values) < 2:
        return 0
    
    max_dd = 0
    peak = values[0]
    
    for value in values:
        if value > peak:
            peak = value
        dd = (peak - value) / peak * 100
        if dd > max_dd:
            max_dd = dd
    
    return max_dd

def calculate_sharpe_ratio(values):
    """计算夏普比率"""
    if len(values) < 2:
        return 0
    
    returns = []
    for i in range(1, len(values)):
        if values[i-1] > 0:
            returns.append((values[i] / values[i-1] - 1) * 100)
    
    if not returns:
        return 0
    
    mean_return = np.mean(returns)
    std_return = np.std(returns)
    
    if std_return == 0:
        return 0
    
    # 假设无风险利率为3%
    risk_free_rate = 3
    sharpe = (mean_return - risk_free_rate) / std_return * np.sqrt(252)
    
    return sharpe

def select_etfs(etf_list, etf_names, momentum_period=20, ma_period=28):
    """
    筛选符合条件的ETF（兼容动量策略.py的接口）
    
    Args:
        etf_list: ETF代码列表
        etf_names: ETF名称字典
        momentum_period: 动量周期
        ma_period: 均线周期
    
    Returns:
        selected_etfs: 选中的ETF列表
        all_etfs: 所有ETF的排名列表
    """
    etf_data = {}
    for symbol in etf_list:
        try:
            df = fetch_etf_data(symbol)
            if df.empty:
                small_log(f"{symbol} 数据为空，已跳过")
                continue
            df = calculate_momentum_and_ma(df, momentum_period, ma_period)
            etf_data[symbol] = df
        except Exception as e:
            small_log(f"处理{symbol}数据失败: {e}")
            continue
    
    if not etf_data:
        small_log("无法获取任何ETF数据")
        return [], []
    
    # 获取最新的数据
    latest_data = {symbol: df.iloc[-1] for symbol, df in etf_data.items()}
    
    # 收集所有ETF的动量和是否大于均线的信息
    all_etfs = []
    for symbol, data in latest_data.items():
        above_ma = data['Close'] > data['MA']
        all_etfs.append((symbol, etf_names[symbol], data['Close'], data['MA'], data['Momentum'], above_ma))
    
    # 按动量排序
    all_etfs.sort(key=lambda x: x[4], reverse=True)
    
    # 选择动量排名前两位且收盘价大于均线的ETF
    selected_etfs = [(etf[0], etf[1], etf[2], etf[3], etf[4]) for etf in all_etfs if etf[5]][:2]
    return selected_etfs, all_etfs

def select_etfs_ui(etf_pool, default_selection=None):
    """
    选择ETF的函数（UI版本）
    
    Args:
        etf_pool: ETF池字典
        default_selection: 默认选择的ETF代码列表
    
    Returns:
        selected_etfs: 用户选择的ETF代码列表
    """
    if default_selection is None:
        default_selection = list(etf_pool.keys())[:3]  # 默认选择前3个
    
    selected_etfs = st.multiselect(
        '选择ETF',
        options=list(etf_pool.keys()),
        default=default_selection,
        format_func=lambda x: f"{x} - {etf_pool[x]}"
    )
    
    return selected_etfs

def render_analysis_results(momentum_results, etf_pool):
    """
    渲染分析结果
    
    Args:
        momentum_results: 动量计算结果
        etf_pool: ETF池字典
    """
    if momentum_results is None or momentum_results.empty:
        st.warning("暂无计算结果，请先计算动量")
        return
    
    st.subheader("📊 动量分析结果")
    
    # 显示结果表格
    # 显示表格，不设置高度避免滚动条
    st.dataframe(momentum_results, use_container_width=True)
    
    # 显示图表
    if not momentum_results.empty:
        # 动量
        st.subheader("📈 动量")
        momentum_scores = momentum_results['动量得分'].values
        
        # 创建柱状图
        chart_data = pd.DataFrame({
            'ETF': momentum_results['ETF代码'],
            '动量': momentum_scores
        })
        
        st.bar_chart(chart_data.set_index('ETF'))
        
        # 显示详细信息
        st.subheader("📋 详细信息")
        for _, row in momentum_results.iterrows():
            with st.expander(f"{row['ETF代码']} - {etf_pool.get(row['ETF代码'], '未知')}"):
                st.write(f"**动量**: {row['动量得分']:.4f}")
                st.write(f"**价格**: {row['当前价格']:.4f}")
                st.write(f"**涨跌幅**: {row['涨跌幅']:.2f}%")
                st.write(f"**成交量**: {row['成交量']:,.0f}")

def render_momentum_results(selected_etfs_result, all_etfs_result, etf_pool, momentum_period, ma_period, max_positions):
    """
    渲染动量策略结果（兼容动量策略.py的输出格式）
    
    Args:
        selected_etfs_result: 选中的ETF结果
        all_etfs_result: 所有ETF结果
        etf_pool: ETF池字典
        momentum_period: 动量周期
        ma_period: 均线周期
        max_positions: 最大持仓数量
    """
    st.subheader("📊 动量策略分析结果")
    
    # 显示选中的ETF（仅显示标题，不显示文字提示）
    if selected_etfs_result:
        st.subheader("🎯 推荐持仓")
        
        # 构建推荐的ETF列表
        etf_list = []
        for i, etf_info in enumerate(selected_etfs_result, 1):
            etf_code = etf_info[0]  # 第一个元素是ETF代码
            etf_name = etf_info[1]  # 第二个元素是ETF名称
            etf_list.append(f"{i}. {etf_code} - {etf_name}")
        
        etf_list_text = "\n".join(etf_list)
        
        # 添加策略说明
        st.info(f"""
**📋 持仓策略说明：**

• **默认推荐前两名**：系统基于动量策略自动选择动量最强且趋势向上的前2只ETF
• **缓冲机制**：可以持有前三名，提供一定的缓冲空间
• **调仓条件**：只有当ETF掉到第四名时才进行调仓
• **风险控制**：结合价格与均线关系，确保趋势向上

**🎯 当前推荐标的：**
{etf_list_text}

**💡 操作建议：**
- 当前持仓：{len(selected_etfs_result)}只ETF
- 建议：可以适当持有第3名ETF作为缓冲
- 调仓时机：关注排名变化，避免频繁交易
        """)
    
    # 显示所有ETF的排名
    if all_etfs_result:
        st.subheader("📈 所有ETF动量排名")
        # 创建所有ETF的表格
        all_data = []
        for etf in all_etfs_result:
            if len(etf) >= 6:
                status = "✅ 推荐" if etf[5] else "❌ 不符合条件"
                all_data.append({
                    'ETF代码': etf[0],
                    'ETF名称': etf[1],
                    '当前价格': f"{etf[2]:.4f}",
                    '均线价格': f"{etf[3]:.4f}",
                    '动量': f"{etf[4]*100:.2f}%",
                    '状态': status
                })
        
        if all_data:
            all_df = pd.DataFrame(all_data)
            
            # 美化表格显示
            def style_momentum_table(df):
                """美化动量排名表格"""
                
                def color_momentum_values(val):
                    """为动量值添加颜色"""
                    if isinstance(val, str) and '%' in val:
                        try:
                            momentum_value = float(val.rstrip('%'))
                            if momentum_value > 5:
                                return 'background-color: #ffebee; color: #c62828; font-weight: bold; border-radius: 4px; padding: 4px 8px;'  # 超强动量：深红色
                            elif momentum_value > 2:
                                return 'background-color: #ffcdd2; color: #b71c1c; font-weight: bold; border-radius: 4px; padding: 4px 8px;'  # 强动量：红色
                            elif momentum_value > 0:
                                return 'background-color: #fff3e0; color: #ef6c00; font-weight: bold; border-radius: 4px; padding: 4px 8px;'  # 正动量：橙色
                            elif momentum_value > -2:
                                return 'background-color: #f5f5f5; color: #424242; font-weight: bold; border-radius: 4px; padding: 4px 8px;'  # 轻微负动量：灰色
                            elif momentum_value > -5:
                                return 'background-color: #e8f5e8; color: #2e7d32; font-weight: bold; border-radius: 4px; padding: 4px 8px;'  # 负动量：绿色
                            else:
                                return 'background-color: #c8e6c9; color: #1b5e20; font-weight: bold; border-radius: 4px; padding: 4px 8px;'  # 强负动量：深绿色
                        except:
                            return ''
                    return ''
                
                def color_status_values(val):
                    """为状态值添加颜色"""
                    if isinstance(val, str):
                        if '✅ 推荐' in val:
                            return 'background-color: #e8f5e8; color: #2e7d32; font-weight: bold; border-radius: 4px; padding: 4px 8px; border: 2px solid #4caf50;'
                        elif '❌ 不符合条件' in val:
                            return 'background-color: #ffebee; color: #c62828; font-weight: bold; border-radius: 4px; padding: 4px 8px; border: 2px solid #f44336;'
                    return ''
                
                def color_price_values(val):
                    """为价格值添加颜色"""
                    if isinstance(val, str) and '.' in val:
                        return 'background-color: #f8f9fa; color: #495057; font-weight: 500; font-family: "Courier New", monospace; border-radius: 4px; padding: 4px 8px;'
                    return ''
                
                # 应用样式到不同列
                styled_df = df.style.map(color_momentum_values, subset=['动量'])
                styled_df = styled_df.map(color_status_values, subset=['状态'])
                styled_df = styled_df.map(color_price_values, subset=['当前价格', '均线价格'])
                
                # 为ETF代码和名称添加样式
                styled_df = styled_df.apply(lambda x: [
                    'background-color: #e3f2fd; color: #1565c0; font-weight: bold; border-radius: 4px; padding: 4px 8px;' if col == 'ETF代码' else
                    'background-color: #f3e5f5; color: #7b1fa2; font-weight: bold; border-radius: 4px; padding: 4px 8px;' if col == 'ETF名称' else
                    '' for col in df.columns
                ], axis=0)
                
                return styled_df
            
            # 应用美化样式
            styled_all_df = style_momentum_table(all_df)
            
            # 显示美化后的表格
            st.dataframe(styled_all_df, use_container_width=True)
            
            # 添加表格说明
            st.markdown("""
            <div style='background-color: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #007bff; margin-top: 15px;'>
                <strong>📊 动量排名表格说明：</strong><br>
                <strong>动量颜色含义：</strong><br>
                • <span style='color: #c62828;'>🔴 深红色</span>：超强动量（>5%）<br>
                • <span style='color: #b71c1c;'>🔴 红色</span>：强动量（2-5%）<br>
                • <span style='color: #ef6c00;'>🟠 橙色</span>：正动量（0-2%）<br>
                • <span style='color: #424242;'>⚪ 灰色</span>：轻微负动量（-2% 到 0%）<br>
                • <span style='color: #2e7d32;'>🟢 绿色</span>：负动量（-5% 到 -2%）<br>
                • <span style='color: #1b5e20;'>🟢 深绿色</span>：强负动量（<-5%）<br>
                <br>
                <strong>状态说明：</strong>✅ 推荐 = 符合动量策略条件，❌ 不符合条件 = 不满足策略要求
            </div>
            """, unsafe_allow_html=True)
            
            # 显示动量排名图
            st.subheader("📊 动量排名图")
            # 按动量排序（从高到低）
            sorted_data = sorted([(etf[0], etf[1], etf[4]*100) for etf in all_etfs_result if len(etf) >= 6], 
                                key=lambda x: x[2], reverse=True)
            etf_codes = [item[0] for item in sorted_data]
            etf_names = [item[1] for item in sorted_data]
            momentum_values = [item[2] for item in sorted_data]
            
            # 创建ETF代码+名称的标签
            etf_labels = [f"{code} {name}" for code, name in zip(etf_codes, etf_names)]
            
            # 使用plotly创建美观的横向柱状图
            import plotly.express as px
            import plotly.graph_objects as go
            
            # 创建横向柱状图数据
            chart_data_horizontal = pd.DataFrame({
                'ETF': etf_labels,
                '动量': momentum_values
            })
            
            # 为每个ETF添加颜色（涨为红色，跌为绿色）
            colors = ['#ff4444' if x > 0 else '#44aa44' for x in momentum_values]
            
            # 使用plotly.graph_objects创建更美观的图表
            fig = go.Figure()
            
            # 添加横向柱状图
            fig.add_trace(go.Bar(
                x=momentum_values,
                y=etf_labels,
                orientation='h',
                marker=dict(
                    color=colors,
                    line=dict(color='rgba(0,0,0,0.3)', width=1)
                ),
                text=[f'{x:.2f}%' for x in momentum_values],
                textposition='auto',
                hovertemplate='<b>%{y}</b><br>动量: %{x:.2f}%<extra></extra>'
            ))
            
            # 添加零线
            fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
            
            # 更新布局
            fig.update_layout(
                title=dict(
                    text='📊 ETF动量排名',
                    x=0.5,
                    font=dict(size=18, color='#2c3e50')
                ),
                xaxis=dict(
                    title="动量 (%)",
                    titlefont=dict(size=14, color='#34495e'),
                    tickfont=dict(size=12, color='#7f8c8d'),
                    gridcolor='rgba(128,128,128,0.2)',
                    zeroline=True,
                    zerolinecolor='rgba(128,128,128,0.5)'
                ),
                yaxis=dict(
                    title="ETF代码+名称",
                    titlefont=dict(size=14, color='#34495e'),
                    tickfont=dict(size=11, color='#2c3e50'),
                    gridcolor='rgba(128,128,128,0.1)'
                ),
                showlegend=False,
                height=max(400, len(etf_labels) * 25),  # 根据ETF数量动态调整高度
                margin=dict(l=20, r=20, t=60, b=20),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                hoverlabel=dict(
                    bgcolor="white",
                    font_size=12,
                    font_family="Arial"
                )
            )
            
            # 添加网格线
            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.1)')
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.1)')
            
            # 显示图表
            st.plotly_chart(fig, use_container_width=True)
            
            # 添加图表说明
            st.markdown("""
            <div style='background-color: #f8f9fa; padding: 10px; border-radius: 5px; border-left: 4px solid #28a745; margin-top: 15px;'>
                <strong>📈 图表说明：</strong><br>
                • <span style='color: #ff4444;'>🔴 红色</span>：正动量（上涨）<br>
                • <span style='color: #44aa44;'>🟢 绿色</span>：负动量（下跌）<br>
                • 图表按动量从高到低排序，动量最高的ETF显示在最上方
            </div>
            """, unsafe_allow_html=True)
    
    # 策略说明已移至页面顶部的折叠组件中

def render_cache_info(cache_meta):
    """
    渲染缓存信息
    
    Args:
        cache_meta: 缓存元数据
    """
    if cache_meta:
        st.sidebar.info(f"📅 数据更新时间: {cache_meta.get('update_time', '未知')}")
        st.sidebar.info(f" 数据来源: {cache_meta.get('source', '未知')}")

def small_log(message):
    """
    小日志函数
    
    Args:
        message: 日志消息
    """
    # 默认隐藏所有日志
    if not SHOW_CACHE_LOGS:
        return
    
    # 如果是缓存相关的日志且设置为不显示，则跳过
    if not SHOW_CACHE_LOGS and ("缓存" in message or "使用" in message and "数据" in message):
        return
    
    st.markdown(f"<div style='font-size:12px; color:#888;'>{message}</div>", unsafe_allow_html=True)

def calculate_momentum(etf_code, period=20, ma_period=20):
    """
    计算单个ETF的动量
    
    Args:
        etf_code: ETF代码
        period: 动量计算周期
        ma_period: 移动平均周期
    
    Returns:
        momentum_data: 动量数据字典
    """
    try:
        # 获取ETF数据
        if etf_code.endswith('.SH') or etf_code.endswith('.SZ'):
            etf_code = etf_code[:-3]  # 移除交易所后缀
        
        # 获取历史数据
        df = ak.fund_etf_hist_sina(symbol=etf_code)
        
        if df.empty:
            return None
        
        # 计算技术指标
        df['MA'] = df['close'].rolling(window=ma_period).mean()
        df['动量'] = df['close'].pct_change(periods=period)
        df['成交量变化'] = df['volume'].pct_change(periods=period)
        
        # 获取最新数据
        latest = df.iloc[-1]
        prev = df.iloc[-period-1] if len(df) > period else df.iloc[0]
        
        # 计算动量得分
        price_momentum = (latest['close'] - prev['close']) / prev['close']
        volume_momentum = latest['volume'] / df['volume'].rolling(window=period).mean().iloc[-1]
        ma_momentum = (latest['close'] - latest['MA']) / latest['MA']
        
        # 综合动量得分
        momentum_score = (price_momentum * 0.5 + 
                         (volume_momentum - 1) * 0.3 + 
                         ma_momentum * 0.2)
        
        return {
            'ETF代码': etf_code,
            '当前价格': latest['close'],
            '涨跌幅': price_momentum * 100,
            '成交量': latest['volume'],
            '动量得分': momentum_score,
            'MA': latest['MA'],
            '成交量变化': (volume_momentum - 1) * 100
        }
        
    except Exception as e:
        small_log(f"计算ETF {etf_code} 动量时出错: {str(e)}")
        return None

def auto_calculate_momentum(selected_etfs, momentum_period, ma_period, etf_pool):
    """
    自动计算动量
    
    Args:
        selected_etfs: 选择的ETF列表
        momentum_period: 动量周期
        ma_period: 均线周期
        etf_pool: ETF池字典
    
    Returns:
        momentum_results: 动量计算结果DataFrame
    """
    if not selected_etfs:
        st.warning("请选择至少一只ETF")
        return None
    
    momentum_results = []
    
    with st.spinner("正在计算动量..."):
        for etf_code in selected_etfs:
            result = calculate_momentum(etf_code, momentum_period, ma_period)
            if result:
                momentum_results.append(result)
    
    if not momentum_results:
        st.error("所有ETF计算失败，请检查网络连接或ETF代码")
        return None
    
    return pd.DataFrame(momentum_results)

def backtest_strategy(etf_list, etf_names, start_date, end_date, momentum_period=20, ma_period=28, max_positions=2):
    """
    回测动量策略
    
    Args:
        etf_list: ETF代码列表
        etf_names: ETF名称字典
        start_date: 开始日期
        end_date: 结束日期
        momentum_period: 动量周期
        ma_period: 均线周期
        max_positions: 最大持仓数量
    
    Returns:
        backtest_results: 回测结果字典
        trade_history: 交易历史
        holdings_history: 持仓历史
    """
    # 转换日期类型
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    
    # 获取所有ETF的历史数据
    etf_data = {}
    for symbol in etf_list:
        try:
            df = fetch_etf_data(symbol)
            if df.empty:
                continue
            # 筛选时间范围
            df = df[(df.index >= start_date) & (df.index <= end_date)]
            if len(df) < max(momentum_period, ma_period) + 10:  # 确保有足够的数据
                continue
            df = calculate_momentum_and_ma(df, momentum_period, ma_period)
            etf_data[symbol] = df
        except Exception as e:
            small_log(f"处理{symbol}数据失败: {e}")
            continue
    
    if len(etf_data) < 2:
        small_log("可用ETF数量不足2只，无法回测")
        return None, None, None
    
    # 获取所有ETF的共同日期
    common_dates = None
    for symbol, df in etf_data.items():
        if common_dates is None:
            common_dates = set(df.index)
        else:
            common_dates = common_dates.intersection(set(df.index))
    
    if len(common_dates) < 30:
        small_log("共同交易日不足30天，无法回测")
        return None, None, None
    
    common_dates = sorted(list(common_dates))
    
    # 回测逻辑
    # 初始化投资组合净值，从第一个有效交易日开始
    start_index = max(momentum_period, ma_period)
    portfolio_values = [1.0]  # 初始净值1.0
    holdings_history = []  # 持仓历史
    trade_history = []  # 交易历史
    
    current_holdings = set()  # 当前持仓
    
    for i, date in enumerate(common_dates):
        if i < start_index:
            # 前N天数据不足，跳过
            continue
        
        # 计算当日动量排名
        momentums = {}
        candidates = []
        
        for symbol, df in etf_data.items():
            if date in df.index:
                row = df.loc[date]
                if not pd.isna(row['Close']) and not pd.isna(row['MA']) and not pd.isna(row['Momentum']):
                    if row['Close'] > row['MA']:
                        candidates.append(symbol)
                        momentums[symbol] = row['Momentum']
        
        # 按动量排序，取前N名
        if candidates:
            sorted_candidates = sorted(candidates, key=lambda x: momentums[x], reverse=True)
            top_candidates = sorted_candidates[:max_positions]
            
            # 检查是否需要调仓
            to_sell = current_holdings - set(top_candidates)
            to_buy = set(top_candidates) - current_holdings
            
            # 记录交易
            for etf in to_sell:
                trade_history.append({
                    '日期': date.strftime('%Y-%m-%d'),
                    'ETF代码': etf,
                    'ETF名称': etf_names[etf],
                    '操作': '卖出',
                    '价格': etf_data[etf].loc[date, 'Close']
                })
            
            for etf in to_buy:
                trade_history.append({
                    '日期': date.strftime('%Y-%m-%d'),
                    'ETF代码': etf,
                    'ETF名称': etf_names[etf],
                    '操作': '买入',
                    '价格': etf_data[etf].loc[date, 'Close']
                })
            
            # 更新持仓
            current_holdings = set(top_candidates)
        else:
            # 没有符合条件的ETF，清仓
            for etf in current_holdings:
                trade_history.append({
                    '日期': date.strftime('%Y-%m-%d'),
                    'ETF代码': etf,
                    'ETF名称': etf_names[etf],
                    '操作': '卖出',
                    '价格': etf_data[etf].loc[date, 'Close']
                })
            current_holdings = set()
        
        # 记录持仓
        holdings_history.append({
            '日期': date.strftime('%Y-%m-%d'),
            '持仓ETF': list(current_holdings),
            '持仓数量': len(current_holdings)
        })
        
        # 计算当日收益
        if i > 0 and current_holdings:
            # 计算持仓ETF的平均收益
            daily_returns = []
            for etf in current_holdings:
                if i > 0:
                    prev_date = common_dates[i-1]
                    if prev_date in etf_data[etf].index and date in etf_data[etf].index:
                        prev_price = etf_data[etf].loc[prev_date, 'Close']
                        curr_price = etf_data[etf].loc[date, 'Close']
                        if prev_price > 0:
                            daily_return = (curr_price / prev_price - 1)
                            daily_returns.append(daily_return)
            
            if daily_returns:
                # 计算平均收益
                avg_daily_return = sum(daily_returns) / len(daily_returns)
                portfolio_values.append(portfolio_values[-1] * (1 + avg_daily_return))
            else:
                portfolio_values.append(portfolio_values[-1])
        else:
            portfolio_values.append(portfolio_values[-1])
    
    # 计算回测指标
    if len(portfolio_values) > 1:
        # 确保首末净值与日期一一对应
        start_value = portfolio_values[0]
        end_value = portfolio_values[-1]
        total_return = (end_value / start_value - 1) * 100
        # 使用正确的起始日期计算天数
        start_date_index = max(momentum_period, ma_period)
        days = (common_dates[-1] - common_dates[start_date_index]).days
        annual_return = calculate_annual_return(start_value, end_value, days)
        max_drawdown = calculate_max_drawdown(portfolio_values)
        sharpe_ratio = calculate_sharpe_ratio(portfolio_values)
    else:
        total_return = 0
        annual_return = 0
        max_drawdown = 0
        sharpe_ratio = 0
    
    return {
        'portfolio_values': portfolio_values,
        'dates': [d.strftime('%Y-%m-%d') for d in common_dates[max(momentum_period, ma_period):]],
        'total_return': total_return,  # 总收益率=首末净值之比-1
        'annual_return': annual_return,
        'max_drawdown': max_drawdown,
        'sharpe_ratio': sharpe_ratio,
        'trade_count': len(trade_history)
    }, trade_history, holdings_history

def render_backtest_results(backtest_results, trade_history, holdings_history):
    """
    渲染回测结果
    
    Args:
        backtest_results: 回测结果字典
        trade_history: 交易历史
        holdings_history: 持仓历史
    """
    if not backtest_results:
        st.warning("暂无回测结果")
        return
    
    st.subheader("📊 回测结果")
    
    # 显示关键指标
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("总收益率", f"{backtest_results['total_return']:.2f}%")
    with col2:
        st.metric("年化收益率", f"{backtest_results['annual_return']:.2f}%")
    with col3:
        st.metric("最大回撤", f"{backtest_results['max_drawdown']:.2f}%")
    with col4:
        st.metric("夏普比率", f"{backtest_results['sharpe_ratio']:.2f}")
    
    # 显示净值曲线
    if 'portfolio_values' in backtest_results and 'dates' in backtest_results:
        st.subheader("📈 净值曲线")
        chart_data = pd.DataFrame({
            '日期': backtest_results['dates'],
            '净值': backtest_results['portfolio_values']
        })
        chart_data['日期'] = pd.to_datetime(chart_data['日期'])
        chart_data = chart_data.set_index('日期')
        
        st.line_chart(chart_data, use_container_width=True)
    
    # 显示交易历史
    if trade_history:
        st.subheader("📋 交易历史")
        trade_df = pd.DataFrame(trade_history)
        # 显示表格，不设置高度避免滚动条
        st.dataframe(trade_df, use_container_width=True)
    
    # 显示持仓历史
    if holdings_history:
        st.subheader("📊 持仓历史")
        holdings_df = pd.DataFrame(holdings_history)
        # 显示表格，不设置高度避免滚动条
        st.dataframe(holdings_df, use_container_width=True)

def get_bias_status(bias_6, bias_12, bias_24):
    """
    获取偏离状态
    
    Args:
        bias_6: 6日偏离度
        bias_12: 12日偏离度
        bias_24: 24日偏离度
    
    Returns:
        status: 偏离状态描述
    """
    if bias_6 > 0 and bias_12 > 0 and bias_24 > 0:
        return "强势上涨"
    elif bias_6 < 0 and bias_12 < 0 and bias_24 < 0:
        return "强势下跌"
    elif bias_6 > 0 and bias_12 < 0:
        return "短期反弹"
    elif bias_6 < 0 and bias_12 > 0:
        return "短期回调"
    else:
        return "震荡整理"

def calculate_dynamic_threshold(bias_values, multiplier=2.0):
    """
    计算动态阈值
    
    Args:
        bias_values: 偏离度值列表
        multiplier: 倍数
    
    Returns:
        threshold: 动态阈值
    """
    if bias_values is None or len(bias_values) == 0:
        return 0
    
    # 确保输入是数值数组
    if hasattr(bias_values, 'values'):
        bias_values = bias_values.values
    
    # 过滤掉NaN值
    bias_values = [x for x in bias_values if not pd.isna(x)]
    
    if len(bias_values) == 0:
        return 0
    
    mean_bias = np.mean(bias_values)
    std_bias = np.std(bias_values)
    
    return mean_bias + multiplier * std_bias

def calculate_bias(df, period=6):
    """
    计算偏离度 (BIAS)
    
    Args:
        df: 包含价格数据的DataFrame
        period: 计算周期
    
    Returns:
        bias: 偏离度值
    """
    if len(df) < period:
        return None
    
    # 计算移动平均线
    ma = df['Close'].rolling(window=period).mean()
    
    # 计算偏离度: (收盘价 - 移动平均线) / 移动平均线 * 100
    bias = (df['Close'] - ma) / ma * 100
    
    return bias

def calculate_bias_analysis(df, periods=[6, 12, 24]):
    """
    计算多周期偏离度分析
    
    Args:
        df: 包含价格数据的DataFrame
        periods: 计算周期列表
    
    Returns:
        bias_data: 偏离度分析数据字典
    """
    bias_data = {}
    
    for period in periods:
        bias = calculate_bias(df, period)
        if bias is not None:
            bias_data[f'BIAS_{period}'] = bias
    
    return bias_data

def render_bias_analysis(etf_code, etf_name, df, periods=[6, 12, 24]):
    """
    渲染偏离度分析结果
    
    Args:
        etf_code: ETF代码
        etf_name: ETF名称
        df: 价格数据
        periods: 分析周期
    """
    st.subheader(f"🔍 {etf_code} - {etf_name} 偏离度分析")
    
    # 计算偏离度
    bias_data = calculate_bias_analysis(df, periods)
    
    if not bias_data:
        st.warning("数据不足，无法计算偏离度")
        return
    
    # 获取最新值
    latest_bias = {}
    for period, bias in bias_data.items():
        if not bias.empty:
            latest_bias[period] = bias.iloc[-1]
    
    # 显示最新偏离度值
    cols = st.columns(len(latest_bias))
    for i, (period, value) in enumerate(latest_bias.items()):
        with cols[i]:
            period_num = period.split('_')[1]
            st.metric(f"{period_num}日偏离度", f"{value:.2f}%")
    
    # 判断偏离状态
    if len(latest_bias) >= 3:
        bias_6 = latest_bias.get('BIAS_6', 0)
        bias_12 = latest_bias.get('BIAS_12', 0)
        bias_24 = latest_bias.get('BIAS_24', 0)
        
        status = get_bias_status(bias_6, bias_12, bias_24)
        
        # 根据状态显示不同的颜色
        if "强势上涨" in status:
            st.success(f"📈 当前状态: {status}")
        elif "强势下跌" in status:
            st.error(f"📉 当前状态: {status}")
        elif "反弹" in status:
            st.warning(f"🔄 当前状态: {status}")
        elif "回调" in status:
            st.info(f"📊 当前状态: {status}")
        else:
            st.info(f"📊 当前状态: {status}")
    
    # 显示偏离度趋势图
    st.subheader("📈 偏离度趋势")
    
    # 准备图表数据
    chart_data = pd.DataFrame(bias_data)
    chart_data.index = df.index
    
    # 绘制偏离度趋势线
    st.line_chart(chart_data, use_container_width=True)
    
    # 显示偏离度统计信息
    st.subheader("📊 偏离度统计")
    
    stats_data = []
    for period, bias in bias_data.items():
        if not bias.empty:
            period_num = period.split('_')[1]
            stats_data.append({
                '周期': f"{period_num}日",
                '当前值': f"{bias.iloc[-1]:.2f}%",
                '最大值': f"{bias.max():.2f}%",
                '最小值': f"{bias.min():.2f}%",
                '平均值': f"{bias.mean():.2f}%",
                '标准差': f"{bias.std():.2f}%"
            })
    
    if stats_data:
        stats_df = pd.DataFrame(stats_data)
        # 显示表格，不设置高度避免滚动条
        st.dataframe(stats_df, use_container_width=True)
    
    # 显示动态阈值分析
    st.subheader("🎯 动态阈值分析")
    
    for period, bias in bias_data.items():
        if not bias.empty:
            period_num = period.split('_')[1]
            current_bias = bias.iloc[-1]
            
            # 计算动态阈值
            threshold_1 = calculate_dynamic_threshold(bias.values, 1.0)
            threshold_2 = calculate_dynamic_threshold(bias.values, 2.0)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(f"{period_num}日偏离度", f"{current_bias:.2f}%")
            with col2:
                st.metric("1σ阈值", f"{threshold_1:.2f}%")
            with col3:
                st.metric("2σ阈值", f"{threshold_2:.2f}%")
            
            # 判断是否超阈值
            if abs(current_bias) > threshold_2:
                st.warning(f"⚠️ {period_num}日偏离度超过2σ阈值，可能存在超买超卖")
            elif abs(current_bias) > threshold_1:
                st.info(f"ℹ️ {period_num}日偏离度超过1σ阈值，需要关注")
            else:
                st.success(f"✅ {period_num}日偏离度在正常范围内")

def render_simplified_bias_table(etf_list, etf_names, periods=[6, 12, 24]):
    """
    渲染Bias分析表格（所有标的在一个表格中）
    
    Args:
        etf_list: ETF代码列表
        etf_names: ETF名称字典
        periods: 分析周期
    """
    bias_results = []
    
    for etf_code in etf_list:
        try:
            # 获取ETF数据
            df = fetch_etf_data(etf_code)
            if df.empty:
                continue
                
            # 计算偏离度
            bias_data = calculate_bias_analysis(df, periods)
            
            if not bias_data:
                continue
            
            # 获取最新值
            etf_bias = {'ETF代码': etf_code, 'ETF名称': etf_names.get(etf_code, etf_code)}
            
            for period, bias in bias_data.items():
                if not bias.empty:
                    period_num = period.split('_')[1]
                    etf_bias[f'{period_num}日偏离度'] = f"{bias.iloc[-1]:.2f}%"
            
            # 判断偏离状态
            if len(etf_bias) >= 5:  # 至少有6日、12日偏离度
                bias_6 = float(etf_bias.get('6日偏离度', '0%').rstrip('%'))
                bias_12 = float(etf_bias.get('12日偏离度', '0%').rstrip('%'))
                bias_24 = float(etf_bias.get('24日偏离度', '0%').rstrip('%'))
                
                # 添加超买超卖结论
                conclusion_result = get_bias_conclusion(bias_6, bias_12, bias_24)
                if isinstance(conclusion_result, tuple):
                    conclusion, status = conclusion_result
                else:
                    conclusion = conclusion_result
                    status = "info"
                etf_bias['超买超卖结论'] = conclusion
            
            bias_results.append(etf_bias)
            
        except Exception as e:
            small_log(f"计算{etf_code}偏离度失败: {e}")
            continue
    
    if bias_results:
        # 创建DataFrame
        bias_df = pd.DataFrame(bias_results)
        
        # 重新排序列
        columns_order = ['ETF代码', 'ETF名称']
        for period in periods:
            columns_order.append(f'{period}日偏离度')
        columns_order.append('超买超卖结论')
        
        # 确保所有列都存在
        for col in columns_order:
            if col not in bias_df.columns:
                bias_df[col] = '-'
        
        # 按列顺序重新排列
        bias_df = bias_df[columns_order]
        
        # 美化表格显示
        def style_bias_table(df):
            """美化Bias分析表格"""
            def color_bias_values(val):
                """为偏离度值添加颜色"""
                if isinstance(val, str) and '%' in val:
                    try:
                        bias_value = float(val.rstrip('%'))
                        if bias_value > 5:
                            return 'background-color: #ffebee; color: #c62828; font-weight: bold'  # 超买：浅红色
                        elif bias_value > 2:
                            return 'background-color: #fff3e0; color: #ef6c00; font-weight: bold'  # 偏超买：浅橙色
                        elif bias_value < -5:
                            return 'background-color: #e8f5e8; color: #2e7d32; font-weight: bold'  # 超卖：浅绿色
                        elif bias_value < -2:
                            return 'background-color: #f3e5f5; color: #7b1fa2; font-weight: bold'  # 偏超卖：浅紫色
                        else:
                            return 'background-color: #f5f5f5; color: #424242; font-weight: bold'  # 正常：浅灰色
                    except:
                        return ''
                return ''
            
            def color_conclusion(val):
                """为超买超卖结论添加颜色"""
                if isinstance(val, str):
                    if '🔴' in val or '超买' in val:
                        return 'background-color: #ffebee; color: #c62828; font-weight: bold'
                    elif '🟢' in val or '超卖' in val:
                        return 'background-color: #e8f5e8; color: #2e7d32; font-weight: bold'
                    elif '🟡' in val or '偏超买' in val:
                        return 'background-color: #fff3e0; color: #ef6c00; font-weight: bold'
                    elif '🟠' in val or '偏超卖' in val:
                        return 'background-color: #f3e5f5; color: #7b1fa2; font-weight: bold'
                    elif '⚪' in val or '正常' in val:
                        return 'background-color: #f5f5f5; color: #424242; font-weight: bold'
                return ''
            
            # 应用样式
            styled_df = df.style.map(color_bias_values, subset=[col for col in df.columns if '偏离度' in col])
            styled_df = styled_df.map(color_conclusion, subset=['超买超卖结论'])
            
            return styled_df
        
        # 应用美化样式
        styled_bias_df = style_bias_table(bias_df)
        
        # 显示美化后的表格
        st.dataframe(styled_bias_df, use_container_width=True)
        
        # 添加表格说明
        st.markdown("""
        <div style='background-color: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #007bff; margin-top: 15px;'>
            <strong>📊 Bias分析说明：</strong><br>
            <strong>偏离度颜色含义：</strong><br>
            • <span style='color: #c62828;'>🔴 深红色</span>：超买（>5%）<br>
            • <span style='color: #ef6c00;'>🟠 橙色</span>：偏超买（2-5%）<br>
            • <span style='color: #424242;'>⚪ 灰色</span>：正常（-2% 到 2%）<br>
            • <span style='color: #7b1fa2;'>🟣 紫色</span>：偏超卖（-5% 到 -2%）<br>
            • <span style='color: #2e7d32;'>🟢 深绿色</span>：超卖（<-5%）<br>
            <br>
            <strong>超买超卖结论：</strong>基于6日、12日、24日偏离度的综合判断
        </div>
        """, unsafe_allow_html=True)
        
    else:
        st.warning("无法获取Bias分析数据")

def render_enhanced_momentum_results(selected_etfs_result, all_etfs_result, etf_pool, momentum_period, ma_period, max_positions):
    """
    渲染增强版动量策略结果（包含更多分析信息）
    
    Args:
        selected_etfs_result: 选中的ETF结果
        all_etfs_result: 所有ETF结果
        etf_pool: ETF池字典
        momentum_period: 动量周期
        ma_period: 均线周期
        max_positions: 最大持仓数量
    """
    st.subheader("📊 增强版动量策略分析结果")
    
    # 显示策略参数
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("动量周期", momentum_period)
    with col2:
        st.metric("均线周期", ma_period)
    with col3:
        st.metric("最大持仓", max_positions)
        
        # 显示选中的ETF（仅显示标题，不显示文字提示）
        if selected_etfs_result:
            st.subheader("🎯 推荐持仓")
            
            # 构建推荐的ETF列表
            etf_list = []
            for i, etf_info in enumerate(selected_etfs_result, 1):
                etf_code = etf_info[0]  # 第一个元素是ETF代码
                etf_name = etf_info[1]  # 第二个元素是ETF名称
                etf_list.append(f"{i}. {etf_code} - {etf_name}")
            
            etf_list_text = "\n".join(etf_list)
            
            # 添加策略说明
            st.info(f"""
**📋 持仓策略说明：**

• **默认推荐前两名**：系统基于动量策略自动选择动量最强且趋势向上的前2只ETF
• **缓冲机制**：可以持有前三名，提供一定的缓冲空间
• **调仓条件**：只有当ETF掉到第四名时才进行调仓
• **风险控制**：结合价格与均线关系，确保趋势向上

**🎯 当前推荐标的：**
{etf_list_text}

**💡 操作建议：**
- 当前持仓：{len(selected_etfs_result)}只ETF
- 建议：可以适当持有第3名ETF作为缓冲
- 调仓时机：关注排名变化，避免频繁交易
            """)
    
    # 显示所有ETF的排名
    if all_etfs_result:
        st.subheader("📈 所有ETF动量排名")
        # 创建所有ETF的表格
        all_data = []
        for etf in all_etfs_result:
            if len(etf) >= 6:
                status = "✅ 推荐" if etf[5] else "❌ 不符合条件"
                all_data.append({
                    'ETF代码': etf[0],
                    'ETF名称': etf[1],
                    '当前价格': f"{etf[2]:.4f}",
                    '均线价格': f"{etf[3]:.4f}",
                    '动量': f"{etf[4]*100:.2f}%",
                    '价格-均线': f"{etf[2] - etf[3]:.4f}",
                    '状态': status
                })
        
        if all_data:
            all_df = pd.DataFrame(all_data)
            # 显示表格，不设置高度避免滚动条
            st.dataframe(all_df, use_container_width=True)
            
            # 显示动量对比柱状图
            st.subheader("📊 动量对比")
            # 按动量排序（从高到低）
            sorted_data = sorted([(etf[0], etf[4]*100) for etf in all_etfs_result if len(etf) >= 6],
                                key=lambda x: x[1], reverse=True)
            etf_codes = [item[0] for item in sorted_data]
            momentum_values = [item[1] for item in sorted_data]
            
            chart_data = pd.DataFrame({
                'ETF': etf_codes,
                '动量': momentum_values
            })
            
            # 确保图表按排序后的数据显示
            st.bar_chart(chart_data.set_index('ETF'), use_container_width=True)
    
    # 显示策略说明
    st.subheader("💡 策略说明")
    st.markdown("""
    **增强版动量策略逻辑：**
    1. **动量计算**: 计算各ETF在{momentum_period}天内的价格变化百分比
    2. **趋势过滤**: 使用{ma_period}天移动平均线过滤下跌趋势
    3. **持仓选择**: 选择动量最强（涨幅最大）且趋势向上的ETF
    4. **动态调整**: 定期重新计算并调整持仓
    5. **风险控制**: 结合价格与均线关系进行风险控制
    
    **当前参数设置：**
    - 动量周期：{momentum_period}天（计算价格变化百分比）
    - 均线周期：{ma_period}天（趋势过滤）
    - 最大持仓：{max_positions}只
    """.format(momentum_period=momentum_period, ma_period=ma_period, max_positions=max_positions))

def get_bias_conclusion(bias_6, bias_12, bias_24):
    """
    获取超买超卖结论
    
    Args:
        bias_6: 6日偏离度
        bias_12: 12日偏离度
        bias_24: 24日偏离度
    
    Returns:
        conclusion: 超买超卖结论
    """
    try:
        # 使用动态阈值判断
        # 计算动态阈值（基于历史数据，这里使用固定阈值作为示例）
        upper_6, upper_12, upper_24 = 5.0, 3.0, 2.0  # 超买阈值
        lower_6, lower_12, lower_24 = -5.0, -3.0, -2.0  # 超卖阈值
        
        if bias_6 > upper_6 and bias_12 > upper_12 and bias_24 > upper_24:
            return f"🔴 超买 (6日:{bias_6:.1f}%>{upper_6:.1f}%)", "danger"
        elif bias_6 < lower_6 and bias_12 < lower_12 and bias_24 < lower_24:
            return f"🟢 超卖 (6日:{bias_6:.1f}%<{lower_6:.1f}%)", "success"
        elif bias_6 > upper_6 * 0.8 or bias_12 > upper_12 * 0.8:
            return f"🟡 偏超买 (6日:{bias_6:.1f}%)", "warning"
        elif bias_6 < lower_6 * 0.8 or bias_12 < lower_12 * 0.8:
            return f"🟠 偏超卖 (6日:{bias_6:.1f}%)", "warning"
        else:
            return f"⚪ 正常 (6日:{bias_6:.1f}%)", "info"
            
    except:
        # 如果动态计算失败，使用传统固定阈值
        if bias_6 > 5 and bias_12 > 3 and bias_24 > 2:
            return "🔴 超买", "danger"
        elif bias_6 < -5 and bias_12 < -3 and bias_24 < -2:
            return "🔴 超卖", "success"
        elif bias_6 > 3 or bias_12 > 2:
            return "🟡 偏超买", "warning"
        elif bias_6 < -3 or bias_12 < -2:
            return "🟠 偏超卖", "warning"
        else:
            return "⚪ 正常", "info"

def show_bias_statistics(bias_results):
    """
    显示偏离度统计信息
    
    Args:
        bias_results: 偏离度结果列表
    """
    if not bias_results:
        return
    
    # 统计超买超卖情况
    overbought_count = 0
    oversold_count = 0
    normal_count = 0
    
    for result in bias_results:
        conclusion = result.get('超买超卖结论', '')
        if '超买' in conclusion:
            overbought_count += 1
        elif '超卖' in conclusion:
            oversold_count += 1
        else:
            normal_count += 1
    
    # 显示统计信息
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if overbought_count > 0:
            st.metric("🔥 超买标的", f"{overbought_count}只", delta=f"{overbought_count/len(bias_results)*100:.1f}%")
        else:
            st.metric("🔥 超买标的", "0只")
    
    with col2:
        if oversold_count > 0:
            st.metric("💧 超卖标的", f"{oversold_count}只", delta=f"{oversold_count/len(bias_results)*100:.1f}%")
        else:
            st.metric("💧 超卖标的", "0只")
    
    with col3:
        st.metric("⚖️ 正常标的", f"{normal_count}只", delta=f"{normal_count/len(bias_results)*100:.1f}%")
    
    # 显示投资建议
    st.subheader("💡 投资建议")
    
    if overbought_count > len(bias_results) * 0.3:
        st.warning("🚨 市场整体偏热，建议谨慎操作，注意风险控制")
    elif oversold_count > len(bias_results) * 0.3:
        st.success("🎯 市场整体偏冷，可能存在投资机会，建议关注超卖标的")
    else:
        st.info("📊 市场整体平衡，建议根据个股情况灵活操作")
    
    # 显示具体建议
    if overbought_count > 0:
        st.markdown("**超买标的建议：**")
        for result in bias_results:
            conclusion = result.get('超买超卖结论', '')
            if '超买' in conclusion:
                st.markdown(f"- {result['ETF代码']} {result['ETF名称']}: {conclusion} - 建议减仓或观望")
    
    if oversold_count > 0:
        st.markdown("**超卖标的建议：**")
        for result in bias_results:
            conclusion = result.get('超买超卖结论', '')
            if '超卖' in conclusion:
                st.markdown(f"- {result['ETF代码']} {result['ETF名称']}: {conclusion} - 可考虑逢低布局")

def render_etf_trend_chart(etf_list, etf_names, periods=[6, 12, 24]):
    """
    渲染所有ETF近一年累计涨跌幅趋势图（所有标的在同一张图上）
    
    Args:
        etf_list: ETF代码列表
        etf_names: ETF名称字典
        periods: 分析周期（用于计算偏离度）
    """
    st.subheader("📈 所有ETF近一年累计涨跌幅趋势")
    
    try:
        # 收集所有ETF的数据
        etf_data = {}
        valid_etfs = []
        
        for etf_code in etf_list:
            try:
                # 获取ETF数据
                df = fetch_etf_data(etf_code)
                if df.empty or len(df) < 250:
                    small_log(f"{etf_code} 数据不足，跳过")
                    continue
                
                # 获取近一年的数据
                one_year_ago = df.index[-1] - pd.Timedelta(days=365)
                df_recent = df[df.index >= one_year_ago].copy()
                
                if len(df_recent) < 100:
                    small_log(f"{etf_code} 近一年数据不足，跳过")
                    continue
                
                # 计算累计涨跌幅（以一年前为基准）
                base_price = df_recent.iloc[0]['Close']
                df_recent['累计涨跌幅'] = (df_recent['Close'] / base_price - 1) * 100
                
                # 验证数据有效性
                if pd.isna(df_recent['累计涨跌幅']).all() or df_recent['累计涨跌幅'].isnull().all():
                    small_log(f"{etf_code} 累计涨跌幅计算失败，跳过")
                    continue
                
                etf_data[etf_code] = df_recent
                valid_etfs.append(etf_code)
                small_log(f"{etf_code} 数据获取成功，共{len(df_recent)}个交易日")
                
            except Exception as e:
                small_log(f"获取{etf_code}数据失败: {e}")
                continue
        
        if not valid_etfs:
            st.warning("无法获取任何ETF数据")
            return
        
        small_log(f"成功获取{len(valid_etfs)}只ETF的数据")
        
        # 创建累计涨跌幅趋势图
        import plotly.graph_objects as go
        
        fig = go.Figure()
        
        # 为每个ETF添加累计涨跌幅曲线
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']
        
        for i, etf_code in enumerate(valid_etfs):
            df_recent = etf_data[etf_code]
            etf_name = etf_names.get(etf_code, etf_code)
            color = colors[i % len(colors)]
            
            fig.add_trace(
                go.Scatter(
                    x=df_recent.index,
                    y=df_recent['累计涨跌幅'],
                    mode='lines',
                    name=f'{etf_code} {etf_name}',
                    line=dict(color=color, width=2),
                    hovertemplate=f'{etf_code} {etf_name}<br>日期: %{{x}}<br>累计涨跌幅: %{{y:.2f}}%<extra></extra>'
                )
            )
        
        # 添加零线
        fig.add_hline(y=0, line_dash="dash", line_color="gray", line_width=1)
        
        # 更新布局
        fig.update_layout(
            title='所有ETF近一年累计涨跌幅对比',
            xaxis_title="日期",
            yaxis_title="累计涨跌幅 (%)",
            height=500,
            showlegend=True,
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # 显示图表
        st.plotly_chart(fig, use_container_width=True)
        
        # 计算并显示对比表格
        st.subheader("📊 近一年表现对比")
        
        comparison_data = []
        successful_etfs = []  # 记录成功计算指标的ETF
        
        for etf_code in valid_etfs:
            df_recent = etf_data[etf_code]
            etf_name = etf_names.get(etf_code, etf_code)
            
            try:
                # 计算关键指标
                current_return = df_recent['累计涨跌幅'].iloc[-1]
                max_return = df_recent['累计涨跌幅'].max()
                min_return = df_recent['累计涨跌幅'].min()
                
                # 计算最大回撤
                cumulative_returns = (1 + df_recent['累计涨跌幅'] / 100)
                running_max = cumulative_returns.expanding().max()
                drawdown = (cumulative_returns / running_max - 1) * 100
                max_drawdown = drawdown.min()
                
                # 计算夏普比率（基于价格变化，不是累计涨跌幅变化）
                price_returns = df_recent['Close'].pct_change().dropna()
                if len(price_returns) > 0 and price_returns.std() != 0:
                    # 年化收益率
                    annual_return = price_returns.mean() * 252
                    # 年化波动率
                    annual_volatility = price_returns.std() * np.sqrt(252)
                    # 夏普比率（假设无风险利率为3%）
                    risk_free_rate = 0.03
                    sharpe_ratio = (annual_return - risk_free_rate) / annual_volatility if annual_volatility != 0 else 0
                else:
                    sharpe_ratio = 0
                
                # 计算年化波动率
                volatility = price_returns.std() * np.sqrt(252) * 100 if len(price_returns) > 0 else 0
                
                # 验证数据有效性
                if pd.isna(current_return) or pd.isna(max_return) or pd.isna(min_return) or pd.isna(max_drawdown):
                    small_log(f"{etf_code} 指标计算包含NaN值，跳过")
                    continue
                
                # 验证数值的合理性
                if not (isinstance(current_return, (int, float)) and isinstance(max_return, (int, float)) and 
                       isinstance(min_return, (int, float)) and isinstance(max_drawdown, (int, float))):
                    small_log(f"{etf_code} 指标类型不正确，跳过")
                    continue
                
                comparison_data.append({
                    'ETF代码': etf_code,
                    'ETF名称': etf_name,
                    '当前累计涨跌幅': f"{current_return:.2f}%",
                    '期间最高涨幅': f"{max_return:.2f}%",
                    '期间最大跌幅': f"{min_return:.2f}%",
                    '最大回撤': f"{max_drawdown:.2f}%",
                    '夏普比率': f"{sharpe_ratio:.2f}",
                    '年化波动率': f"{volatility:.2f}%"
                })
                
                successful_etfs.append(etf_code)
                small_log(f"{etf_code} 指标计算成功")
                
            except Exception as e:
                small_log(f"计算{etf_code}指标失败: {e}")
                continue
        
        # 创建对比表格
        if comparison_data:
            comparison_df = pd.DataFrame(comparison_data)
            
            # 再次验证数据完整性
            comparison_df = comparison_df.dropna(how='any')
            
            if len(comparison_df) == 0:
                st.warning("所有ETF指标计算失败")
                return
            
            small_log(f"成功计算{len(comparison_df)}只ETF的指标，成功列表: {successful_etfs}")
            
            # 应用表格样式
            def style_performance_table(df):
                """美化近一年表现对比表格"""
                
                def color_return_values(val):
                    """为涨跌幅添加颜色"""
                    if isinstance(val, str) and '%' in val:
                        try:
                            return_value = float(val.rstrip('%'))
                            if return_value > 10:
                                return 'background-color: #ffebee; color: #c62828; font-weight: bold; border-radius: 4px; padding: 4px 8px;'  # 超强表现：深红色
                            elif return_value > 5:
                                return 'background-color: #ffcdd2; color: #b71c1c; font-weight: bold; border-radius: 4px; padding: 4px 8px;'  # 强表现：红色
                            elif return_value > 0:
                                return 'background-color: #fff3e0; color: #ef6c00; font-weight: bold; border-radius: 4px; padding: 4px 8px;'  # 正表现：橙色
                            elif return_value > -5:
                                return 'background-color: #f5f5f5; color: #424242; font-weight: bold; border-radius: 4px; padding: 4px 8px;'  # 轻微负表现：灰色
                            elif return_value > -10:
                                return 'background-color: #e8f5e8; color: #2e7d32; font-weight: bold; border-radius: 4px; padding: 4px 8px;'  # 负表现：绿色
                            else:
                                return 'background-color: #c8e6c9; color: #1b5e20; font-weight: bold; border-radius: 4px; padding: 4px 8px;'  # 强负表现：深绿色
                        except:
                            return ''
                    return ''
                
                def color_sharpe_values(val):
                    """为夏普比率添加颜色"""
                    if isinstance(val, str):
                        try:
                            sharpe_value = float(val)
                            if sharpe_value > 1.5:
                                return 'background-color: #e8f5e8; color: #2e7d32; font-weight: bold; border-radius: 4px; padding: 4px 8px; border: 2px solid #4caf50;'  # 优秀：绿色
                            elif sharpe_value > 0.5:
                                return 'background-color: #fff3e0; color: #ef6c00; font-weight: bold; border-radius: 4px; padding: 4px 8px; border: 2px solid #ff9800;'  # 良好：橙色
                            elif sharpe_value > 0:
                                return 'background-color: #f5f5f5; color: #424242; font-weight: bold; border-radius: 4px; padding: 4px 8px; border: 2px solid #9e9e9e;'  # 一般：灰色
                            else:
                                return 'background-color: #ffebee; color: #c62828; font-weight: bold; border-radius: 4px; padding: 4px 8px; border: 2px solid #f44336;'  # 较差：红色
                        except:
                            return ''
                    return ''
                
                def color_volatility_values(val):
                    """为波动率添加颜色"""
                    if isinstance(val, str) and '%' in val:
                        try:
                            vol_value = float(val.rstrip('%'))
                            if vol_value < 15:
                                return 'background-color: #e8f5e8; color: #2e7d32; font-weight: bold; border-radius: 4px; padding: 4px 8px;'  # 低波动：绿色
                            elif vol_value < 25:
                                return 'background-color: #fff3e0; color: #ef6c00; font-weight: bold; border-radius: 4px; padding: 4px 8px;'  # 中波动：橙色
                            else:
                                return 'background-color: #ffebee; color: #c62828; font-weight: bold; border-radius: 4px; padding: 4px 8px;'  # 高波动：红色
                        except:
                            return ''
                    return ''
                
                # 应用样式到不同列
                styled_df = df.style.map(color_return_values, subset=['当前累计涨跌幅', '期间最高涨幅', '期间最大跌幅', '最大回撤'])
                styled_df = styled_df.map(color_sharpe_values, subset=['夏普比率'])
                styled_df = styled_df.map(color_volatility_values, subset=['年化波动率'])
                
                # 为ETF代码和名称添加样式 - 修复apply方法的使用
                def style_etf_columns(row):
                    """为ETF代码和名称列添加样式"""
                    styles = []
                    for col in df.columns:
                        if col == 'ETF代码':
                            styles.append('background-color: #e3f2fd; color: #1565c0; font-weight: bold; border-radius: 4px; padding: 4px 8px;')
                        elif col == 'ETF名称':
                            styles.append('background-color: #f3e5f5; color: #7b1fa2; font-weight: bold; border-radius: 4px; padding: 4px 8px;')
                        else:
                            styles.append('')
                    return styles
                
                styled_df = styled_df.apply(style_etf_columns, axis=1)
                
                return styled_df
            
            # 应用美化样式
            styled_comparison_df = style_performance_table(comparison_df)
            
            # 显示美化后的表格
            st.dataframe(styled_comparison_df, use_container_width=True)
            
            # 添加表格说明
            st.markdown("""
            <div style='background-color: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #007bff; margin-top: 15px;'>
                <strong>📊 近一年表现对比表格说明：</strong><br>
                <strong>涨跌幅颜色含义：</strong><br>
                • <span style='color: #c62828;'>🔴 深红色</span>：超强表现（>10%）<br>
                • <span style='color: #b71c1c;'>🔴 红色</span>：强表现（5-10%）<br>
                • <span style='color: #ef6c00;'>🟠 橙色</span>：正表现（0-5%）<br>
                • <span style='color: #424242;'>⚪ 灰色</span>：轻微负表现（-5% 到 0%）<br>
                • <span style='color: #2e7d32;'>🟢 绿色</span>：负表现（-10% 到 -5%）<br>
                • <span style='color: #1b5e20;'>🟢 深绿色</span>：强负表现（<-10%）<br>
                <br>
                <strong>夏普比率颜色含义：</strong><br>
                • <span style='color: #2e7d32;'>🟢 绿色</span>：优秀（>1.5）<br>
                • <span style='color: #ef6c00;'>🟠 橙色</span>：良好（0.5-1.5）<br>
                • <span style='color: #424242;'>⚪ 灰色</span>：一般（0-0.5）<br>
                • <span style='color: #c62828;'>🔴 红色</span>：较差（<0）<br>
                <br>
                <strong>波动率颜色含义：</strong><br>
                • <span style='color: #2e7d32;'>🟢 绿色</span>：低波动（<15%）<br>
                • <span style='color: #ef6c00;'>🟠 橙色</span>：中波动（15-25%）<br>
                • <span style='color: #c62828;'>🔴 红色</span>：高波动（>25%）
            </div>
            """, unsafe_allow_html=True)
            
            # 显示统计摘要
            st.subheader("📈 表现统计摘要")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                positive_count = sum(1 for data in comparison_data if float(data['当前累计涨跌幅'].rstrip('%')) > 0)
                st.metric("上涨标的", f"{positive_count}只", delta=f"{positive_count}/{len(comparison_data)}")
            
            with col2:
                negative_count = sum(1 for data in comparison_data if float(data['当前累计涨跌幅'].rstrip('%')) < 0)
                st.metric("下跌标的", f"{negative_count}只", delta=f"{negative_count}/{len(comparison_data)}")
            
            with col3:
                best_performer = max(comparison_data, key=lambda x: float(x['当前累计涨跌幅'].rstrip('%')))
                st.metric("表现最佳", f"{best_performer['ETF代码']}", delta=best_performer['当前累计涨跌幅'])
            
            with col4:
                worst_performer = min(comparison_data, key=lambda x: float(x['当前累计涨跌幅'].rstrip('%')))
                st.metric("表现最差", f"{worst_performer['ETF代码']}", delta=worst_performer['当前累计涨跌幅'])
        else:
            st.warning("无法计算任何ETF的指标")
        
    except Exception as e:
        st.error(f"绘制趋势图失败: {e}")
        small_log(f"绘制趋势图失败: {e}")
        import traceback
        st.markdown(f"<div style='font-size:12px; color:#888;'>错误详情: {traceback.format_exc()}</div>", unsafe_allow_html=True)

def render_all_etfs_trend_charts(etf_list, etf_names):
    """
    为所有ETF渲染趋势图（现在直接调用render_etf_trend_chart）
    
    Args:
        etf_list: ETF代码列表
        etf_names: ETF名称字典
    """
    render_etf_trend_chart(etf_list, etf_names)
