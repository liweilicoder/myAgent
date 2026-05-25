# -*- coding: utf-8 -*-
"""
人民币汇率实时查看应用
==============================
功能：
- 支持25+种货币汇率实时查询
- 两种显示模式切换（1 RMB = ? 外币 / 1 外币 = ? RMB）
- 24小时趋势图表展示
- 多货币自由选择
"""

import streamlit as st
import requests
import plotly.graph_objects as go
from datetime import datetime
from typing import Literal
import random

# 导入配置
from config import (
    CURRENCY_CONFIG,
    CURRENCY_PRESETS,
    ALL_CURRENCIES,
    get_currency_info,
)

# ==================== 配置区 ====================

# API 配置
API_BASE_URL = "https://api.exchangerate-api.com/v4/latest/CNY"
API_TIMEOUT = 10  # 请求超时时间（秒）
CACHE_TTL = 300   # 缓存时间（秒）

# 页面配置
st.set_page_config(
    page_title="人民币汇率实时查看",
    page_icon="💱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义样式
st.markdown("""
<style>
    /* 主标题样式 */
    .main-title {
        text-align: center;
        padding: 20px 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 12px;
        margin-bottom: 20px;
    }
    
    /* 货币卡片样式 */
    .currency-card {
        background: white;
        border-radius: 12px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border: 1px solid #e2e8f0;
        transition: transform 0.2s;
    }
    
    .currency-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.12);
    }
    
    /* 汇率数值样式 */
    .rate-value {
        font-size: 28px;
        font-weight: bold;
        color: #1e293b;
    }
    
    /* 涨幅样式 */
    .rate-up {
        color: #22c55e;
        background: rgba(34,197,94,0.1);
        padding: 4px 12px;
        border-radius: 20px;
    }
    
    .rate-down {
        color: #ef4444;
        background: rgba(239,68,68,0.1);
        padding: 4px 12px;
        border-radius: 20px;
    }
    
    /* 分组标题样式 */
    .group-header {
        padding: 10px 15px;
        background: #f1f5f9;
        border-radius: 8px;
        margin: 15px 0 10px 0;
        font-weight: bold;
        color: #475569;
    }
    
    /* 模式切换样式 */
    .mode-indicator {
        text-align: center;
        padding: 10px;
        background: linear-gradient(135deg, #f8fafc, #e2e8f0);
        border-radius: 8px;
        margin-bottom: 15px;
        font-weight: bold;
    }
    
    /* 状态标签样式 */
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
    }
    
    .status-success {
        background: #22c55e;
        color: white;
    }
    
    .status-error {
        background: #ef4444;
        color: white;
    }
    
    /* 趋势图表容器 */
    .chart-container {
        background: #fafafa;
        border-radius: 8px;
        padding: 10px;
    }
</style>
""", unsafe_allow_html=True)


# ==================== 工具函数 ====================

@st.cache_data(ttl=CACHE_TTL)
def fetch_exchange_rates() -> dict:
    """
    获取人民币汇率数据
    使用缓存机制，5分钟内相同请求不会重复调用API
    """
    try:
        with st.spinner("正在获取汇率数据..."):
            response = requests.get(API_BASE_URL, timeout=API_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            
            return {
                "success": True,
                "data": data,
                "timestamp": datetime.now(),
                "error": None
            }
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "data": None,
            "timestamp": datetime.now(),
            "error": "请求超时，请检查网络连接后重试"
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "data": None,
            "timestamp": datetime.now(),
            "error": f"获取汇率数据失败: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "timestamp": datetime.now(),
            "error": f"未知错误: {str(e)}"
        }


def generate_trend_data(base_rate: float, num_points: int = 24) -> list[float]:
    """
    生成模拟的24小时趋势数据
    实际项目中应替换为真实的历史数据API
    """
    trend = []
    current = base_rate
    
    for i in range(num_points):
        # 模拟小幅波动
        change_percent = random.uniform(-0.005, 0.005)
        current = current * (1 + change_percent)
        trend.append(round(current, 4))
    
    # 确保最后一个数据点接近实际汇率
    trend[-1] = base_rate
    return trend


def calculate_change_metrics(trend: list[float]) -> tuple[float, float]:
    """
    计算涨跌幅和涨跌额
    """
    start_rate = trend[0]
    end_rate = trend[-1]
    change_amount = end_rate - start_rate
    change_percent = (change_amount / start_rate) * 100 if start_rate != 0 else 0
    return change_amount, change_percent


def create_trend_chart(
    trend: list[float], 
    currency_code: str,
    mode: str = "rmb_to_foreign"
) -> go.Figure:
    """
    创建汇率趋势折线图
    """
    hours = list(range(len(trend)))
    change_amount, change_percent = calculate_change_metrics(trend)
    is_positive = change_amount >= 0
    
    # 颜色设置
    line_color = "#22c55e" if is_positive else "#ef4444"
    fill_color = "rgba(34,197,94,0.1)" if is_positive else "rgba(239,68,68,0.1)"
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=hours,
        y=trend,
        mode="lines+markers",
        fill="tozeroy",
        fillcolor=fill_color,
        line=dict(color=line_color, width=2.5),
        marker=dict(size=6, color=line_color),
        hovertemplate=f"<b>{currency_code}</b><br>时间: %{{x}}:00<br>汇率: %{{y:.4f}}<extra></extra>"
    ))
    
    # 图表布局
    fig.update_layout(
        height=180,
        margin=dict(l=40, r=20, t=10, b=40),
        showlegend=False,
        xaxis=dict(
            title="时间（小时）",
            showgrid=True,
            gridcolor="rgba(128,128,128,0.15)",
            zeroline=False,
            dtick=4,
        ),
        yaxis=dict(
            title="汇率",
            showgrid=True,
            gridcolor="rgba(128,128,128,0.15)",
            zeroline=False,
        ),
        plot_bgcolor="white",
        paper_bgcolor="white",
        hovermode="x unified",
    )
    
    return fig


def render_currency_card(
    code: str,
    rate: float,
    mode: Literal["rmb_to_foreign", "foreign_to_rmb"]
) -> None:
    """
    渲染单个货币卡片
    """
    info = get_currency_info(code)
    if not info:
        return
    
    # 根据模式计算显示汇率
    if mode == "foreign_to_rmb":
        display_rate = 1 / rate if rate != 0 else 0
        rate_label = f"1 {info['symbol']} = {display_rate:.4f} CNY"
        unit_label = f"1 外币 = {display_rate:.4f} 人民币"
    else:
        display_rate = rate
        rate_label = f"1 CNY = {display_rate:.4f} {info['symbol']}"
        unit_label = f"1 人民币 = {display_rate:.4f} 外币"
    
    # 生成趋势数据
    trend = generate_trend_data(rate)
    change_amount, change_percent = calculate_change_metrics(trend)
    is_positive = change_amount >= 0
    
    # 涨跌样式
    arrow = "↑" if is_positive else "↓"
    sign = "+" if is_positive else ""
    change_color = "#22c55e" if is_positive else "#ef4444"
    change_bg = "rgba(34,197,94,0.1)" if is_positive else "rgba(239,68,68,0.1)"
    
    # 图表
    fig = create_trend_chart(trend, code, mode)
    
    # 使用 columns 布局创建卡片
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # 货币信息头部
        st.markdown(f"""
        ### {info['flag']} {code}
        **{info['name_cn']}** | {info['name']}
        """)
        
        # 当前汇率（根据模式显示）
        if mode == "rmb_to_foreign":
            st.markdown(f"""
            <div style="
                text-align: center;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 12px;
                color: white;
                margin: 10px 0;
            ">
                <div style="font-size: 14px; opacity: 0.9;">1 人民币 =</div>
                <div style="font-size: 32px; font-weight: bold;">{rate:.4f}</div>
                <div style="font-size: 18px;">{info['symbol']}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="
                text-align: center;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 12px;
                color: white;
                margin: 10px 0;
            ">
                <div style="font-size: 14px; opacity: 0.9;">1 {info['symbol']} =</div>
                <div style="font-size: 32px; font-weight: bold;">{1/rate:.4f}</div>
                <div style="font-size: 18px;">CNY</div>
            </div>
            """, unsafe_allow_html=True)
        
        # 涨跌信息
        st.markdown(f"""
        <div style="
            padding: 12px;
            background: {change_bg};
            border-radius: 8px;
            border-left: 4px solid {change_color};
            margin-top: 10px;
        ">
            <div style="font-size: 12px; color: #64748b; margin-bottom: 5px;">
                📊 24小时变化
            </div>
            <div style="font-size: 20px; font-weight: bold; color: {change_color};">
                {arrow} {sign}{abs(change_amount):.4f}
            </div>
            <div style="font-size: 14px; color: {change_color};">
                ({sign}{abs(change_percent):.2f}%)
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # 趋势图表
        st.markdown("""
        <div style="padding: 10px 0;">
            <span style="color: #64748b; font-size: 14px;">📈 24小时趋势</span>
        </div>
        """, unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")


# ==================== 主应用 ====================

def main():
    # 顶部标题
    st.markdown("""
    <div class="main-title">
        <h1>💱 人民币汇率实时查看</h1>
        <p style="font-size: 14px; opacity: 0.9; margin-top: 5px;">
            支持 25+ 种货币 · 实时更新 · 趋势分析
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # ==================== 侧边栏 ====================
    with st.sidebar:
        st.header("⚙️ 设置")
        
        # 显示模式切换
        st.markdown("### 📐 显示模式")
        mode = st.radio(
            "选择换算方式",
            options=["rmb_to_foreign", "foreign_to_rmb"],
            format_func=lambda x: "💵 1 RMB = ? 外币" if x == "rmb_to_foreign" else "💴 1 外币 = ? RMB",
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # 货币选择
        st.markdown("### 🌐 选择货币")
        
        # 快捷预设
        preset_options = list(CURRENCY_PRESETS.keys())
        selected_preset = st.selectbox(
            "快捷选择",
            options=preset_options,
            index=0,
            label_visibility="collapsed"
        )
        
        # 使用预设更新选择
        if selected_preset and selected_preset in CURRENCY_PRESETS:
            default_selection = CURRENCY_PRESETS[selected_preset]
        else:
            default_selection = []
        
        # 多选货币
        selected_currencies = st.multiselect(
            "选择要显示的货币",
            options=ALL_CURRENCIES,
            default=default_selection,
            format_func=lambda x: f"{get_currency_info(x)['flag']} {x} - {get_currency_info(x)['name_cn']}",
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # 刷新按钮
        if st.button("🔄 刷新数据", use_container_width=True, type="primary"):
            st.cache_data.clear()
            st.rerun()
        
        # 信息说明
        st.markdown("""
        ### ℹ️ 使用说明
        1. 选择显示模式和货币种类
        2. 点击刷新获取最新数据
        3. 查看各货币的实时汇率和趋势
        
        ### 📊 数据说明
        - 数据约 **5分钟** 自动缓存
        - 趋势图为 **模拟数据**
        - 实际数据需使用付费API
        """)
    
    # ==================== 主内容区 ====================
    
    # 获取汇率数据
    result = fetch_exchange_rates()
    
    # 错误处理
    if not result["success"]:
        st.error(f"❌ {result['error']}")
        st.info("💡 请检查网络连接后点击侧边栏的「刷新数据」按钮重试")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🔄 重试", use_container_width=True):
                st.cache_data.clear()
                st.rerun()
        return
    
    data = result["data"]
    rates = data.get("rates", {})
    
    # 顶部状态栏
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        st.success("🟢 数据正常")
    with col2:
        mode_text = "1 RMB = ? 外币" if mode == "rmb_to_foreign" else "1 外币 = ? RMB"
        st.markdown(f"""
        <div style="
            text-align: center;
            padding: 12px;
            background: linear-gradient(135deg, #f1f5f9, #e2e8f0);
            border-radius: 10px;
            display: flex;
            justify-content: space-around;
            align-items: center;
        ">
            <div><b>📅 数据日期</b>: {data.get('date', '未知')}</div>
            <div><b>🕐 更新时间</b>: {result['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}</div>
            <div><b>📐 显示模式</b>: {mode_text}</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"**已选择 {len(selected_currencies)} 种货币**")
    
    st.markdown("---")
    
    # 货币展示区
    if not selected_currencies:
        st.warning("⚠️ 请在左侧边栏选择要显示的货币")
        st.info("💡 提示：可以使用「快捷选择」快速选择常用货币组合")
        
        # 显示默认推荐
        st.markdown("### 🔥 热门货币推荐")
        default_currencies = ["USD", "EUR", "GBP", "JPY", "HKD"]
        for code in default_currencies:
            if code in rates:
                info = get_currency_info(code)
                st.markdown(f"- {info['flag']} **{code}** - {info['name_cn']}")
    else:
        # 按分组显示货币
        st.subheader(f"📊 已选择 {len(selected_currencies)} 种货币")
        
        # 将选择的货币按分组整理
        grouped_currencies = {}
        for code in selected_currencies:
            info = get_currency_info(code)
            if info:
                group = info["group"]
                if group not in grouped_currencies:
                    grouped_currencies[group] = []
                grouped_currencies[group].append(code)
        
        # 分组显示
        for group, currencies in grouped_currencies.items():
            with st.expander(f"{group} ({len(currencies)}种)", expanded=True):
                # 创建卡片网格
                for code in currencies:
                    if code in rates:
                        with st.container():
                            render_currency_card(code, rates[code], mode)
    
    # 底部免责声明
    st.markdown("---")
    st.markdown("""
    <div style="
        text-align: center;
        padding: 20px;
        background: #f8fafc;
        border-radius: 10px;
        color: #64748b;
    ">
        <p><b>⚠️ 免责声明</b></p>
        <p>本应用提供的汇率数据仅供参考，不构成任何投资建议。</p>
        <p>实际交易汇率可能因金融机构和交易时间而异。</p>
    </div>
    """, unsafe_allow_html=True)


# ==================== 入口 ====================

if __name__ == "__main__":
    main()