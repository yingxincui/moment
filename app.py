#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETF动量策略分析系统 - 主应用
"""

import streamlit as st
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(__file__))

# 设置页面配置
st.set_page_config(
    page_title="ETF动量策略分析系统",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 暗号验证
SECRET_CODE = "xldl"

# 检查是否已经通过暗号验证
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# 添加时间戳验证，防止会话劫持
if 'auth_timestamp' not in st.session_state:
    st.session_state.auth_timestamp = None

# 如果未通过验证，显示暗号输入界面
if not st.session_state.authenticated:
    st.title("🔐 ETF动量策略分析系统")
    st.markdown("---")
    
    # 暗号输入界面
    st.markdown("""
    <div style='text-align: center; padding: 40px;'>
        <h2>🚀 欢迎使用ETF动量策略分析系统</h2>
        <p style='font-size: 18px; color: #666; margin: 20px 0;'>
            请输入暗号以访问系统功能
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # 暗号输入框
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        secret_input = st.text_input(
            "🔑 请输入暗号：",
            type="password",
            placeholder="请输入暗号...",
            help="请输入正确的暗号才能访问系统"
        )
        
        # 验证按钮
        if st.button("🔓 验证暗号", type="primary", use_container_width=True):
            if secret_input == SECRET_CODE:
                st.session_state.authenticated = True
                st.session_state.auth_timestamp = st.session_state.get('_session_id', 'unknown')
                st.success("✅ 暗号验证成功！正在进入系统...")
                st.rerun()
            else:
                st.error("❌ 暗号错误，请重新输入！")
                st.session_state.authenticated = False
                st.session_state.auth_timestamp = None
        
        # 提示信息
        st.info("💡 提示：请输入暗号验证身份")
    
    # 页脚
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #888; font-size: 12px;'>
        ETF动量策略分析系统 | 基于Streamlit构建 | 仅供学习研究使用
    </div>
    """, unsafe_allow_html=True)
    
    # 阻止继续执行
    st.stop()

# 验证通过后的额外安全检查
if st.session_state.authenticated:
    # 检查会话ID是否匹配（防止会话劫持）
    current_session_id = st.session_state.get('_session_id', 'unknown')
    if st.session_state.auth_timestamp != current_session_id:
        st.error("🔐 会话验证失败！请重新登录。")
        st.session_state.authenticated = False
        st.session_state.auth_timestamp = None
        st.rerun()
    
    # 可以在这里添加其他安全检查，比如IP验证、时间限制等

# 暗号验证通过后的逻辑
# 检查是否已经重定向
if 'redirected_to_default' not in st.session_state:
    st.session_state.redirected_to_default = False

# 自动重定向到默认组合页面
if not st.session_state.redirected_to_default:
    st.session_state.redirected_to_default = True
    
    # 显示重定向信息
    st.info("🔄 正在跳转到默认组合页面...")
    
    # 使用Streamlit的重定向方法
    try:
        st.switch_page("pages/1_📊_默认组合.py")
    except Exception as e:
        st.error(f"重定向失败: {e}")
        st.info("请手动点击左侧菜单的'📊 默认组合'页面")
    
    st.stop()

# 如果重定向失败，显示主页面内容
st.title("📈 ETF动量策略分析系统")

# 添加登出按钮
col1, col2, col3 = st.columns([3, 1, 1])
with col3:
    if st.button("🚪 登出", type="secondary"):
        # 清除认证状态
        if 'authenticated' in st.session_state:
            del st.session_state.authenticated
        if 'auth_timestamp' in st.session_state:
            del st.session_state.auth_timestamp
        if 'redirected_to_default' in st.session_state:
            del st.session_state.redirected_to_default
        st.success("✅ 已安全登出！")
        st.rerun()

st.markdown("---")

# 显示欢迎信息
st.markdown("""
## 🎯 系统介绍

这是一个基于动量策略的ETF投资分析系统，支持多种ETF组合配置：

- **📊 默认组合**: 包含A股、美股、黄金、债券等主要资产类别
- **🚀 科创创业**: 用科创创业ETF替代创业板，更聚焦科技创新企业  
- **🌍 全球股市轮动**: 覆盖中美欧日等主要市场，支持全球资产配置
- **👑 明总定制组合**: 在默认组合基础上增加科创创业ETF和科创50ETF

## 🚀 快速开始

请从左侧边栏选择您想要分析的ETF组合页面，然后：

1. 选择您感兴趣的ETF
2. 调整策略参数（动量周期、均线周期等）
3. 查看分析结果和持仓建议

## 📊 策略说明

本系统采用**动量策略**，通过以下步骤进行投资决策：

1. **动量计算**: 计算各ETF的相对动量排名
2. **趋势过滤**: 使用移动平均线过滤下跌趋势
3. **持仓选择**: 选择动量最强且趋势向上的ETF
4. **动态调整**: 定期重新计算并调整持仓

## ⚠️ 风险提示

- 本系统仅供学习和研究使用，不构成投资建议
- 投资有风险，入市需谨慎
- 历史表现不代表未来收益
""")

# 显示系统状态
st.markdown("---")
st.markdown("### 🔧 系统状态")

# 检查核心模块
try:
    from core_strategy import select_etfs
    st.success("✅ 核心策略模块加载成功")
except ImportError as e:
    st.error(f"❌ 核心策略模块加载失败: {e}")

# 检查ETF池配置
try:
    from etf_pools import ETF_POOLS_CONFIG
    st.success(f"✅ ETF池配置加载成功 (共{len(ETF_POOLS_CONFIG)}个组合)")
except ImportError as e:
    st.error(f"❌ ETF池配置加载失败: {e}")

# 检查数据缓存
try:
    import os
    cache_dir = "etf_cache"
    if os.path.exists(cache_dir):
        cache_files = [f for f in os.listdir(cache_dir) if f.endswith('.csv')]
        st.success(f"✅ 数据缓存可用 (共{len(cache_files)}个ETF数据文件)")
    else:
        st.warning("⚠️ 数据缓存目录不存在")
except Exception as e:
    st.error(f"❌ 数据缓存检查失败: {e}")

# 页脚
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #888; font-size: 12px;'>
    ETF动量策略分析系统 | 基于Streamlit构建 | 仅供学习研究使用
</div>
""", unsafe_allow_html=True)
