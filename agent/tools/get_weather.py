import requests
import agent.logger as log

def get_weather(city: str) -> str:
    """
    通过调用 wttr.in API 查询真实的天气信息。
    """
    log.info(f"查询城市天气: {city}")
    url = f"https://wttr.in/{city}?format=j1"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        current_condition = data['current_condition'][0]
        weather_desc = current_condition['weatherDesc'][0]['value']
        temp_c = current_condition['temp_C']

        result = f"{city}当前天气：{weather_desc}，气温{temp_c}摄氏度"
        log.info(result)
        return result

    except requests.exceptions.RequestException as e:
        log.warn(f"查询天气时遇到网络问题 - {e}")
        return f"错误：查询天气时遇到网络问题 - {e}"
    except (KeyError, IndexError) as e:
        log.warn(f"解析天气数据失败 - {e}")
        return f"错误：解析天气数据失败，可能是城市名称无效 - {e}"
