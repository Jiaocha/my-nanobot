#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
版本兼容性检查脚本
用于在主项目更新时自动检测汉化文件的兼容性
"""

import json
import os
import sys
from typing import Dict, List, Tuple


class CompatibilityChecker:
    """
    兼容性检查器
    """

    def __init__(self, localization_dir: str = "localization"):
        """
        初始化兼容性检查器
        
        Args:
            localization_dir: 本地化文件夹路径
        """
        self.localization_dir = localization_dir
        self.translations_dir = os.path.join(localization_dir, "translations")
        self.config_dir = os.path.join(localization_dir, "config")

    def load_project_version(self) -> str:
        """
        加载项目版本号
        
        Returns:
            项目版本号
        """
        # 尝试从 pyproject.toml 或其他配置文件中读取版本号
        pyproject_path = os.path.join(os.path.dirname(self.localization_dir), "pyproject.toml")
        if os.path.exists(pyproject_path):
            with open(pyproject_path, "r", encoding="utf-8") as f:
                content = f.read()
                import re
                match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
                if match:
                    return match.group(1)

        # 默认为 1.0.0
        return "1.0.0"

    def load_translations(self) -> Dict[str, Dict]:
        """
        加载所有翻译文件
        
        Returns:
            翻译文件内容字典
        """
        translations = {}

        if not os.path.exists(self.translations_dir):
            return translations

        for root, dirs, files in os.walk(self.translations_dir):
            for file in files:
                if file.endswith(".json"):
                    lang_code = file.split(".")[0]
                    file_path = os.path.join(root, file)

                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            if lang_code not in translations:
                                translations[lang_code] = {}
                            # 合并翻译内容
                            self._merge_translations(translations[lang_code], json.load(f))
                    except Exception as e:
                        print(f"Error loading translation file {file_path}: {e}")

        return translations

    def _merge_translations(self, target: Dict, source: Dict):
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

    def check_missing_keys(self, base_lang: str = "en", check_lang: str = "zh-CN") -> List[str]:
        """
        检查翻译文件中缺失的键
        
        Args:
            base_lang: 基础语言，用于对比
            check_lang: 需要检查的语言
        
        Returns:
            缺失的键列表
        """
        translations = self.load_translations()
        missing_keys = []

        if base_lang not in translations:
            print(f"Base language {base_lang} not found")
            return missing_keys

        if check_lang not in translations:
            print(f"Check language {check_lang} not found")
            return missing_keys

        base_translations = translations[base_lang]
        check_translations = translations[check_lang]

        def _check_keys(base: Dict, check: Dict, prefix: str = ""):
            for key, value in base.items():
                full_key = f"{prefix}.{key}" if prefix else key

                if key not in check:
                    missing_keys.append(full_key)
                elif isinstance(value, dict):
                    if not isinstance(check.get(key), dict):
                        missing_keys.append(full_key)  # 类型不匹配
                    else:
                        _check_keys(value, check[key], full_key)

        _check_keys(base_translations, check_translations)
        return missing_keys

    def check_version_compatibility(self) -> Tuple[bool, str]:
        """
        检查版本兼容性
        
        Returns:
            (是否兼容, 兼容性信息)
        """
        project_version = self.load_project_version()

        # 检查翻译文件是否存在
        if not os.path.exists(self.translations_dir):
            return False, "Translations directory not found"

        # 检查语言配置文件
        languages_config = os.path.join(self.config_dir, "languages.json")
        if not os.path.exists(languages_config):
            return False, "Languages config file not found"

        # 检查缺失的翻译键
        missing_keys = self.check_missing_keys()
        if missing_keys:
            return False, f"Missing translation keys: {', '.join(missing_keys[:10])}{'...' if len(missing_keys) > 10 else ''}"

        return True, f"Compatibility check passed for version {project_version}"

    def run_check(self):
        """
        运行兼容性检查
        """
        print("Running compatibility check...")
        is_compatible, message = self.check_version_compatibility()

        if is_compatible:
            print(f"✅ {message}")
            return 0
        else:
            print(f"❌ {message}")
            return 1

if __name__ == "__main__":
    checker = CompatibilityChecker()
    sys.exit(checker.run_check())
