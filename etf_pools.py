#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETF池配置模块
定义不同的ETF组合
"""

# 默认ETF池
DEFAULT_ETF_POOL = {
    '510300': '300ETF',
    '159915': '创业板',
    '513050': '中概互联网ETF',
    '159941': '纳指ETF',
    '518880': '黄金ETF',
    '511090':'30年国债'
}

# 科创创业组合（替换创业板为科创创业ETF）
SCI_TECH_POOL = {
    '510300': '300ETF',
    '159781': '科创创业ETF',
    '513050': '中概互联网ETF',
    '159941': '纳指ETF',
    '518880': '黄金ETF',
    '511090':'30年国债'
}

# 明总定制组合（默认组合 + 科创创业ETF + 科创50ETF）
MINGZONG_CUSTOM_POOL = {
    '510300': '300ETF',
    '159915': '创业板',
    '513050': '中概互联网ETF',
    '159941': '纳指ETF',
    '518880': '黄金ETF',
    '511090': '30年国债',
    '159781': '科创创业ETF',
    '588000': '科创50ETF'
}

# 全球股市轮动组合
GLOBAL_ROTATION_POOL = {
    '510300': '300ETF',
    '513050': '中概互联网ETF',
    '159941': '纳指ETF',
    '513520': '日经ETF',
    '513030': '德国ETF',
    '513730': '东南亚科技ETF',
    '159329': '沙特ETF'
}

# 期权标的组合
OPTION_UNDERLYING_POOL = {
    '588000': '科创50ETF',
    '510500': '中证500ETF',
    '510050': '上证50ETF',
    '159915': '创业板ETF',
    '510300': '沪深300ETF',
    '159901': '深证100ETF'
}

# 所有ETF池的配置信息
ETF_POOLS_CONFIG = {
    'default': {
        'name': '默认组合',
        'description': '包含A股、美股、黄金、债券等主要资产类别',
        'pool': DEFAULT_ETF_POOL,
        'icon': '📊'
    },
    'scitech': {
        'name': '科创创业',
        'description': '用科创创业ETF替代创业板，更聚焦科技创新企业',
        'pool': SCI_TECH_POOL,
        'icon': '🚀'
    },
    'mingzong': {
        'name': '明总定制组合',
        'description': '在默认组合基础上增加科创创业ETF和科创50ETF，更全面的科技创新配置',
        'pool': MINGZONG_CUSTOM_POOL,
        'icon': '👑'
    },
    'global': {
        'name': '全球股市轮动',
        'description': '覆盖中美欧日等主要市场，支持全球资产配置',
        'pool': GLOBAL_ROTATION_POOL,
        'icon': '🌍'
    },
    'option': {
        'name': '期权标的组合',
        'description': '包含科创50、中证500、上证50、创业板、沪深300、深证100等主要期权标的ETF',
        'pool': OPTION_UNDERLYING_POOL,
        'icon': '📈'
    }
}
