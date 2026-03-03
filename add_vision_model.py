import json

config_path = r'C:\Users\Administrator\.nanobot\config.json'

with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

# 确保字段存在
if 'agents' not in config:
    config['agents'] = {}
if 'defaults' not in config['agents']:
    config['agents']['defaults'] = {}

# 添加 vision_model
config['agents']['defaults']['vision_model'] = 'openai/gpt-4o'

with open(config_path, 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

# 验证
with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)
    print('✅ vision_model:', config['agents']['defaults'].get('vision_model'))
    print('请重启网关：nanobot gateway')
