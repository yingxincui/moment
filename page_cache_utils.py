#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
页面计算结果缓存工具模块
支持按页面和参数缓存计算结果，默认缓存一天
"""

import streamlit as st
import json
import os
import hashlib
from datetime import datetime, timedelta
import pandas as pd

# 缓存配置
CACHE_DIR = "page_cache"
CACHE_DURATION_HOURS = 24  # 缓存24小时
CACHE_META_FILE = "cache_meta.json"

def convert_to_json_serializable(data):
    """
    将数据转换为JSON可序列化格式
    
    Args:
        data: 要转换的数据
    
    Returns:
        json_data: JSON可序列化的数据
    """
    if isinstance(data, (list, tuple)):
        return [convert_to_json_serializable(item) for item in data]
    elif isinstance(data, dict):
        return {key: convert_to_json_serializable(value) for key, value in data.items()}
    elif hasattr(data, 'to_dict'):  # pandas DataFrame
        return data.to_dict('records')
    elif hasattr(data, 'tolist'):  # numpy array
        return data.tolist()
    elif hasattr(data, 'item'):  # numpy scalar
        return data.item()
    elif isinstance(data, (int, float, str, bool, type(None))):
        return data
    else:
        # 对于其他类型，尝试转换为字符串
        return str(data)

def ensure_cache_dir():
    """确保缓存目录存在"""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

def get_cache_key(page_name, params):
    """
    生成缓存键
    
    Args:
        page_name: 页面名称
        params: 参数字典
    
    Returns:
        cache_key: 缓存键
    """
    # 将参数转换为字符串并排序，确保相同参数生成相同键
    params_str = json.dumps(params, sort_keys=True, ensure_ascii=False)
    # 使用页面名称和参数生成哈希键
    cache_key = f"{page_name}_{hashlib.md5(params_str.encode('utf-8')).hexdigest()}"
    return cache_key

def get_cache_file_path(cache_key):
    """获取缓存文件路径"""
    ensure_cache_dir()
    return os.path.join(CACHE_DIR, f"{cache_key}.json")

def get_cache_meta_file_path():
    """获取缓存元数据文件路径"""
    ensure_cache_dir()
    return os.path.join(CACHE_DIR, CACHE_META_FILE)

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
        print(f"保存缓存元数据失败: {e}")

def is_cache_valid(cache_key):
    """
    检查缓存是否有效
    
    Args:
        cache_key: 缓存键
    
    Returns:
        bool: 缓存是否有效
    """
    meta_data = load_cache_meta()
    
    if cache_key not in meta_data:
        return False
    
    cache_info = meta_data[cache_key]
    cache_time = datetime.fromisoformat(cache_info['created_at'])
    current_time = datetime.now()
    
    # 检查是否超过缓存时间
    if current_time - cache_time > timedelta(hours=CACHE_DURATION_HOURS):
        return False
    
    # 检查是否跨过了0:00（强制刷新）
    cache_date = cache_time.date()
    current_date = current_time.date()
    if cache_date != current_date:
        return False
    
    # 检查缓存文件是否存在
    cache_file = get_cache_file_path(cache_key)
    if not os.path.exists(cache_file):
        return False
    
    return True

def save_to_cache(cache_key, data, page_name, params):
    """
    保存数据到缓存
    
    Args:
        cache_key: 缓存键
        data: 要缓存的数据
        page_name: 页面名称
        params: 参数字典
    """
    try:
        # 转换数据为JSON可序列化格式
        json_data = convert_to_json_serializable(data)
        
        # 保存数据到文件
        cache_file = get_cache_file_path(cache_key)
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        # 更新元数据
        meta_data = load_cache_meta()
        meta_data[cache_key] = {
            'page_name': page_name,
            'params': params,
            'created_at': datetime.now().isoformat(),
            'data_type': type(data).__name__,
            'file_size': os.path.getsize(cache_file)
        }
        save_cache_meta(meta_data)
        
        print(f"缓存已保存: {page_name} - {cache_key}")
        
    except Exception as e:
        print(f"保存缓存失败: {e}")

def load_from_cache(cache_key):
    """
    从缓存加载数据
    
    Args:
        cache_key: 缓存键
    
    Returns:
        data: 缓存的数据，如果不存在或无效则返回None
    """
    try:
        cache_file = get_cache_file_path(cache_key)
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"从缓存加载: {cache_key}")
            return data
    except Exception as e:
        print(f"加载缓存失败: {e}")
    return None

def get_cached_result(page_name, params, compute_func, *args, **kwargs):
    """
    获取缓存结果，如果缓存无效则重新计算
    
    Args:
        page_name: 页面名称
        params: 参数字典
        compute_func: 计算函数
        *args: 计算函数的参数
        **kwargs: 计算函数的关键字参数
    
    Returns:
        result: 计算结果
    """
    cache_key = get_cache_key(page_name, params)
    
    # 检查缓存是否有效
    if is_cache_valid(cache_key):
        cached_data = load_from_cache(cache_key)
        if cached_data is not None:
            return cached_data
    
    # 缓存无效或不存在，重新计算
    print(f"缓存无效，重新计算: {page_name}")
    result = compute_func(*args, **kwargs)
    
    # 保存到缓存
    if result is not None:
        save_to_cache(cache_key, result, page_name, params)
    
    return result

def clear_page_cache(page_name=None):
    """
    清除页面缓存
    
    Args:
        page_name: 页面名称，如果为None则清除所有缓存
    """
    meta_data = load_cache_meta()
    
    if page_name is None:
        # 清除所有缓存
        for cache_key in list(meta_data.keys()):
            cache_file = get_cache_file_path(cache_key)
            if os.path.exists(cache_file):
                os.remove(cache_file)
        meta_data = {}
    else:
        # 清除指定页面的缓存
        to_remove = []
        for cache_key, cache_info in meta_data.items():
            if cache_info.get('page_name') == page_name:
                cache_file = get_cache_file_path(cache_key)
                if os.path.exists(cache_file):
                    os.remove(cache_file)
                to_remove.append(cache_key)
        
        for cache_key in to_remove:
            del meta_data[cache_key]
    
    save_cache_meta(meta_data)
    print(f"缓存已清除: {page_name if page_name else '所有页面'}")

def get_cache_info():
    """
    获取缓存信息
    
    Returns:
        dict: 缓存信息
    """
    meta_data = load_cache_meta()
    
    cache_info = {
        'total_caches': len(meta_data),
        'pages': {},
        'total_size': 0,
        'oldest_cache': None,
        'newest_cache': None
    }
    
    for cache_key, cache_data in meta_data.items():
        page_name = cache_data.get('page_name', 'unknown')
        created_at = datetime.fromisoformat(cache_data.get('created_at', datetime.now().isoformat()))
        file_size = cache_data.get('file_size', 0)
        
        if page_name not in cache_info['pages']:
            cache_info['pages'][page_name] = {
                'count': 0,
                'size': 0,
                'oldest': created_at,
                'newest': created_at
            }
        
        cache_info['pages'][page_name]['count'] += 1
        cache_info['pages'][page_name]['size'] += file_size
        cache_info['pages'][page_name]['oldest'] = min(cache_info['pages'][page_name]['oldest'], created_at)
        cache_info['pages'][page_name]['newest'] = max(cache_info['pages'][page_name]['newest'], created_at)
        
        cache_info['total_size'] += file_size
        
        if cache_info['oldest_cache'] is None or created_at < cache_info['oldest_cache']:
            cache_info['oldest_cache'] = created_at
        
        if cache_info['newest_cache'] is None or created_at > cache_info['newest_cache']:
            cache_info['newest_cache'] = created_at
    
    return cache_info

def format_file_size(size_bytes):
    """格式化文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"

def render_cache_management_ui():
    """渲染缓存管理界面"""
    st.subheader("📊 缓存管理")
    
    cache_info = get_cache_info()
    
    # 缓存统计已移除，不显示给用户
    
    # 全局操作
    st.subheader("🔧 全局操作")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ 清除所有缓存", type="secondary"):
            clear_page_cache()
            st.success("已清除所有缓存")
            st.rerun()
    
    with col2:
        if st.button("🔄 刷新缓存信息", type="secondary"):
            st.rerun()
    
    # 缓存说明
    st.info("""
    **缓存说明：**
    - 所有页面计算结果默认缓存24小时
    - 每天0:00后强制刷新所有缓存
    - 参数变化时会自动重新计算
    - 缓存过期后会在下次访问时自动刷新
    - 使用JSON格式存储，便于查看和调试
    - 可以手动清除特定页面或所有缓存
    """)

def get_page_cache_key(page_name, **params):
    """
    获取页面缓存键的便捷函数
    
    Args:
        page_name: 页面名称
        **params: 页面参数
    
    Returns:
        cache_key: 缓存键
    """
    return get_cache_key(page_name, params)

def cache_page_result(page_name, result, **params):
    """
    缓存页面结果的便捷函数
    
    Args:
        page_name: 页面名称
        result: 计算结果
        **params: 页面参数
    """
    cache_key = get_cache_key(page_name, params)
    save_to_cache(cache_key, result, page_name, params)

def get_cached_page_result(page_name, **params):
    """
    获取页面缓存结果的便捷函数
    
    Args:
        page_name: 页面名称
        **params: 页面参数
    
    Returns:
        result: 缓存的结果，如果不存在或无效则返回None
    """
    cache_key = get_cache_key(page_name, params)
    
    if is_cache_valid(cache_key):
        return load_from_cache(cache_key)
    
    return None
