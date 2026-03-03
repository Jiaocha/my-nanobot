import asyncio
import sys

import httpx


async def get_weather_monthly(city_name: str):
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            # 1. 搜索经纬度
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=1&language=zh"
            geo_res = await client.get(geo_url)
            geo_data = geo_res.json()

            if not geo_data.get("results"):
                return f"未找到城市坐标: {city_name}"

            loc = geo_data["results"][0]
            lat, lon = loc["latitude"], loc["longitude"]
            display_name = f"{loc.get('admin1', '')} {loc.get('name', '')}"

            # 2. 获取 16 天预报 (这是免 Key API 的极限跨度)
            weather_url = (
                f"https://api.open-meteo.com/v1/forecast?"
                f"latitude={lat}&longitude={lon}&"
                f"current_weather=true&"
                f"daily=temperature_2m_max,temperature_2m_min,weathercode&"
                f"timezone=auto&forecast_days=16"
            )
            w_res = await client.get(weather_url)
            w_data = w_res.json()

            current = w_data["current_weather"]
            daily = w_data["daily"]

            def get_status(code):
                codes = {0: "☀️ 晴朗", 1: "🌤️ 大部晴朗", 2: "⛅ 多云", 3: "☁️ 阴", 45: "🌫️ 雾", 48: "🌫️ 霾",
                         51: "🌧️ 毛毛雨", 61: "🌧️ 小雨", 71: "❄️ 小雪", 80: "🌦️ 阵雨", 95: "⛈️ 雷阵雨"}
                return codes.get(code, "☁️ 多云/阴")

            # 3. 数据分析
            temps_max = daily['temperature_2m_max']
            temps_min = daily['temperature_2m_min']
            avg_max = sum(temps_max) / len(temps_max)
            avg_min = sum(temps_min) / len(temps_min)

            # 4. 构建结构化输出
            output = [
                f"📍 城市: {display_name}",
                f"--- 当前实时: {current['temperature']}°C / {get_status(current['weathercode'])} ---",
                f"📊 16日趋势：平均 {avg_min:.1f}°C ~ {avg_max:.1f}°C",
                "未来 16 天详细预报（气象局提示：超过10天数据仅供参考）："
            ]

            for i in range(16):
                date_str = daily['time'][i]
                t_min = daily['temperature_2m_min'][i]
                t_max = daily['temperature_2m_max'][i]
                status = get_status(daily['weathercode'][i])

                # 每 7 天加一个分割线，增加可读性
                if i > 0 and i % 7 == 0:
                    output.append("----------------------------")

                label = "今天" if i == 0 else "明天" if i == 1 else "后天" if i == 2 else date_str[5:]
                output.append(f"📅 {label: <5} | {status} | {t_min: >4}°C ~ {t_max: <4}°C")

            output.append("\n数据来源: Open-Meteo (GitHub Open Source)")
            return "\n".join(output)

        except Exception as e:
            return f"查询出错: {str(e)}"

if __name__ == "__main__":
    city = sys.argv[1] if len(sys.argv) > 1 else "惠州"
    print(asyncio.run(get_weather_monthly(city)))
