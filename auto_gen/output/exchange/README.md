# 💱 人民币汇率实时查

实时显示人民币兑主要货币汇率的 Web 应用。

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 运行应用
```bash
streamlit run exchange_rate_app.py
```

### 3. 访问
浏览器打开 http://localhost:8501

## ⚙️ 功能特性

- ✅ 实时汇率显示（8种主流货币）
- ✅ 涨跌幅展示
- ✅ 手动刷新 + 自动缓存
- ✅ 货币自由选择
- ✅ 响应式设计

## ⚠️ 注意事项

涨跌幅数据为模拟数据，实际项目中建议接入历史汇率 API 获取真实 24 小时变化。

## 📡 数据来源

使用 [ExchangeRate-API](https://www.exchangerate-api.com/) 提供的数据。