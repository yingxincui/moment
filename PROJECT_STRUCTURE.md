# 项目结构说明

```
etf-momentum-strategy/
├── app.py                          # 主应用入口和暗号验证
├── core_strategy.py                # 核心策略逻辑和渲染函数
├── email_subscription.py           # 邮件订阅功能模块
├── email_config.py                 # 邮件配置管理
├── etf_pools.py                    # ETF池配置
├── requirements.txt                # 项目依赖
├── README.md                       # 项目说明文档
├── LICENSE                         # MIT许可证
├── .gitignore                      # Git忽略文件
├── PROJECT_STRUCTURE.md            # 项目结构说明（本文件）
├── pages/                          # Streamlit页面目录
│   ├── 1_📊_默认组合.py           # 默认ETF组合分析页面
│   ├── 2_🚀_科创创业.py           # 科创创业ETF分析页面
│   ├── 3_🌍_全球股市轮动.py       # 全球股市轮动策略页面
│   ├── 4_👑_明总定制组合.py       # 明总定制组合分析页面
│   └── 5_📧_邮件订阅.py           # 邮件订阅管理页面
├── etf_cache/                      # ETF数据缓存目录
│   └── *.csv                       # 缓存的ETF历史数据文件
├── email_config.json               # 邮件配置信息（运行时生成）
└── email_subscriptions.json        # 邮件订阅信息（运行时生成）
```

## 核心文件说明

### 主要应用文件
- **`app.py`**: 系统入口点，包含暗号验证和页面重定向逻辑
- **`core_strategy.py`**: 核心策略实现，包含动量计算、Bias分析、趋势图表等所有核心功能
- **`etf_pools.py`**: 定义各种ETF组合配置

### 邮件订阅模块
- **`email_subscription.py`**: 邮件订阅的核心功能实现
- **`email_config.py`**: 邮件配置管理类
- **`email_config.json`**: 存储邮件服务器配置（自动生成）
- **`email_subscriptions.json`**: 存储订阅者信息（自动生成）

### 页面文件
- **`pages/1_📊_默认组合.py`**: 基础ETF组合分析
- **`pages/2_🚀_科创创业.py`**: 科创相关ETF分析
- **`pages/3_🌍_全球股市轮动.py`**: 全球ETF轮动策略
- **`pages/4_👑_明总定制组合.py`**: 定制ETF组合分析
- **`pages/5_📧_邮件订阅.py`**: 邮件订阅管理界面

### 配置文件
- **`requirements.txt`**: Python依赖包列表
- **`.gitignore`**: Git版本控制忽略文件配置
- **`LICENSE`**: MIT开源许可证

## 数据流向

1. **数据获取**: `core_strategy.py` 通过akshare获取ETF历史数据
2. **策略计算**: 计算动量、均线、偏离度等指标
3. **结果渲染**: 生成表格、图表和分析报告
4. **邮件发送**: `email_subscription.py` 自动生成并发送HTML邮件

## 缓存机制

- **`etf_cache/`**: 本地缓存ETF历史数据，避免重复API调用
- **配置文件**: 邮件配置和订阅信息本地存储，保护用户隐私

## 安全特性

- **暗号验证**: 在`app.py`中实现，保护系统访问
- **会话管理**: 使用Streamlit的session_state管理用户状态
- **数据隔离**: 不同用户的数据相互隔离

## 部署说明

项目可以直接在本地运行，也可以部署到Streamlit Cloud等云平台。所有依赖都在`requirements.txt`中列出，确保环境一致性。
