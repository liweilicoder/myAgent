import re
from typing import Optional


def clean_llm_resp(text: str) -> Optional[str]:
    text = re.sub(r"<think>.*?</think>", "", text or "", flags=re.DOTALL | re.IGNORECASE)
    text = "\n".join(line for line in text.splitlines() if line.strip())
    return text