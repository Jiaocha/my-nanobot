# 项目本地化（汉化）系统

## 📚 概述

本项目已建立完整的本地化系统，用于支持多语言界面，特别是中文汉化。该系统确保汉化内容与主项目代码完全分离，实现独立维护和更新。

## 🏗️ 目录结构

```
localization/
├── __init__.py                      # 本地化管理器模块
├── config/
│   └── languages.json               # 语言配置文件
├── scripts/
│   ├── check_compatibility.py       # 版本兼容性检查脚本
│   ├── check_translation_quality.py # 翻译质量检查脚本
│   └── full_localization_audit.py   # 全面汉化审计脚本
├── translations/
│   ├── zh-CN.json                   # 中文翻译主文件
│   └── agent/
│       ├── en.json                  # Agent 模块英文翻译
│       └── zh-CN.json               # Agent 模块中文翻译
├── docs/
│   ├── maintenance_guide.md         # 维护指南
│   ├── localization_audit_report.md # 汉化审计报告
│   ├── localization_implementation_plan.md  # 实施方案
│   └── README.md                    # 本文件
└── resources/                        # 资源文件（图像、音频等）
```

## 🚀 快速开始

### 1. 在代码中使用翻译

```python
from localization import get_translation, set_language

# 设置语言（默认为英语）
set_language('zh-CN')

# 获取翻译文本
text = get_translation('cli.error.no_api_key', 'Error: No API key configured.')
print(text)  # 输出：错误：未配置 API 密钥。

# 如果翻译不存在，返回默认值
text = get_translation('nonexistent.key', 'Default text')
print(text)  # 输出：Default text
```

### 2. 运行汉化检查

```bash
# 全面汉化审计
python localization/scripts/full_localization_audit.py

# 翻译质量检查
python localization/scripts/check_translation_quality.py

# 版本兼容性检查
python localization/scripts/check_compatibility.py
```

## 📊 当前汉化状态

根据最新的审计报告（2026-03-02）：

| 指标 | 数值 |
|------|------|
| 扫描文件数 | 90 |
| 用户可见文本 | 642 条 |
| 已汉化 | 4 条 (0.6%) |
| 待汉化 | 638 条 (99.4%) |

**详细报告**: 查看 [`docs/localization_audit_report.md`](docs/localization_audit_report.md)

## 🎯 汉化优先级

### P0 - 紧急（立即实施）
- ✅ CLI 命令行界面（64 条）
- ✅ 错误提示信息（8 条）
- ✅ Agent 工具描述（约 20 条）

### P1 - 高优先级（1-2 周）
- 通讯渠道消息（约 30 条）
- Provider 错误信息（约 10 条）
- Cron 服务消息（约 10 条）

### P2 - 中优先级（2-4 周）
- Markdown 模板文件（529 条）

### P3 - 低优先级（后续优化）
- 日志信息优化
- 动态生成内容

## 📝 翻译文件格式

### JSON 格式示例

```json
{
  "cli": {
    "error": {
      "no_api_key": "错误：未配置 API 密钥。",
      "npm_not_found": "未找到 npm。请安装 Node.js >= 18。"
    },
    "status": {
      "goodbye": "再见！",
      "bridge_ready": "✓ Bridge 已就绪"
    }
  },
  "agent": {
    "tools": {
      "cron": {
        "description": "安排提醒和重复性任务。操作：添加、列表、删除。",
        "error": {
          "message_required": "错误：添加操作需要提供消息内容"
        }
      }
    }
  }
}
```

### 命名规范

- **翻译键**: 使用点号分隔的层级结构，如 `cli.error.no_api_key`
- **文件命名**: `{模块}_{语言代码}.json`，如 `agent_zh-CN.json`
- **语言代码**: 遵循 ISO 639-1 标准，如 `en`（英语）、`zh-CN`（简体中文）

## 🛠️ 工具使用

### 1. 本地化管理器

提供以下主要函数：

- `set_language(language_code)`: 设置当前语言
- `get_translation(key, default, language)`: 获取翻译文本
- `get_supported_languages()`: 获取支持的语言列表
- `check_compatibility(project_version)`: 检查版本兼容性

### 2. 检查脚本

#### full_localization_audit.py
扫描整个项目，识别用户可见文本，生成汉化状态报告。

```bash
python localization/scripts/full_localization_audit.py
# 输出：localization_audit_report.json
```

#### check_translation_quality.py
检查翻译文件的格式正确性和完整性。

```bash
python localization/scripts/check_translation_quality.py
```

#### check_compatibility.py
检查汉化文件与主项目版本的兼容性。

```bash
python localization/scripts/check_compatibility.py
```

## 📖 文档说明

### 1. 维护指南 ([docs/maintenance_guide.md](docs/maintenance_guide.md))
详细的汉化文件维护指南，包括：
- 项目结构说明
- 命名规范
- 翻译范围界定
- 质量控制流程
- 版本更新兼容机制

### 2. 审计报告 ([docs/localization_audit_report.md](docs/localization_audit_report.md))
全面的汉化状态检查报告，包括：
- 各模块汉化状态
- 待汉化内容清单
- 重点汉化建议
- 实施计划

### 3. 实施方案 ([docs/localization_implementation_plan.md](docs/localization_implementation_plan.md))
详细的汉化实施方案，包括：
- 技术实施方案
- 渐进式改造步骤
- 质量保证措施
- 进度跟踪方法

## 🔧 代码改造示例

### 改造前

```python
console.print("[red]Error: No API key configured.[/red]")
```

### 改造后

```python
from localization import get_translation

console.print(f"[red]{get_translation('cli.error.no_api_key', 'Error: No API key configured.')}[/red]")
```

## 🧪 质量保证

### 自动化检查

所有翻译文件必须通过以下检查：

1. **格式检查**: JSON 格式正确
2. **完整性检查**: 所有键都有对应翻译
3. **兼容性检查**: 与主项目版本兼容

### 人工审核流程

1. **初译**: 翻译人员完成翻译
2. **校对**: 另一翻译人员校对
3. **测试**: 在实际环境中测试
4. **审核**: 项目负责人最终审核
5. **发布**: 合并到主分支

## 📈 进度跟踪

### 运行审计查看进度

```bash
python localization/scripts/full_localization_audit.py
```

### 查看覆盖率

```bash
cat localization_audit_report.json | jq '.summary.localization_coverage'
```

### 里程碑

| 阶段 | 目标 | 状态 |
|------|------|------|
| 第 1 周 | CLI 和错误信息完成 (15%) | ⏳ 待开始 |
| 第 2 周 | 渠道消息完成 (30%) | ⏳ 待开始 |
| 第 4 周 | 模板文档完成 (85%) | ⏳ 待开始 |
| 第 5 周 | 基本完成 (95%+) | ⏳ 待开始 |

## 🤝 贡献指南

### 如何贡献翻译

1. Fork 项目仓库
2. 选择要翻译的模块
3. 在对应的翻译文件中添加翻译
4. 运行质量检查脚本
5. 提交 Pull Request

### 翻译标准

- ✅ 准确传达原意
- ✅ 符合中文表达习惯
- ✅ 保持术语一致性
- ✅ 简洁明了
- ✅ 避免歧义

### 术语表

查看术语表确保翻译一致性。建议创建 `docs/glossary.md`。

## ⚠️ 注意事项

1. **保留技术术语**: URL、API 密钥、命令等保持原文
2. **格式保持**: Markdown 格式、颜色代码等保持不变
3. **向后兼容**: 确保翻译文件与主项目版本兼容
4. **定期更新**: 每次主项目更新后重新运行检查

## 📞 支持与反馈

### 问题反馈

1. 提交 Issue 到项目仓库
2. 标注为 `localization` 标签
3. 提供具体场景和截图

### 联系方式

- 查看项目 README.md
- 提交 GitHub Issue
- 联系项目维护人员

## 🔗 相关资源

- [维护指南](docs/maintenance_guide.md)
- [审计报告](docs/localization_audit_report.md)
- [实施方案](docs/localization_implementation_plan.md)
- [术语表](docs/glossary.md) (建议创建)

## 📄 许可证

与主项目许可证相同。

---

**最后更新**: 2026-03-02  
**维护者**: nanobot 团队