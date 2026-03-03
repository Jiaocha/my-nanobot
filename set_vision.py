import json

config_path = r'C:\Users\Administrator\.nanobot\config.json'

with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

# custom provider 直接用模型名，不需要前缀
config['agents']['defaults']['vision_model'] = 'vision_model'

with open(config_path, 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)
    print('✅ vision_model:', config['agents']['defaults']['vision_model'])
    print('请重启网关：nanobot gateway')
