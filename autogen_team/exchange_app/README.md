# 💱 人民币汇率实时查看应用

一个基于 Streamlit 构建的简洁美观的汇率展示应用，实时显示人民币对主要外币的汇率及24小时趋势。

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## ✨ 功能特性

- 📊 **多货币支持**: 支持美元、欧元、日元、英镑、港币
- 📈 **实时汇率**: 自动获取最新汇率数据
- 📉 **趋势分析**: 24小时汇率变化趋势图表
- 🔄 **手动刷新**: 一键刷新获取最新数据
- 🎨 **美观界面**: 卡片式布局，颜色区分涨跌
- ⏱️ **智能缓存**: 5分钟数据缓存，减少API调用

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行应用

```bash
streamlit run app.py
```

应用将在浏览器中自动打开，默认地址：`http://localhost:8501`

## 📁 项目结构

```
exchange_app/
├── app.py              # 主应用文件
├── requirements.txt    # Python 依赖清单
├── README.md           # 本文档
└── prd.md              # 产品需求文档
```

## 🖥️ 界面预览

### 主页面
- 顶部显示数据更新时间
- 中间展示5种货币的汇率卡片
- 每个卡片包含：货币名称、当前汇率、24小时涨跌

### 货币卡片
- 左侧：货币图标、中英文名称、当前汇率数值
- 右侧：24小时涨跌额和涨跌幅
- 下方：24小时趋势折线图

## ⚙️ 配置说明

### 更换 API
如需更换汇率数据源，请修改 `app.py` 中的 `API_BASE_URL`：

```python
API_BASE_URL = "https://your-api-url.com/v4/latest/CNY"
```

### 添加新货币
在 `SUPPORTED_CURRENCIES` 字典中添加：

```python
"CNY": {"name": "人民币", "symbol": "¥", "flag": "🇨🇳"},
```

## ⚠️ 注意事项

1. **免费API限制**: 当前使用的免费API有请求频率限制
2. **历史数据**: 趋势图数据为模拟数据，实际项目中应使用提供历史数据的API
3. **免责声明**: 汇率数据仅供参考，不构成投资建议

## 🔧 故障排除

### 问题：应用无法启动
```bash
# 检查Python版本
python --version

# 重新安装依赖
pip uninstall -y streamlit requests plotly
pip install -r requirements.txt
```

### 问题：数据加载失败
- 检查网络连接
- API可能暂时不可用，等待后重试
- 查看终端中的错误日志

### 问题：界面显示异常
- 使用 Chrome、Firefox 或 Edge 浏览器
- 清除浏览器缓存
- 尝试强制刷新页面 (Ctrl+F5 / Cmd+Shift+R)

## 📝 开发说明

### 技术栈
- **Web框架**: Streamlit
- **数据可视化**: Plotly
- **HTTP请求**: Requests
- **数据源**: Exchange Rate API

### 生产部署建议
1. 使用 Streamlit Cloud 或 Heroku 部署
2. 配置环境变量存储敏感信息
3. 考虑使用付费API获得更稳定的数据源

## 📄 许可证

本项目采用 MIT 许可证，详情请查看 [LICENSE](LICENSE) 文件。

---

*如有问题或建议，请提交 Issue 或 Pull Request*