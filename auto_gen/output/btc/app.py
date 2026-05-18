"""
比特币价格显示应用
==================
使用 Streamlit 和 CoinGecko API 构建的实时价格追踪工具

作者: 开发团队
版本: 1.1.0
"""

import streamlit as st
import requests
from datetime import datetime
from typing import Optional, Dict, Any

# ============================================
# 配置常量
# ============================================

st.set_page_config(
    page_title="₿ 比特币价格追踪",
    page_icon="₿",
    layout="centered"
)

API_URL = "https://api.coingecko.com/api/v3/simple/price"
MAX_RETRIES = 3
RETRY_COOLDOWN = 10


# ============================================
# 数据获取模块
# ============================================

@st.cache_data(ttl=30)
def get_btc_price() -> Optional[Dict[str, Any]]:
    """
    从 CoinGecko API 获取比特币价格数据

    Returns:
        包含价格和变化数据的字典，失败时返回 None
    """
    try:
        response = requests.get(
            API_URL,
            params={
                "ids": "bitcoin",
                "vs_currencies": "usd",
                "include_24hr_change": "true"
            },
            timeout=10
        )

        response.raise_for_status()
        data = response.json()

        btc = data.get("bitcoin", {})
        price = btc.get("usd")
        change = btc.get("usd_24h_change")

        # 数据验证
        if price is None or change is None:
            return {
                "success": False,
                "error": "API返回数据格式异常",
                "last_updated": datetime.now()
            }

        # 数值类型检查
        if not isinstance(price, (int, float)) or not isinstance(change, (int, float)):
            return {
                "success": False,
                "error": "数据格式错误",
                "last_updated": datetime.now()
            }

        return {
            "success": True,
            "price": float(price),
            "change_24h": float(change),
            "last_updated": datetime.now()
        }

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "请求超时，请检查网络连接后重试",
            "last_updated": datetime.now()
        }
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "error": "网络连接失败，请检查网络设置",
            "last_updated": datetime.now()
        }
    except requests.exceptions.HTTPError as e:
        return {
            "success": False,
            "error": f"API请求失败: HTTP {e.response.status_code}",
            "last_updated": datetime.now()
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"未知错误: {str(e)}",
            "last_updated": datetime.now()
        }


# ============================================
# CSS 样式
# ============================================

def load_css():
    """加载自定义CSS样式"""
    st.markdown("""
    <style>
        .main-title {
            text-align: center;
            color: #F7931A;
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 0.5rem;
        }
        .subtitle {
            text-align: center;
            color: #666;
            font-size: 1rem;
            margin-bottom: 2rem;
        }
        .status-info {
            font-size: 0.85rem;
            color: #888;
            text-align: center;
            margin-top: 1rem;
        }
        .error-box {
            background-color: #fee;
            border-left: 4px solid #c00;
            padding: 1rem;
            border-radius: 8px;
        }
        .stMetric {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            padding: 1.5rem;
            border-radius: 15px;
            border: 1px solid #333;
        }
    </style>
    """, unsafe_allow_html=True)


# ============================================
# 主应用
# ============================================

def main():
    """主应用入口"""
    load_css()

    # 页面标题
    st.markdown('<p class="main-title">₿ 比特币价格追踪</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">实时加密货币市场数据</p>', unsafe_allow_html=True)

    # ============================================
    # 侧边栏设置
    # ============================================

    with st.sidebar:
        st.header("⚙️ 设置")

        auto_refresh = st.checkbox(
            "🔄 自动刷新",
            value=True,
            help="启用后页面将自动刷新"
        )

        refresh_interval = st.slider(
            "刷新间隔（秒）",
            min_value=15,
            max_value=300,
            value=60,
            step=15,
            disabled=not auto_refresh
        )

        st.divider()
        st.caption("📡 数据来源: CoinGecko")
        st.caption("⏱️ 缓存时间: 30秒")

    # ============================================
    # 刷新按钮区域
    # ============================================

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔄 刷新价格", type="primary", use_container_width=True):
            # 检查是否在冷却中
            if st.session_state.get("last_error_time"):
                elapsed = (datetime.now() - st.session_state.last_error_time).seconds
                if elapsed < RETRY_COOLDOWN:
                    remaining = RETRY_COOLDOWN - elapsed
                    st.warning(f"⏳ 请等待 {remaining} 秒后再试")
                else:
                    st.rerun()
            else:
                st.rerun()

    # ============================================
    # 数据获取与展示
    # ============================================

    with st.spinner("正在获取价格数据..."):
        data = get_btc_price()

    if data["success"]:
        price = data["price"]
        change = data["change_24h"]
        is_positive = change >= 0

        # 主价格显示
        st.subheader("💰 当前价格")

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                label="比特币 (BTC)",
                value=f"${price:,.2f}",
                delta=f"{change:.2f}%",
                delta_color="normal"
            )

        with col2:
            change_amount = price * (change / 100)
            st.metric(
                label="24小时变化",
                value=f"${abs(change_amount):,.2f}",
                delta=f"{change_amount:+.2f}",
                delta_color="normal"
            )

        # 市场状态信息
        st.markdown("---")

        col1, col2, col3 = st.columns(3)

        with col1:
            trend_icon = "📈" if is_positive else "📉"
            trend_text = "上涨" if is_positive else "下跌"
            st.info(f"{trend_icon} {trend_text} {abs(change):.2f}%")

        with col2:
            st.info(f"💵 最新价: ${price:,.0f}")

        with col3:
            st.info(f"📊 24h变化额: ${abs(change_amount):,.2f}")

        # 最后更新时间
        last_update = data["last_updated"].strftime("%Y-%m-%d %H:%M:%S")
        st.markdown(f'<p class="status-info">🕐 最后更新: {last_update}</p>', unsafe_allow_html=True)

        # ============================================
        # 自动刷新实现
        # ============================================

        if auto_refresh:
            st.markdown(
                f'<meta http-equiv="refresh" content="{refresh_interval}">',
                unsafe_allow_html=True
            )

    else:
        # 错误处理界面
        st.error("❌ 获取数据失败")

        st.markdown(f"""
        <div class="error-box">
            <strong>错误信息:</strong><br>
            {data.get('error', '未知错误')}
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("🔄 重试", type="secondary"):
                st.session_state.last_error_time = datetime.now()
                st.rerun()

        st.info("💡 提示: 请检查网络连接，或稍后重试")


# ============================================
# 入口点
# ============================================

if __name__ == "__main__":
    main()
