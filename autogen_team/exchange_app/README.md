# 💱 人民币汇率实时看板

> 基于 Streamlit + Frankfurter API 的实时汇率监控应用

## 📖 项目简介

一款简洁美观的人民币汇率实时监控应用，支持多种主流货币的实时汇率显示、24小时涨跌分析、趋势图表展示。

## ✨ 功能特性

### 核心功能
- ✅ **多币种支持**：USD、EUR、JPY、GBP、HKD、KRW、CNY、AUD、CAD、CHF
- ✅ **实时汇率**：显示人民币兑各货币的实时汇率
- ✅ **涨跌分析**：24小时涨跌幅、涨跌额、最高价、最低价
- ✅ **趋势图表**：交互式折线图，支持缩放和悬停查看详情
- ✅ **货币对比**：多货币涨跌幅对比图
- ✅ **统计表格**：完整的汇率数据汇总表

### 用户体验
- 🎨 **精美卡片设计**：金融风格深蓝渐变卡片
- 📊 **涨跌颜色标识**：绿色上涨、红色下跌
- 🔄 **手动刷新**：一键获取最新数据
- ⚡ **智能缓存**：5分钟自动缓存，减少API请求
- 📱 **响应式布局**：适配桌面和移动端

## 🛠️ 技术栈

| 技术 | 用途 |
|------|------|
| Streamlit | Web 应用框架 |
| Plotly | 交互式图表 |
| Pandas | 数据处理 |
| Requests | HTTP 请求 |
| Frankfurter API | 汇率数据源 |

## 🚀 快速开始

### 1. 安装依赖

```bash
cd exchange_app
pip install -r requirements.txt
```

### 2. 启动应用

```bash
streamlit run app.py
```

### 3. 访问应用

打开浏览器访问 `http://localhost:8501`

## 📁 项目结构

```
exchange_app/
├── app.py              # 主应用代码
├── requirements.txt    # Python 依赖
├── prd.md             # 产品需求文档
└── README.md          # 项目说明文档
```

## 🎮 功能预览

### 汇率卡片
- 显示货币名称、符号、当前汇率
- 24小时涨跌幅和涨跌额
- 最高价/最低价

### 趋势图表
- 交互式折线图
- 涨跌幅柱状图
- 支持缩停查看

### 侧边栏设置
- 币种选择（多选）
- 数据范围（1-30天）
- 自动刷新间隔
- 显示模式切换

## ⚙️ 配置选项

### 环境变量（可选）
```bash
# 设置 Streamlit 端口
export STREAMLIT_SERVER_PORT=8501

# 禁用分析
export STREAMLIT_ANALYTICS=false
```

### 启动参数
```bash
streamlit run app.py --server.port 8501 --server.headless true
```

## 📡 API 数据源

本应用使用 [Frankfurter API](https://www.frankfurter.app/) 获取汇率数据，该 API 提供：
- 实时汇率
- 历史汇率
- 欧洲央行数据源

## 🔧 常见问题

### Q: 数据不更新怎么办？
A: 点击"刷新数据"按钮或清除缓存后重新加载

### Q: API 请求失败？
A: 检查网络连接，Frankfurter API 可能暂时不可用

### Q: 如何添加新货币？
A: 在 `SUPPORTED_CURRENCIES` 字典中添加新条目

## 🔐 安全说明

本应用注重代码安全：
- **XSS 防护**：所有用户可见的文本均经过 HTML 转义
- **输入验证**：API 响应数据经过严格验证
- **超时保护**：请求超时时间设置为 15 秒
- **错误处理**：统一异常捕获，避免应用崩溃

## 🧪 开发指南

### 添加新货币
```python
# 在 SUPPORTED_CURRENCIES 字典中添加
"CAD": {"name": "加元", "symbol": "C$", "flag": "🇨🇦", "decimals": 4},
```

### 修改缓存时间
```python
CACHE_TTL = 300  # 默认 5 分钟，可在配置区修改
```

### 自定义样式
```python
# 修改 get_custom_css() 函数中的 CSS 样式
```

## 📝 许可证

本项目仅供学习和参考使用，数据仅供参考，不构成投资建议。

## 🙏 致谢

- [Streamlit](https://streamlit.io/) - 极棒的 Web 应用框架
- [Frankfurter](https://www.frankfurter.app/) - 开源汇率 API
- [Plotly](https://plotly.com/) - 交互式可视化库

---

**⚠️ 免责声明**：本应用提供的汇率数据仅供参考，不构成任何金融建议。实际交易请以银行或正规金融机构公布的汇率为准。