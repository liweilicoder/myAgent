# ₿ 比特币价格追踪

一个使用 Streamlit 构建的实时比特币价格显示应用。

## 功能特性

- ✅ 实时显示比特币当前价格（USD）
- ✅ 显示 24 小时价格变化趋势
- ✅ 支持手动刷新
- ✅ 支持自动刷新（可配置间隔）
- ✅ 友好的错误处理
- ✅ 涨跌颜色区分

## 技术栈

- **前端框架**: Streamlit
- **数据来源**: CoinGecko API（免费，无需 API Key）
- **编程语言**: Python 3.8+

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动应用

```bash
streamlit run app.py
```

### 3. 访问应用

在浏览器中打开 http://localhost:8501

## 项目结构

```
bitcoin-price-app/
├── app.py              # 主应用文件
├── requirements.txt    # 依赖列表
└── README.md          # 使用说明
```

## 配置选项

| 选项 | 说明 | 默认值 |
|------|------|--------|
| 自动刷新 | 是否启用自动刷新 | 开启 |
| 刷新间隔 | 自动刷新的时间间隔（秒） | 60 |

## 注意事项

- CoinGecko API 有速率限制，请勿频繁刷新
- 免费 API 响应可能有延迟
- 数据缓存时间: 30 秒

## License

MIT License