#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证工具模块
提供统一的暗号验证和安全检查功能
"""

import streamlit as st
import time

def check_authentication():
    """
    检查用户是否已通过暗号验证
    
    Returns:
        bool: 如果验证通过返回True，否则返回False
    """
    # 检查基本认证状态
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        return False
    
    # 检查会话时间戳
    if 'auth_timestamp' not in st.session_state:
        return False
    
    # 检查会话ID匹配（防止会话劫持）
    current_session_id = st.session_state.get('_session_id', 'unknown')
    if st.session_state.auth_timestamp != current_session_id:
        return False
    
    # 可以在这里添加更多安全检查
    # 比如检查认证时间是否过期等
    
    return True

def require_authentication():
    """
    要求用户必须通过认证才能访问页面
    
    如果用户未通过认证，会显示错误信息并停止页面执行
    """
    if not check_authentication():
        st.error("🔐 访问被拒绝！请先通过暗号验证。")
        st.info("请返回主页面输入正确的暗号。")
        st.stop()

def get_auth_status():
    """
    获取当前认证状态信息
    
    Returns:
        dict: 包含认证状态信息的字典
    """
    return {
        'authenticated': st.session_state.get('authenticated', False),
        'auth_timestamp': st.session_state.get('auth_timestamp', None),
        'session_id': st.session_state.get('_session_id', 'unknown')
    }

def clear_auth_session():
    """
    清除认证会话信息
    """
    if 'authenticated' in st.session_state:
        del st.session_state.authenticated
    if 'auth_timestamp' in st.session_state:
        del st.session_state.auth_timestamp
