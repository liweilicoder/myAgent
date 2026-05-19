"""
人民币汇率实时显示应用
====================
基于 Streamlit + Frankfurter API

功能特性:
- 支持 USD, EUR, JPY, GBP, HKD, KRW 等主要货币
- 实时汇率显示与24小时涨跌分析
- 交互式趋势图表
- 智能缓存与自动刷新
"""

import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple, Any
import time
import json
import hashlib
import html

# ==================== 配置常量 ====================
API_BASE_URL = "https://api.frankfurter.app"
SUPPORTED_CURRENCIES = {
    "USD": {"name": "美元", "symbol": "$", "flag": "🇺🇸", "decimals": 4},
    "EUR": {"name": "欧元", "symbol": "€", "flag": "🇪🇺", "decimals": 4},
    "JPY": {"name": "日元", "symbol": "¥", "flag": "🇯🇵", "decimals": 4},
    "GBP": {"name": "英镑", "symbol": "£", "flag": "🇬🇧", "decimals": 4},
    "HKD": {"name": "港币", "symbol": "HK$", "flag": "🇭🇰", "decimals": 4},
    "KRW": {"name": "韩元", "symbol": "₩", "flag": "🇰🇷", "decimals": 2},
    "CNY": {"name": "人民币", "symbol": "¥", "flag": "🇨🇳", "decimals": 4},
    "AUD": {"name": "澳元", "symbol": "A$", "flag": "🇦🇺", "decimals": 4},
    "CAD": {"name": "加元", "symbol": "C$", "flag": "🇨🇦", "decimals": 4},
    "CHF": {"name": "瑞士法郎", "symbol": "Fr", "flag": "🇨🇭", "decimals": 4},
}

REFRESH_OPTIONS = {"30秒": 30, "1分钟": 60, "5分钟": 300, "手动": 0}
REQUEST_TIMEOUT = 15
CACHE_TTL = 300  # 5分钟缓存

# ==================== 工具函数 ====================

def generate_cache_key(*args) -> str:
    """生成缓存键"""
    key_str = "_".join(str(arg) for arg in args)
    return hashlib.md5(key_str.encode()).hexdigest()


def format_rate(rate: float, currency: str) -> str:
    """格式化汇率显示"""
    decimals = SUPPORTED_CURRENCIES.get(currency, {}).get("decimals", 4)
    return f"{rate:.{decimals}f}"


def format_change(value: float, decimals: int = 4) -> str:
    """格式化涨跌值"""
    prefix = "+" if value >= 0 else ""
    return f"{prefix}{value:.{decimals}f}"


def calculate_color(change: float) -> Tuple[str, str]:
    """根据涨跌返回颜色和箭头"""
    if change > 0:
        return "#22c55e", "↑", "上涨"
    elif change < 0:
        return "#ef4444", "↓", "下跌"
    return "#6b7280", "→", "持平"


def sanitize_html(text: str) -> str:
    """HTML 转义，防止 XSS 攻击"""
    return html.escape(str(text))


def validate_api_response(data: Dict, required_keys: List[str]) -> Tuple[bool, str]:
    """验证 API 响应数据结构"""
    if not isinstance(data, dict):
        return False, "响应数据格式错误：期望字典类型"
    
    for key in required_keys:
        if key not in data:
            return False, f"响应缺少必要字段: {key}"
    
    return True, ""


# ==================== API 交互 ====================

@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def fetch_current_rates() -> Tuple[Optional[Dict], Optional[str]]:
    """获取当前汇率"""
    try:
        url = f"{API_BASE_URL}/latest"
        params = {"from": "CNY", "to": ",".join(SUPPORTED_CURRENCIES.keys())}
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        
        # 验证响应数据结构
        is_valid, error_msg = validate_api_response(data, ["rates", "base", "date"])
        if not is_valid:
            return None, f"数据格式异常: {error_msg}"
        
        # 验证汇率数据
        if not isinstance(data.get("rates"), dict):
            return None, "汇率数据格式错误"
        
        return data, None
        
    except requests.exceptions.Timeout:
        return None, "⏱️ 请求超时，请检查网络连接后重试"
    except requests.exceptions.ConnectionError:
        return None, "🌐 网络连接失败，请检查网络设置"
    except requests.exceptions.HTTPError as e:
        return None, f"HTTP错误: {e.response.status_code}"
    except requests.exceptions.RequestException as e:
        return None, f"❌ 请求失败: {str(e)}"
    except (json.JSONDecodeError, KeyError) as e:
        return None, f"📦 数据格式错误: {str(e)}"


@st.cache_data(ttl=CACHE_TTL * 2, show_spinner=False)
def fetch_historical_rates(days: int = 7) -> Tuple[Optional[Dict], Optional[str]]:
    """获取历史汇率数据"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        url = f"{API_BASE_URL}/{start_date.strftime('%Y-%m-%d')}..{end_date.strftime('%Y-%m-%d')}"
        params = {
            "from": "CNY",
            "to": ",".join(SUPPORTED_CURRENCIES.keys())
        }
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        
        # 验证响应数据结构
        is_valid, error_msg = validate_api_response(data, ["rates"])
        if not is_valid:
            return None, f"历史数据格式异常: {error_msg}"
        
        return data, None
        
    except requests.exceptions.RequestException as e:
        return None, f"获取历史数据失败: {str(e)}"
    except (json.JSONDecodeError, KeyError) as e:
        return None, f"历史数据格式错误: {str(e)}"


def calculate_rate_metrics(
    historical_data: Optional[Dict], 
    current_rate: float, 
    currency: str
) -> Dict[str, float]:
    """计算汇率指标"""
    metrics = {
        "change_percent": 0.0,
        "change_amount": 0.0,
        "high": current_rate,
        "low": current_rate,
        "average": current_rate,
        "volatility": 0.0
    }
    
    if not historical_data or "rates" not in historical_data:
        return metrics
    
    dates = sorted(historical_data["rates"].keys())
    if len(dates) < 2:
        return metrics
    
    # 获取历史数据
    rates_list = []
    for date in dates:
        rate = historical_data["rates"][date].get(currency)
        if rate:
            rates_list.append(1.0 / rate)  # 转换为 CNY 基准
    
    if not rates_list:
        return metrics
    
    first_rate = rates_list[0]
    metrics["change_amount"] = current_rate - first_rate
    metrics["change_percent"] = (metrics["change_amount"] / first_rate * 100) if first_rate else 0
    metrics["high"] = max(rates_list)
    metrics["low"] = min(rates_list)
    metrics["average"] = sum(rates_list) / len(rates_list)
    metrics["volatility"] = metrics["high"] - metrics["low"]
    
    return metrics


def get_price_series(historical_data: Optional[Dict], currency: str) -> List[Dict]:
    """获取价格时间序列"""
    if not historical_data or "rates" not in historical_data:
        return []
    
    series = []
    for date in sorted(historical_data["rates"].keys()):
        rate = historical_data["rates"][date].get(currency)
        if rate:
            series.append({
                "date": date,
                "rate": 1.0 / rate,
                "datetime": datetime.strptime(date, "%Y-%m-%d")
            })
    return series


# ==================== UI 组件 ====================

def render_header():
    """渲染页面头部"""
    st.markdown("""
    <div class="header-container">
        <div class="header-content">
            <h1>💱 人民币汇率实时看板</h1>
            <p class="subtitle">实时追踪 · 涨跌分析 · 趋势预测</p>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_last_update():
    """渲染最后更新时间"""
    now = datetime.now()
    st.markdown(f"""
    <div class="update-time">
        <span>🕐 数据更新于 {sanitize_html(now.strftime('%Y-%m-%d %H:%M:%S'))}</span>
        <span class="refresh-hint">自动刷新间隔: 5分钟</span>
    </div>
    """, unsafe_allow_html=True)


def render_currency_card(
    currency: str, 
    rate: float, 
    metrics: Dict[str, float],
    index: int
):
    """渲染货币卡片"""
    config = SUPPORTED_CURRENCIES[currency]
    color, arrow, _ = calculate_color(metrics["change_percent"])
    change_text = format_change(metrics["change_percent"], 4)
    amount_text = format_change(metrics["change_amount"], 6)
    
    # HTML 转义所有用户可见的文本
    safe_symbol = sanitize_html(config['symbol'])
    safe_name = sanitize_html(config['name'])
    safe_currency = sanitize_html(currency)
    safe_rate = format_rate(rate, currency)
    
    st.markdown(f"""
    <div class="currency-card" style="animation-delay: {index * 0.1}s">
        <div class="card-header">
            <div class="currency-info">
                <span class="flag">{config['flag']}</span>
                <span class="currency-name">{safe_name}</span>
                <span class="currency-code">{safe_currency}</span>
            </div>
            <div class="currency-symbol">{safe_symbol}</div>
        </div>
        <div class="card-rate">
            {safe_rate}
        </div>
        <div class="card-change" style="color: {color}">
            <span class="arrow">{arrow}</span>
            <span class="percent">{change_text}%</span>
            <span class="amount">({amount_text})</span>
        </div>
        <div class="card-footer">
            <div class="mini-stat">
                <span class="label">最高</span>
                <span class="value high">{format_rate(metrics['high'], currency)}</span>
            </div>
            <div class="mini-stat">
                <span class="label">最低</span>
                <span class="value low">{format_rate(metrics['low'], currency)}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_trend_chart(
    price_series: List[Dict], 
    currency: str,
    height: int = 280
):
    """渲染趋势图表"""
    if len(price_series) < 2:
        st.info(f"📊 暂无 {SUPPORTED_CURRENCIES[currency]['name']} 的历史数据")
        return
    
    config = SUPPORTED_CURRENCIES[currency]
    dates = [p["date"] for p in price_series]
    rates = [p["rate"] for p in price_series]
    
    # 确定颜色
    first_rate = rates[0]
    last_rate = rates[-1]
    line_color = "#22c55e" if last_rate >= first_rate else "#ef4444"
    
    # 创建图表
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        row_heights=[0.75, 0.25],
        subplot_titles=("", "涨跌幅变化")
    )
    
    # 主趋势线
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=rates,
            mode='lines+markers',
            name=config['name'],
            line=dict(color=line_color, width=2.5),
            marker=dict(size=6, symbol='circle'),
            fill='tonexty' if last_rate >= first_rate else None,
            fillcolor='rgba(34, 197, 94, 0.1)' if last_rate >= first_rate else 'rgba(239, 68, 68, 0.1)',
            hovertemplate=f"<b>{sanitize_html(config['name'])}</b><br>" +
                         "日期: %{x}<br>" +
                         f"汇率: %{{y:.{config['decimals']}f}}<extra></extra>"
        ),
        row=1, col=1
    )
    
    # 计算涨跌幅
    changes = []
    for i, rate in enumerate(rates):
        if i == 0:
            changes.append(0)
        else:
            changes.append((rate - rates[0]) / rates[0] * 100)
    
    # 涨跌幅柱状图
    bar_colors = ['#22c55e' if c >= 0 else '#ef4444' for c in changes]
    fig.add_trace(
        go.Bar(
            x=dates,
            y=changes,
            marker_color=bar_colors,
            opacity=0.7,
            hovertemplate="涨跌幅: %{y:.2f}%<extra></extra>",
            showlegend=False
        ),
        row=2, col=1
    )
    
    # 添加零线
    fig.add_hline(y=0, line_dash="dash", line_color="#6b7280", row=2, col=1)
    
    # 更新布局
    fig.update_layout(
        height=height,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='white',
        margin=dict(l=50, r=20, t=30, b=50),
        hovermode='x unified',
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)',
            showticklabels=True,
            tickangle=-45
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)',
            title=dict(text="汇率", font=dict(size=11))
        ),
        yaxis2=dict(
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)',
            title=dict(text="%", font=dict(size=11))
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_comparison_chart(
    historical_data: Optional[Dict],
    currencies: List[str],
    days: int = 7
):
    """渲染多货币对比图表"""
    if not historical_data or "rates" not in historical_data:
        st.warning("暂无数据可供对比")
        return
    
    fig = go.Figure()
    colors = px.colors.qualitative.Set2[:len(currencies)]
    
    for idx, currency in enumerate(currencies):
        series = get_price_series(historical_data, currency)
        if not series:
            continue
        
        dates = [p["date"] for p in series]
        rates = [p["rate"] for p in series]
        
        # 归一化到第一个点，便于对比
        if rates:
            base = rates[0]
            normalized = [(r / base - 1) * 100 for r in rates]
        else:
            normalized = []
        
        config = SUPPORTED_CURRENCIES[currency]
        fig.add_trace(go.Scatter(
            x=dates,
            y=normalized,
            mode='lines+markers',
            name=f"{config['flag']} {sanitize_html(currency)}",
            line=dict(width=2),
            marker=dict(size=5),
            hovertemplate=f"<b>{sanitize_html(config['name'])}</b><br>" +
                         "日期: %{x}<br>" +
                         "变化: %{y:.2f}%<extra></extra>"
        ))
    
    fig.update_layout(
        title=dict(text="📊 多货币24小时涨跌幅对比 (%)", font=dict(size=14)),
        height=350,
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=50, r=30, t=50, b=50),
        hovermode='x unified',
        yaxis=dict(
            title="涨跌幅 (%)",
            gridcolor='rgba(0,0,0,0.05)',
            zeroline=True,
            zerolinecolor='rgba(0,0,0,0.1)'
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)',
            tickangle=-45
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_statistics_table(currencies: List[str], rates: Dict, historical_data: Optional[Dict]):
    """渲染统计表格"""
    rows = []
    for currency in currencies:
        if currency not in rates:
            continue
        rate = rates[currency]
        metrics = calculate_rate_metrics(historical_data, rate, currency)
        config = SUPPORTED_CURRENCIES[currency]
        
        change_color, arrow, _ = calculate_color(metrics["change_percent"])
        
        rows.append({
            "货币": f"{config['flag']} {sanitize_html(config['name'])} ({sanitize_html(currency)})",
            "当前汇率": format_rate(rate, currency),
            "涨跌幅": f"<span style='color:{change_color}'>{arrow} {format_change(metrics['change_percent'], 2)}%</span>",
            "涨跌额": f"<span style='color:{change_color}'>{format_change(metrics['change_amount'], 6)}</span>",
            "最高": format_rate(metrics["high"], currency),
            "最低": format_rate(metrics["low"], currency),
            "波动幅度": format_rate(metrics["volatility"], currency)
        })
    
    if rows:
        df = pd.DataFrame(rows)
        st.markdown("""
        <style>
        .dataframe-container {
            background: white;
            border-radius: 12px;
            padding: 15px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown("### 📋 汇率详情汇总")
        st.markdown(
            df.to_html(escape=False, index=False),
            unsafe_allow_html=True
        )


def render_error_card(message: str):
    """渲染错误卡片"""
    safe_message = sanitize_html(message)
    st.markdown(f"""
    <div class="error-card">
        <div class="error-icon">⚠️</div>
        <div class="error-message">{safe_message}</div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔄 重新加载", use_container_width=True, type="primary"):
            st.cache_data.clear()
            st.rerun()


def render_empty_state():
    """渲染空状态"""
    st.markdown("""
    <div class="empty-state">
        <div class="empty-icon">📭</div>
        <div class="empty-message">暂无数据</div>
        <div class="empty-hint">请检查网络连接后重试</div>
    </div>
    """, unsafe_allow_html=True)


# ==================== 样式 ====================

def get_custom_css() -> str:
    """获取自定义CSS样式"""
    return """
    <style>
    /* 全局样式 */
    .stApp {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        min-height: 100vh;
    }
    
    /* 头部样式 */
    .header-container {
        text-align: center;
        padding: 25px 20px;
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
        border-radius: 16px;
        margin-bottom: 25px;
        box-shadow: 0 4px 20px rgba(30, 58, 95, 0.3);
    }
    
    .header-content h1 {
        color: white;
        font-size: 2rem;
        margin: 0;
        font-weight: 700;
    }
    
    .subtitle {
        color: rgba(255,255,255,0.8);
        font-size: 0.95rem;
        margin: 8px 0 0 0;
    }
    
    /* 更新时间 */
    .update-time {
        text-align: center;
        margin-bottom: 20px;
        color: #64748b;
        font-size: 0.85rem;
    }
    
    .refresh-hint {
        margin-left: 15px;
        padding-left: 15px;
        border-left: 1px solid #cbd5e1;
    }
    
    /* 货币卡片 */
    .currency-card {
        background: white;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        transition: transform 0.2s, box-shadow 0.2s;
        animation: fadeInUp 0.5s ease-out;
    }
    
    .currency-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.12);
    }
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }
    
    .currency-info {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .flag {
        font-size: 1.5rem;
    }
    
    .currency-name {
        font-size: 1rem;
        font-weight: 600;
        color: #1e293b;
    }
    
    .currency-code {
        font-size: 0.75rem;
        color: #94a3b8;
        background: #f1f5f9;
        padding: 2px 8px;
        border-radius: 4px;
    }
    
    .currency-symbol {
        font-size: 1.2rem;
        color: #64748b;
    }
    
    .card-rate {
        font-size: 2rem;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 8px;
    }
    
    .card-change {
        font-size: 0.95rem;
        font-weight: 600;
        margin-bottom: 15px;
    }
    
    .card-change .arrow {
        margin-right: 4px;
    }
    
    .card-change .amount {
        color: #94a3b8;
        font-weight: 400;
        font-size: 0.85rem;
    }
    
    .card-footer {
        display: flex;
        justify-content: space-between;
        padding-top: 12px;
        border-top: 1px solid #f1f5f9;
    }
    
    .mini-stat {
        text-align: center;
    }
    
    .mini-stat .label {
        display: block;
        font-size: 0.75rem;
        color: #94a3b8;
        margin-bottom: 4px;
    }
    
    .mini-stat .value {
        font-size: 0.9rem;
        font-weight: 600;
    }
    
    .mini-stat .high {
        color: #22c55e;
    }
    
    .mini-stat .low {
        color: #ef4444;
    }
    
    /* 错误卡片 */
    .error-card {
        background: #fef2f2;
        border: 1px solid #fecaca;
        border-radius: 12px;
        padding: 30px;
        text-align: center;
        margin: 20px 0;
    }
    
    .error-icon {
        font-size: 3rem;
        margin-bottom: 15px;
    }
    
    .error-message {
        color: #dc2626;
        font-size: 1rem;
    }
    
    /* 空状态 */
    .empty-state {
        text-align: center;
        padding: 60px 20px;
    }
    
    .empty-icon {
        font-size: 4rem;
        margin-bottom: 20px;
    }
    
    .empty-message {
        font-size: 1.2rem;
        color: #64748b;
        margin-bottom: 8px;
    }
    
    .empty-hint {
        font-size: 0.9rem;
        color: #94a3b8;
    }
    
    /* Streamlit 组件样式优化 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: white;
        padding: 8px;
        border-radius: 12px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        font-weight: 500;
    }
    
    div[data-testid="stMetricValue"] {
        font-size: 1.5rem !important;
    }
    
    div[data-testid="stMetricLabel"] {
        font-size: 0.85rem !important;
    }
    
    /* 按钮样式 */
    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.2s;
    }
    
    /* 侧边栏样式 */
    section[data-testid="stSidebar"] {
        background: white;
    }
    
    /* 隐藏元素 */
    .stDeployButton, footer, #MainMenu {
        display: none !important;
    }
    
    /* 表格样式 */
    .dataframe {
        border: none !important;
    }
    
    .dataframe thead th {
        background: #f8fafc !important;
        color: #475569 !important;
        font-weight: 600 !important;
        border-bottom: 2px solid #e2e8f0 !important;
    }
    
    .dataframe tbody tr:hover {
        background: #f8fafc !important;
    }
    
    .dataframe tbody td {
        border: none !important;
    }
    
    /* 自动刷新提示 */
    .auto-refresh-info {
        font-size: 0.8rem;
        color: #94a3b8;
        text-align: center;
        padding: 10px;
        background: #f8fafc;
        border-radius: 8px;
        margin-top: 15px;
    }
    </style>
    """


# ==================== 主应用 ====================

def main():
    # 页面配置
    st.set_page_config(
        page_title="💱 人民币汇率看板",
        page_icon="💱",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 注入自定义样式
    st.markdown(get_custom_css(), unsafe_allow_html=True)
    
    # 渲染头部
    render_header()
    
    # ==================== 侧边栏设置 ====================
    with st.sidebar:
        st.markdown("### ⚙️ 显示设置")
        
        # 币种选择
        st.markdown("**💰 选择货币**")
        selected_currencies = st.multiselect(
            "勾选要显示的货币",
            options=[c for c in SUPPORTED_CURRENCIES.keys() if c != "CNY"],
            default=["USD", "EUR", "JPY", "GBP"],
            format_func=lambda x: f"{SUPPORTED_CURRENCIES[x]['flag']} {SUPPORTED_CURRENCIES[x]['name']} ({x})",
            label_visibility="collapsed"
        )
        
        st.divider()
        
        # 时间范围选择
        st.markdown("**📅 数据范围**")
        time_range = st.selectbox(
            "选择历史数据范围",
            options=[1, 3, 7, 14, 30],
            index=2,
            format_func=lambda x: f"{x}天",
            label_visibility="collapsed"
        )
        
        st.divider()
        
        # 刷新设置
        st.markdown("**🔄 自动刷新**")
        auto_refresh = st.selectbox(
            "选择刷新间隔",
            options=list(REFRESH_OPTIONS.keys()),
            index=2,
            label_visibility="collapsed"
        )
        
        st.divider()
        
        # 显示模式
        st.markdown("**🎨 显示模式**")
        show_comparison = st.checkbox("显示货币对比图", value=True)
        show_table = st.checkbox("显示统计表格", value=True)
        
        st.divider()
        
        # 关于信息
        st.markdown("""
        <div style="font-size: 0.8rem; color: #94a3b8; line-height: 1.6;">
        <b>💡 使用说明</b><br>
        • 数据每5分钟自动缓存<br>
        • 点击刷新按钮立即更新<br>
        • 数据仅供参考，交易请以银行实际汇率为准<br><br>
        <b>📡 数据来源</b><br>
        European Central Bank<br>
        (Frankfurter API)
        </div>
        """, unsafe_allow_html=True)
    
    # ==================== 主内容区 ====================
    
    # 工具栏
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown("##### 📊 实时汇率总览")
    with col2:
        if st.button("🔄 刷新数据", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    with col3:
        if st.button("🗑️ 清除缓存", use_container_width=True):
            st.cache_data.clear()
            st.success("缓存已清除！")
            time.sleep(0.5)
            st.rerun()
    
    # 显示更新时间
    render_last_update()
    
    # ==================== 获取数据 ====================
    
    # 获取当前汇率
    with st.spinner("正在加载汇率数据..."):
        current_data, current_error = fetch_current_rates()
    
    # 获取历史数据
    with st.spinner("正在加载历史数据..."):
        historical_data, history_error = fetch_historical_rates(days=time_range)
    
    # 处理错误
    if current_error:
        render_error_card(current_error)
        return
    
    # 转换汇率为CNY基准
    rates = {}
    if current_data and "rates" in current_data:
        base_rates = current_data["rates"]
        for currency in SUPPORTED_CURRENCIES.keys():
            if currency in base_rates:
                # CNY 是基准，1 CNY = rate 单位的其他货币
                rates[currency] = 1.0 / base_rates[currency]
    
    if not rates:
        render_empty_state()
        return
    
    # ==================== 汇率卡片 ====================
    
    if selected_currencies:
        st.markdown("---")
        
        # 计算需要显示的行数
        num_cards = len(selected_currencies)
        num_rows = (num_cards + 2) // 3
        
        for row in range(num_rows):
            cols = st.columns(3)
            for col_idx in range(3):
                card_idx = row * 3 + col_idx
                if card_idx < num_cards:
                    currency = selected_currencies[card_idx]
                    if currency in rates:
                        rate = rates[currency]
                        metrics = calculate_rate_metrics(historical_data, rate, currency)
                        with cols[col_idx]:
                            render_currency_card(currency, rate, metrics, card_idx)
    else:
        st.info("👈 请在侧边栏选择要显示的货币")
    
    # ==================== 趋势图表 ====================
    
    if selected_currencies and len(selected_currencies) > 0:
        st.markdown("---")
        st.markdown("##### 📈 汇率趋势分析")
        
        # 为每个货币创建标签页
        tabs = st.tabs([
            f"{SUPPORTED_CURRENCIES[c]['flag']} {SUPPORTED_CURRENCIES[c]['name']} ({c})" 
            for c in selected_currencies
        ])
        
        for idx, currency in enumerate(selected_currencies):
            with tabs[idx]:
                if currency in rates:
                    price_series = get_price_series(historical_data, currency)
                    render_trend_chart(price_series, currency)
    
    # ==================== 货币对比图 ====================
    
    if show_comparison and selected_currencies and len(selected_currencies) > 1:
        st.markdown("---")
        render_comparison_chart(historical_data, selected_currencies)
    
    # ==================== 统计表格 ====================
    
    if show_table and selected_currencies:
        st.markdown("---")
        render_statistics_table(selected_currencies, rates, historical_data)
    
    # ==================== 自动刷新提示 ====================
    
    # 移除阻塞式的 time.sleep，改为显示提示
    refresh_interval = REFRESH_OPTIONS.get(auto_refresh, 0)
    if refresh_interval > 0:
        st.markdown(f"""
        <div class="auto-refresh-info">
            ⏱️ 页面将在 {refresh_interval} 秒后自动刷新...
        </div>
        """, unsafe_allow_html=True)
        
        # 使用 JavaScript 实现无阻塞刷新
        st.components.v1.html(f"""
        <meta http-equiv="refresh" content="{refresh_interval}">
        """, height=0)
    
    # ==================== 页脚 ====================
    
    st.markdown("""
    <div style="text-align: center; padding: 30px 20px; color: #94a3b8; font-size: 0.85rem;">
        <hr style="border: none; border-top: 1px solid #e2e8f0; margin-bottom: 20px;">
        <p style="margin: 0;">
            💱 人民币汇率实时看板 · 仅供参考 · 交易请以银行实际汇率为准<br>
            <span style="font-size: 0.75rem;">Powered by Streamlit & Frankfurter API</span>
        </p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()