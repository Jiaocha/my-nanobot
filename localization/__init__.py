import json
import os
from typing import Any, Dict, Optional


class LocalizationManager:
    """
    本地化管理器，负责加载和管理翻译文件
    """

    def __init__(self, localization_dir: str = "localization"):
        """
        初始化本地化管理器
        
        Args:
            localization_dir: 本地化文件夹路径
        """
        self.localization_dir = localization_dir
        self.translations: Dict[str, Dict[str, Any]] = {}
        self.current_language = "en"
        self.load_languages()
        self.load_translations()

    def load_languages(self):
        """
        加载语言配置文件
        """
        config_path = os.path.join(self.localization_dir, "config", "languages.json")
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                self.language_config = json.load(f)
        else:
            self.language_config = {
                "default_language": "en",
                "supported_languages": [
                    {"code": "en", "name": "English", "locale": "en-US"}
                ],
                "fallback_language": "en"
            }

    def load_translations(self):
        """
        加载所有翻译文件
        """
        translations_dir = os.path.join(self.localization_dir, "translations")
        if not os.path.exists(translations_dir):
            return

        for root, dirs, files in os.walk(translations_dir):
            for file in files:
                if file.endswith(".json"):
                    # 提取语言代码，例如 zh-CN.json -> zh-CN
                    lang_code = file.split(".")[0]
                    file_path = os.path.join(root, file)

                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            if lang_code not in self.translations:
                                self.translations[lang_code] = {}
                            # 合并翻译内容
                            self._merge_translations(self.translations[lang_code], json.load(f))
                    except Exception as e:
                        print(f"Error loading translation file {file_path}: {e}")

    def _merge_translations(self, target: Dict[str, Any], source: Dict[str, Any]):
        """
        合并翻译字典
        
        Args:
            target: 目标字典
            source: 源字典
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._merge_translations(target[key], value)
            else:
                target[key] = value

    def set_language(self, language_code: str):
        """
        设置当前语言
        
        Args:
            language_code: 语言代码，如 en, zh-CN 等
        """
        if language_code in self.translations:
            self.current_language = language_code
        else:
            print(f"Language {language_code} not found, falling back to {self.language_config['fallback_language']}")
            self.current_language = self.language_config['fallback_language']

    def get(self, key: str, default: Any = None, language: Optional[str] = None) -> Any:
        """
        获取翻译文本
        
        Args:
            key: 翻译键，支持点号分隔的路径，如 "agent.name"
            default: 默认值，如果未找到翻译
            language: 语言代码，默认为当前语言
        
        Returns:
            翻译后的文本或默认值
        """
        lang = language or self.current_language
        if lang not in self.translations:
            lang = self.language_config['fallback_language']

        # 解析键路径
        keys = key.split(".")
        value = self.translations.get(lang, {})

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def get_supported_languages(self) -> list:
        """
        获取支持的语言列表
        
        Returns:
            支持的语言列表
        """
        return self.language_config['supported_languages']

    def check_compatibility(self, project_version: str) -> bool:
        """
        检查翻译文件与项目版本的兼容性
        
        Args:
            project_version: 项目版本号
        
        Returns:
            是否兼容
        """
        # 这里可以实现版本兼容性检查逻辑
        # 例如检查翻译文件的版本标记与项目版本是否匹配
        return True

# 创建全局本地化管理器实例
localization_manager = LocalizationManager()

# 导出常用函数
def set_language(language_code: str):
    """
    设置当前语言
    """
    localization_manager.set_language(language_code)

def get_translation(key: str, default: Any = None, language: Optional[str] = None) -> Any:
    """
    获取翻译文本
    """
    return localization_manager.get(key, default, language)

def get_supported_languages() -> list:
    """
    获取支持的语言列表
    """
    return localization_manager.get_supported_languages()

def check_compatibility(project_version: str) -> bool:
    """
    检查翻译文件与项目版本的兼容性
    """
    return localization_manager.check_compatibility(project_version)
