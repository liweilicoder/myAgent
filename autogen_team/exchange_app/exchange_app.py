"""
人民币汇率展示应用
基于 Streamlit 的实时汇率查询工具

功能：
- 实时显示人民币对主要外币的汇率
- 显示24小时涨跌趋势（涨跌幅和涨跌额）
- 提供手动刷新功能
"""

import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# ============================================
# 配置常量
# ============================================

CURRENCIES: Dict[str, Dict[str, str]] = {
    "USD": {"name": "美元", "flag": "🇺🇸"},
    "JPY": {"name": "日元", "flag": "🇯🇵"},
    "GBP": {"name": "英镑", "flag": "🇬🇧"},
    "EUR": {"name": "欧元", "flag": "🇪🇺"},
    "HKD": {"name": "港币", "flag": "🇭🇰"},
}

API_BASE_URL = "https://api.frankfurter.app"
TIMEOUT_SECONDS = 10
MAX_RETRIES = 3  # 最大重试次数


# ============================================
# 辅助函数
# ============================================

def retry_request(url: str, params: Dict, max_retries: int = MAX_RETRIES) -> Optional[Dict]:
    """
    带重试机制的请求函数
    
    Args:
        url: 请求 URL
        params: 请求参数
        max_retries: 最大重试次数
    
    Returns:
        解析后的 JSON 数据，失败返回 None
    """
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=TIMEOUT_SECONDS)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            if attempt < max_retries - 1:
                time.sleep(1)  # 重试前等待 1 秒
            else:
                return None
    return None


@st.cache_data(ttl=300)  # 缓存5分钟
def get_current_rates() -> Optional[Dict]:
    """
    获取当前人民币汇率
    使用 Frankfurter API
    
    Returns:
        API 返回的汇率数据字典，失败返回 None
    """
    url = f"{API_BASE_URL}/latest"
    params = {"from": "CNY", "to": ",".join(CURRENCIES.keys())}
    data = retry_request(url, params)
    
    if data is None:
        st.error("获取汇率数据失败，请检查网络连接后重试")
    
    return data


def get_historical_rate(date: str) -> Optional[Dict]:
    """
    获取指定日期的历史汇率
    
    Args:
        date: 日期字符串，格式 YYYY-MM-DD
    
    Returns:
        API 返回的汇率数据字典，失败返回 None
    """
    url = f"{API_BASE_URL}/{date}"
    params = {"from": "CNY", "to": ",".join(CURRENCIES.keys())}
    return retry_request(url, params)


def fetch_rates_parallel() -> Tuple[Optional[Dict], Optional[Dict]]:
    """
    并行获取当前汇率和历史汇率
    
    Returns:
        (当前汇率数据, 历史汇率数据)
    """
    current_data = None
    historical_data = None
    
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_current = executor.submit(get_current_rates)
        future_historical = executor.submit(get_historical_rate, yesterday)
        
        try:
            current_data = future_current.result(timeout=TIMEOUT_SECONDS + 2)
        except Exception:
            current_data = None
            
        try:
            historical_data = future_historical.result(timeout=TIMEOUT_SECONDS + 2)
        except Exception:
            historical_data = None
    
    return current_data, historical_data


def calculate_changes(current: float, previous: float) -> Tuple[str, float, float]:
    """
    计算涨跌变化
    
    Args:
        current: 当前汇率
        previous: 历史汇率
    
    Returns:
        Tuple(趋势符号, 涨跌额, 涨跌幅%)
    """
    change_amount = current - previous
    change_percent = (change_amount / previous) * 100 if previous != 0 else 0
    
    if change_amount > 0:
        symbol = "↑"
    elif change_amount < 0:
        symbol = "↓"
    else:
        symbol = "→"
    
    return symbol, change_amount, change_percent


# ============================================
# Streamlit 页面配置
# ============================================

def configure_page():
    """配置页面基本信息"""
    st.set_page_config(
        page_title="人民币实时汇率",
        page_icon="💱",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # 自定义 CSS 样式
    st.markdown("""
    <style>
    .main-title {
        text-align: center;
        padding: 1rem 0;
        color: #1f77b4;
    }
    .currency-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .currency-card.up {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    }
    .currency-card.down {
        background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
    }
    .currency-card.neutral {
        background: linear-gradient(135deg, #747474 0%, #999999 100%);
    }
    .rate-value {
        font-size: 2rem;
        font-weight: bold;
        margin: 0.5rem 0;
    }
    .change-positive {
        color: #38ef7d;
        font-weight: bold;
    }
    .change-negative {
        color: #f45c43;
        font-weight: bold;
    }
    .change-neutral {
        color: #999999;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 8px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    }
    .info-box {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)


# ============================================
# 主应用逻辑
# ============================================

def main():
    configure_page()
    
    # 页面标题
    st.markdown('<h1 class="main-title">💱 人民币实时汇率</h1>', unsafe_allow_html=True)
    
    # 初始化 session_state
    if "refresh_count" not in st.session_state:
        st.session_state.refresh_count = 0
    
    # 刷新按钮
    col_refresh = st.columns([1, 2, 1])
    with col_refresh[1]:
        if st.button("🔄 刷新汇率", use_container_width=True):
            st.session_state.refresh_count += 1
            st.cache_data.clear()
            st.rerun()
    
    # 显示更新时间
    st.markdown(f"""
    <div class="info-box">
        📅 数据更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # 并行获取汇率数据
    with st.spinner("正在加载汇率数据..."):
        current_data, yesterday_data = fetch_rates_parallel()
    
    if current_data is None:
        st.error("❌ 无法获取汇率数据，请检查网络连接后重试")
        return
    
    # 构建汇率展示数据
    rates_display: List[Dict] = []
    
    for currency_code, currency_info in CURRENCIES.items():
        current_rate = current_data["rates"].get(currency_code)
        
        if current_rate is None:
            continue
        
        # 获取昨日汇率计算变化
        previous_rate = current_rate
        if yesterday_data and "rates" in yesterday_data:
            prev = yesterday_data["rates"].get(currency_code)
            if prev is not None:
                previous_rate = prev
        
        symbol, change_amount, change_percent = calculate_changes(current_rate, previous_rate)
        
        rates_display.append({
            "code": currency_code,
            "flag": currency_info["flag"],
            "name": currency_info["name"],
            "rate": current_rate,
            "symbol": symbol,
            "change_amount": change_amount,
            "change_percent": change_percent,
            "previous_rate": previous_rate
        })
    
    # 使用卡片式布局展示汇率
    st.markdown("### 📊 实时汇率")
    
    # 分行展示，每行3个货币
    cards_per_row = 3
    
    for row_start in range(0, len(rates_display), cards_per_row):
        row_currencies = rates_display[row_start:row_start + cards_per_row]
        cols = st.columns(cards_per_row)
        
        for idx, currency in enumerate(row_currencies):
            with cols[idx]:
                # 确定卡片颜色类
                if currency["change_percent"] > 0:
                    card_class = "currency-card up"
                elif currency["change_percent"] < 0:
                    card_class = "currency-card down"
                else:
                    card_class = "currency-card neutral"
                
                # 格式化涨跌显示
                if currency["change_percent"] > 0:
                    change_class = "change-positive"
                    change_text = f"↑ +{currency['change_percent']:.2f}%"
                elif currency["change_percent"] < 0:
                    change_class = "change-negative"
                    change_text = f"↓ {currency['change_percent']:.2f}%"
                else:
                    change_class = "change-neutral"
                    change_text = f"→ {currency['change_percent']:.2f}%"
                
                # 涨跌额显示
                amount_text = f"涨跌额: {'+' if currency['change_amount'] >= 0 else ''}{currency['change_amount']:.4f}"
                
                st.markdown(f"""
                <div class="{card_class}">
                    <h3>{currency['flag']} {currency['code']}</h3>
                    <p style="font-size: 0.9rem; opacity: 0.9;">{currency['name']}</p>
                    <div class="rate-value">{currency['rate']:.4f}</div>
                    <p class="{change_class}">{change_text}</p>
                    <p style="font-size: 0.75rem; opacity: 0.8;">{amount_text}</p>
                </div>
                """, unsafe_allow_html=True)
    
    # 表格展示详细数据
    st.markdown("### 📋 汇率详情表")
    
    # 构建 DataFrame
    df_data = []
    for currency in rates_display:
        status = "上涨 📈" if currency['change_percent'] > 0 else (
            "下跌 📉" if currency['change_percent'] < 0 else "持平 ➡️"
        )
        df_data.append({
            "货币": f"{currency['flag']} {currency['code']}",
            "货币名称": currency['name'],
            "当前汇率": f"{currency['rate']:.4f}",
            "昨日汇率": f"{currency['previous_rate']:.4f}",
            "涨跌额": f"{'+' if currency['change_amount'] >= 0 else ''}{currency['change_amount']:.4f}",
            "涨跌幅": f"{'+' if currency['change_percent'] >= 0 else ''}{currency['change_percent']:.2f}%",
            "状态": status
        })
    
    df = pd.DataFrame(df_data)
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "货币": st.column_config.TextColumn("货币", width="small"),
            "货币名称": st.column_config.TextColumn("货币名称", width="small"),
            "当前汇率": st.column_config.TextColumn("当前汇率", width="small"),
            "昨日汇率": st.column_config.TextColumn("昨日汇率", width="small"),
            "涨跌额": st.column_config.TextColumn("涨跌额", width="small"),
            "涨跌幅": st.column_config.TextColumn("涨跌幅", width="small"),
            "状态": st.column_config.TextColumn("状态", width="small"),
        }
    )
    
    # 底部信息
    st.divider()
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.8rem;">
        <p>数据来源: Frankfurter API | 仅供參考，实际交易汇率以银行柜台为准</p>
        <p>建议网络环境: 中国大陆可直接访问</p>
    </div>
    """, unsafe_allow_html=True)


# ============================================
# 入口
# ============================================

if __name__ == "__main__":
    main()