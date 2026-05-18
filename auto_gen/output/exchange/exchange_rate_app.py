"""
人民币汇率实时查应用 v2.0
- 支持双向汇率查询
- CNY → 外币 | 外币 → CNY
"""

import streamlit as st
import requests
from datetime import datetime
from typing import Dict, Optional
import time
from functools import wraps

# ==================== 配置 ====================

CURRENCY_CONFIG = {
    "USD": {"name": "美元", "symbol": "$", "flag": "🇺🇸"},
    "JPY": {"name": "日元", "symbol": "¥", "flag": "🇯🇵"},
    "GBP": {"name": "英镑", "symbol": "£", "flag": "🇬🇧"},
    "EUR": {"name": "欧元", "symbol": "€", "flag": "🇪🇺"},
    "HKD": {"name": "港币", "symbol": "HK$", "flag": "🇭🇰"},
    "KRW": {"name": "韩元", "symbol": "₩", "flag": "🇰🇷"},
    "CHF": {"name": "瑞士法郎", "symbol": "CHF", "flag": "🇨🇭"},
    "AUD": {"name": "澳元", "symbol": "A$", "flag": "🇦🇺"},
}

API_URL = "https://open.er-api.com/v6/latest/CNY"
CACHE_TTL = 300


# ==================== 工具函数 ====================

def with_retry(max_attempts=3, delay=1.0):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt < max_attempts - 1:
                        time.sleep(delay * (2 ** attempt))
                    else:
                        raise e

        return wrapper

    return decorator


def calculate_rate_change(current, base=None):
    is_simulated = base is None
    if base is None:
        base = current * 0.9995
    change = current - base
    percent = (change / base) * 100
    return {
        "change_value": change,
        "change_percent": percent,
        "is_up": change >= 0,
        "is_simulated": is_simulated
    }


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_exchange_rates():
    def _fetch():
        response = requests.get(API_URL, timeout=15)
        if response.status_code == 429:
            st.warning("⚠️ 请求过于频繁")
            return None
        response.raise_for_status()
        data = response.json()
        if data.get("result") != "success":
            raise ValueError("API 返回异常")
        return data

    try:
        return with_retry(max_attempts=2)(_fetch)()
    except requests.exceptions.Timeout:
        st.error("⏰ 请求超时")
        return None
    except requests.exceptions.ConnectionError:
        st.error("🔌 网络连接失败")
        return None
    except Exception as e:
        st.error(f"❌ 获取失败: {str(e)}")
        return None


def calculate_inverse_rate(cny_to_foreign: float) -> float:
    """计算反向汇率 (外币到人民币)"""
    return 1.0 / cny_to_foreign


def get_display_rate(code: str, rates: Dict, direction: str) -> tuple:
    """获取显示用的汇率和描述"""
    cny_to_foreign = rates.get(code)

    if direction == "CNY_TO_FOREIGN":
        # 1 CNY = X 外币
        rate = cny_to_foreign
        display = f"1 CNY = {rate:.4f} {CURRENCY_CONFIG[code]['symbol']}"
    else:
        # 1 外币 = Y CNY
        rate = calculate_inverse_rate(cny_to_foreign)
        display = f"1 {CURRENCY_CONFIG[code]['symbol']} = {rate:.4f} CNY"

    return rate, display


def render_currency_card(code: str, rate: float, display: str, change: Dict):
    """渲染货币卡片"""
    config = CURRENCY_CONFIG.get(code, {"name": code, "flag": "💰", "symbol": ""})
    arrow = "📈" if change["is_up"] else "📉"
    sign = "+" if change["is_up"] else "-"

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 25px; border-radius: 16px; color: white; 
                text-align: center; margin: 10px 0;">
        <div style="font-size: 2.5em; margin-bottom: 10px;">{config['flag']}</div>
        <div style="font-size: 1.3em; font-weight: bold;">{config['name']} ({code})</div>
        <div style="font-size: 1.8em; font-weight: bold; margin: 15px 0; font-family: 'Courier New', monospace;">
            {display}
        </div>
        <div style="background: rgba(255,255,255,0.2); padding: 8px 15px; border-radius: 20px; display: inline-block;">
            {arrow} {sign}{abs(change['change_percent']):.2f}%
        </div>
        {'<div style="font-size: 0.8em; opacity: 0.8; margin-top: 5px;">📊 模拟数据</div>' if change.get('is_simulated') else ''}
    </div>
    """, unsafe_allow_html=True)


# ==================== 主程序 ====================

def main():
    st.set_page_config(page_title="汇率实时查", page_icon="💱", layout="wide")

    # 标题
    st.markdown("<h1 style='text-align: center; color: #2c3e50;'>💱 汇率实时查</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #7f8c8d;'>支持双向汇率查询 | 数据每5分钟自动更新</p>",
                unsafe_allow_html=True)

    # 刷新按钮
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔄 刷新汇率", use_container_width=True, type="primary"):
            st.cache_data.clear()
            st.rerun()

    st.markdown("---")

    # 获取数据
    data = get_exchange_rates()
    if data is None:
        st.error("🚫 获取失败，请检查网络后重试")
        if st.button("🔄 重试"):
            st.cache_data.clear()
            st.rerun()
        return

    rates = data["rates"]
    available_currencies = [c for c in CURRENCY_CONFIG.keys() if c in rates]

    # ==================== 侧边栏设置 ====================
    with st.sidebar:
        st.markdown("### ⚙️ 设置")
        st.markdown("---")

        # 方向选择
        direction = st.radio(
            "📊 汇率方向",
            options=["CNY_TO_FOREIGN", "FOREIGN_TO_CNY"],
            format_func=lambda x: "💰 CNY → 外币" if x == "CNY_TO_FOREIGN" else "💵 外币 → CNY",
            help="选择汇率查询方向"
        )

        st.markdown("---")

        # 货币选择
        selected = st.multiselect(
            "🎯 选择货币",
            options=available_currencies,
            default=["USD", "JPY", "GBP", "EUR"],
            format_func=lambda x: f"{CURRENCY_CONFIG[x]['flag']} {CURRENCY_CONFIG[x]['name']}"
        )

    # ==================== 主内容区 ====================

    # 方向说明
    if direction == "CNY_TO_FOREIGN":
        st.success("💰 当前显示: 1 人民币 = X 外币")
    else:
        st.success("💵 当前显示: 1 外币 = X 人民币")

    st.markdown("### 💰 汇率卡片")

    # 展示货币卡片
    display_currencies = selected if selected else ["USD", "JPY", "GBP", "EUR"]
    cols = st.columns(2)

    for idx, code in enumerate(display_currencies):
        with cols[idx % 2]:
            if code in rates:
                rate, display = get_display_rate(code, rates, direction)
                change = calculate_rate_change(rate)
                render_currency_card(code, rate, display, change)

        if idx % 2 == 1:
            st.markdown("")

    # ==================== 完整汇率表 ====================
    st.markdown("---")
    st.markdown("### 📋 完整汇率表")

    table_data = []
    for code in available_currencies:
        if code in rates:
            config = CURRENCY_CONFIG[code]
            if direction == "CNY_TO_FOREIGN":
                rate = rates[code]
                rate_display = f"1 CNY = {rate:.4f} {config['symbol']}"
            else:
                rate = calculate_inverse_rate(rates[code])
                rate_display = f"1 {config['symbol']} = {rate:.4f} CNY"

            change = calculate_rate_change(rate)
            sign = "+" if change["is_up"] else ""

            table_data.append({
                "货币": f"{config['flag']} {config['name']}",
                "代码": code,
                "汇率": rate_display,
                "涨跌幅": f"{sign}{change['change_percent']:.2f}%"
            })

    if table_data:
        st.dataframe(table_data, use_container_width=True, hide_index=True)

    # ==================== 汇率换算器 ====================
    st.markdown("---")
    st.markdown("### 🧮 快速换算")

    col1, col2, col3 = st.columns([2, 1, 2])

    with col1:
        calc_currency = st.selectbox("选择货币", options=display_currencies,
                                     format_func=lambda x: f"{CURRENCY_CONFIG[x]['flag']} {CURRENCY_CONFIG[x]['name']}")
        amount = st.number_input("输入金额", value=100, min_value=0)

    with col3:
        if calc_currency and calc_currency in rates:
            current_rate, _ = get_display_rate(calc_currency, rates, direction)
            config = CURRENCY_CONFIG[calc_currency]

            if direction == "CNY_TO_FOREIGN":
                result = amount * current_rate
                st.success(f"**{amount} CNY = {result:.2f} {config['symbol']}**")
            else:
                result = amount * current_rate
                st.success(f"**{amount} {config['symbol']} = {result:.2f} CNY**")


if __name__ == "__main__":
    main()