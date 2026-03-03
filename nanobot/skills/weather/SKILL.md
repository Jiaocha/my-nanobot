---
name: weather
description: 获取实时天气预报、空气质量和气象信息。
always: false
---

# 天气 (Weather)

你可以使用本地的 `weather_cn.py` 脚本来获取中国及全球城市的精准天气。

## 使用方法 (首选)

```bash
python weather_cn.py "城市名称"
```
*例如：`python weather_cn.py "惠州"` 或 `python weather_cn.py "北京"`。*

## 备选方案 (仅当脚本失效时)

如果本地脚本无法运行，可以使用 `curl`：
```bash
curl -s --connect-timeout 5 "wttr.in/城市名称?format=3&lang=zh"
```

## 注意事项
- 本地脚本支持中文城市名，返回的信息包括：城市位置、实时温度、体感温度、天气状况、风力风向、湿度以及 AQI 空气质量。
- 如果用户询问“明天”或“未来”天气，而脚本仅返回实时天气，请在回复中说明这是当前的实时观测数据。
