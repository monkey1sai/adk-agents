# [Refactor] 移除 Microsoft ADK 的依賴，使其成為框架無關的純函式
# from agents import function_tool <--- 移除這行
def get_weather(city: str) -> str:
    """
    Get weather information for a specific city.
    
    Args:
        city: The name of the city (e.g., 'Taipei', 'New York').
    """
    # 模擬資料
    weather_data = {
        "taipei": "Sunny, 25°C",
        "new york": "Cloudy, 15°C",
        "london": "Rainy, 10°C",
        "台北": "晴朗, 25°C",
        "紐約": "多雲, 15°C",
    }
    
    city_lower = city.lower()
    result = weather_data.get(city_lower, "Unknown weather data")
    print(f"\n[Tool] Fetching weather for: {city} -> {result}")
    return f"The weather in {city} is {result}."
