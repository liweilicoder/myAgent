# -*- coding: utf-8 -*-
"""
货币配置模块
定义支持的货币种类、分组和显示配置
"""

from typing import TypedDict

# ==================== 类型定义 ====================

class CurrencyInfo(TypedDict):
    """货币信息结构"""
    code: str
    name: str
    name_cn: str
    symbol: str
    flag: str
    group: str


# ==================== 货币分组配置 ====================

CURRENCY_GROUPS = {
    "🌏 亚洲": ["JPY", "HKD", "TWD", "SGD", "KRW", "THB", "MYR", "IDR", "VND", "PHP", "INR"],
    "🌐 欧洲": ["EUR", "GBP", "CHF", "RUB", "TRY", "SEK", "NOK", "DKK", "PLN"],
    "🌎 美洲": ["USD", "CAD", "MXN", "BRL", "ARS"],
    "🌍 大洋洲": ["AUD", "NZD"],
    "🏜️ 中东": ["AED", "SAR", "ILS"],
    "🌍 非洲": ["ZAR", "EGP"]
}

# 所有货币汇总（用于 API 查询）
ALL_CURRENCIES = []
for currencies in CURRENCY_GROUPS.values():
    for c in currencies:
        if c not in ALL_CURRENCIES:
            ALL_CURRENCIES.append(c)

# ==================== 货币详细信息 ====================

CURRENCY_CONFIG: dict[str, CurrencyInfo] = {
    # ===== 亚洲 =====
    "JPY": {"code": "JPY", "name": "Japanese Yen", "name_cn": "日元", "symbol": "¥", "flag": "🇯🇵", "group": "🌏 亚洲"},
    "HKD": {"code": "HKD", "name": "Hong Kong Dollar", "name_cn": "港币", "symbol": "HK$", "flag": "🇭🇰", "group": "🌏 亚洲"},
    "TWD": {"code": "TWD", "name": "New Taiwan Dollar", "name_cn": "新台币", "symbol": "NT$", "flag": "🇹🇼", "group": "🌏 亚洲"},
    "SGD": {"code": "SGD", "name": "Singapore Dollar", "name_cn": "新加坡元", "symbol": "S$", "flag": "🇸🇬", "group": "🌏 亚洲"},
    "KRW": {"code": "KRW", "name": "South Korean Won", "name_cn": "韩元", "symbol": "₩", "flag": "🇰🇷", "group": "🌏 亚洲"},
    "THB": {"code": "THB", "name": "Thai Baht", "name_cn": "泰铢", "symbol": "฿", "flag": "🇹🇭", "group": "🌏 亚洲"},
    "MYR": {"code": "MYR", "name": "Malaysian Ringgit", "name_cn": "林吉特", "symbol": "RM", "flag": "🇲🇾", "group": "🌏 亚洲"},
    "IDR": {"code": "IDR", "name": "Indonesian Rupiah", "name_cn": "印尼盾", "symbol": "Rp", "flag": "🇮🇩", "group": "🌏 亚洲"},
    "VND": {"code": "VND", "name": "Vietnamese Dong", "name_cn": "越南盾", "symbol": "₫", "flag": "🇻🇳", "group": "🌏 亚洲"},
    "PHP": {"code": "PHP", "name": "Philippine Peso", "name_cn": "菲律宾比索", "symbol": "₱", "flag": "🇵🇭", "group": "🌏 亚洲"},
    "INR": {"code": "INR", "name": "Indian Rupee", "name_cn": "印度卢比", "symbol": "₹", "flag": "🇮🇳", "group": "🌏 亚洲"},
    
    # ===== 欧洲 =====
    "EUR": {"code": "EUR", "name": "Euro", "name_cn": "欧元", "symbol": "€", "flag": "🇪🇺", "group": "🌐 欧洲"},
    "GBP": {"code": "GBP", "name": "British Pound", "name_cn": "英镑", "symbol": "£", "flag": "🇬🇧", "group": "🌐 欧洲"},
    "CHF": {"code": "CHF", "name": "Swiss Franc", "name_cn": "瑞士法郎", "symbol": "Fr", "flag": "🇨🇭", "group": "🌐 欧洲"},
    "RUB": {"code": "RUB", "name": "Russian Ruble", "name_cn": "卢布", "symbol": "₽", "flag": "🇷🇺", "group": "🌐 欧洲"},
    "TRY": {"code": "TRY", "name": "Turkish Lira", "name_cn": "土耳其里拉", "symbol": "₺", "flag": "🇹🇷", "group": "🌐 欧洲"},
    "SEK": {"code": "SEK", "name": "Swedish Krona", "name_cn": "瑞典克朗", "symbol": "kr", "flag": "🇸🇪", "group": "🌐 欧洲"},
    "NOK": {"code": "NOK", "name": "Norwegian Krone", "name_cn": "挪威克朗", "symbol": "kr", "flag": "🇳🇴", "group": "🌐 欧洲"},
    "DKK": {"code": "DKK", "name": "Danish Krone", "name_cn": "丹麦克朗", "symbol": "kr", "flag": "🇩🇰", "group": "🌐 欧洲"},
    "PLN": {"code": "PLN", "name": "Polish Zloty", "name_cn": "兹罗提", "symbol": "zł", "flag": "🇵🇱", "group": "🌐 欧洲"},
    
    # ===== 美洲 =====
    "USD": {"code": "USD", "name": "US Dollar", "name_cn": "美元", "symbol": "$", "flag": "🇺🇸", "group": "🌎 美洲"},
    "CAD": {"code": "CAD", "name": "Canadian Dollar", "name_cn": "加元", "symbol": "C$", "flag": "🇨🇦", "group": "🌎 美洲"},
    "MXN": {"code": "MXN", "name": "Mexican Peso", "name_cn": "墨西哥比索", "symbol": "MX$", "flag": "🇲🇽", "group": "🌎 美洲"},
    "BRL": {"code": "BRL", "name": "Brazilian Real", "name_cn": "雷亚尔", "symbol": "R$", "flag": "🇧🇷", "group": "🌎 美洲"},
    "ARS": {"code": "ARS", "name": "Argentine Peso", "name_cn": "阿根廷比索", "symbol": "ARS$", "flag": "🇦🇷", "group": "🌎 美洲"},
    
    # ===== 大洋洲 =====
    "AUD": {"code": "AUD", "name": "Australian Dollar", "name_cn": "澳元", "symbol": "A$", "flag": "🇦🇺", "group": "🌍 大洋洲"},
    "NZD": {"code": "NZD", "name": "New Zealand Dollar", "name_cn": "新西兰元", "symbol": "NZ$", "flag": "🇳🇿", "group": "🌍 大洋洲"},
    
    # ===== 中东 =====
    "AED": {"code": "AED", "name": "UAE Dirham", "name_cn": "阿联酋迪拉姆", "symbol": "د.إ", "flag": "🇦🇪", "group": "🏜️ 中东"},
    "SAR": {"code": "SAR", "name": "Saudi Riyal", "name_cn": "沙特里亚尔", "symbol": "﷼", "flag": "🇸🇦", "group": "🏜️ 中东"},
    "ILS": {"code": "ILS", "name": "Israeli Shekel", "name_cn": "谢克尔", "symbol": "₪", "flag": "🇮🇱", "group": "🏜️ 中东"},
    
    # ===== 非洲 =====
    "ZAR": {"code": "ZAR", "name": "South African Rand", "name_cn": "南非兰特", "symbol": "R", "flag": "🇿🇦", "group": "🌍 非洲"},
    "EGP": {"code": "EGP", "name": "Egyptian Pound", "name_cn": "埃及镑", "symbol": "E£", "flag": "🇪🇬", "group": "🌍 非洲"},
}

# ==================== 快捷预设 ====================

CURRENCY_PRESETS = {
    "🔥 热门货币": ["USD", "EUR", "GBP", "JPY", "HKD"],
    "🌏 亚洲货币": ["JPY", "HKD", "KRW", "SGD", "THB", "TWD", "MYR"],
    "🌐 欧洲货币": ["EUR", "GBP", "CHF", "RUB", "TRY"],
    "🌎 美洲货币": ["USD", "CAD", "MXN", "BRL"],
    "🗺️ 全部货币": ALL_CURRENCIES,
}


def get_currency_info(code: str) -> CurrencyInfo | None:
    """获取货币配置信息"""
    return CURRENCY_CONFIG.get(code)


def get_currencies_by_group(group: str) -> list[str]:
    """按分组获取货币列表"""
    return CURRENCY_GROUPS.get(group, [])


def format_currency_display(code: str, rate: float, mode: str = "rmb_to_foreign") -> str:
    """
    格式化货币显示
    
    Args:
        code: 货币代码
        rate: 汇率（1 CNY = X 外币）
        mode: 显示模式
            - "rmb_to_foreign": 1 RMB = X 外币
            - "foreign_to_rmb": 1 外币 = X RMB
    
    Returns:
        格式化后的显示字符串
    """
    info = get_currency_info(code)
    if not info:
        return f"{code}: {rate:.4f}"
    
    if mode == "rmb_to_foreign":
        return f"1 CNY = {rate:.4f} {info['symbol']}"
    else:
        foreign_rate = 1 / rate if rate != 0 else 0
        return f"1 {info['symbol']} = {foreign_rate:.4f} CNY"