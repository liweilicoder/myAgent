AGENT_COLORS = {
    "ProductManager": "\033[94m",
    "Engineer": "\033[92m",
    "CodeReviewer": "\033[93m",
    "UserProxy": "\033[96m",
    "User": "\033[97m",
}
COLOR_RESET = "\033[0m"


async def print_message(message):
    """按 Agent 类型着色打印消息"""
    source = getattr(message, 'source', None) or message.__class__.__name__
    color = AGENT_COLORS.get(source, "")
    content = message.to_text() if hasattr(message, 'to_text') else str(getattr(message, 'content', ''))
    print(f"{color}{'='*60}\n{source}\n{content}{COLOR_RESET}\n")