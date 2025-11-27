import logging

# Configure logger for this module
logger = logging.getLogger(__name__)

# Mock data moved to module level constant to avoid magic data inside function
MOCK_WEATHER_DATA = {
    "taipei": "Sunny, 25°C",
    "new york": "Cloudy, 15°C",
    "london": "Rainy, 10°C",
    "台北": "晴朗, 25°C",
    "紐約": "多雲, 15°C",
}

def get_weather(city: str) -> str:
    """
    Get weather information for a specific city.
    
    Args:
        city: The name of the city (e.g., 'Taipei', 'New York').
        
    Returns:
        A string describing the weather.
    """
    # [Fix] 使用 strip() 去除 LLM 可能產生的前後空白，並轉為小寫
    city_cleaned = city.strip().lower()
    
    result = MOCK_WEATHER_DATA.get(city_cleaned, "Unknown weather data")
    
    # Log 加上引號以便觀察是否有隱藏空白
    logger.info(f"Fetching weather for: '{city_cleaned}' (raw: '{city}') -> {result}")
    
    return f"The weather in {city.strip()} is {result}."
