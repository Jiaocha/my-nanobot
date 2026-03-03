#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
翻译质量检查脚本
用于验证翻译文件的格式正确性和完整性
"""

import json
import os
import sys
from typing import List, Tuple


class TranslationQualityChecker:
    """
    翻译质量检查器
    """

    def __init__(self, localization_dir: str = "localization"):
        """
        初始化翻译质量检查器
        
        Args:
            localization_dir: 本地化文件夹路径
        """
        self.localization_dir = localization_dir
        self.translations_dir = os.path.join(localization_dir, "translations")

    def check_file_format(self, file_path: str) -> Tuple[bool, str]:
        """
        检查翻译文件格式
        
        Args:
            file_path: 翻译文件路径
        
        Returns:
            (是否有效, 错误信息)
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = json.load(f)

            # 检查是否为字典格式
            if not isinstance(content, dict):
                return False, "Translation file must be a JSON object"

            return True, "File format is valid"
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON format: {str(e)}"
        except Exception as e:
            return False, f"Error reading file: {str(e)}"

    def check_translation_files(self) -> List[Tuple[str, bool, str]]:
        """
        检查所有翻译文件
        
        Returns:
            检查结果列表，每个元素为 (文件路径, 是否有效, 错误信息)
        """
        results = []

        if not os.path.exists(self.translations_dir):
            results.append((self.translations_dir, False, "Translations directory not found"))
            return results

        for root, dirs, files in os.walk(self.translations_dir):
            for file in files:
                if file.endswith(".json"):
                    file_path = os.path.join(root, file)
                    is_valid, message = self.check_file_format(file_path)
                    results.append((file_path, is_valid, message))

        return results

    def check_terminology_consistency(self, base_lang: str = "en", check_lang: str = "zh-CN") -> List[Tuple[str, str, str]]:
        """
        检查术语一致性
        
        Args:
            base_lang: 基础语言
            check_lang: 检查语言
        
        Returns:
            术语一致性问题列表
        """
        # 这里可以实现术语一致性检查逻辑
        # 例如检查特定术语的翻译是否一致
        return []

    def run_check(self):
        """
        运行翻译质量检查
        """
        print("Running translation quality check...")

        # 检查翻译文件格式
        file_results = self.check_translation_files()

        valid_files = 0
        invalid_files = 0

        for file_path, is_valid, message in file_results:
            if is_valid:
                print(f"✅ {file_path}: {message}")
                valid_files += 1
            else:
                print(f"❌ {file_path}: {message}")
                invalid_files += 1

        # 检查术语一致性
        terminology_issues = self.check_terminology_consistency()
        if terminology_issues:
            print("\nTerminology consistency issues:")
            for term, base_translation, check_translation in terminology_issues:
                print(f"  - Term '{term}': {base_translation} -> {check_translation}")

        print("\nQuality check completed:")
        print(f"  Valid files: {valid_files}")
        print(f"  Invalid files: {invalid_files}")
        print(f"  Terminology issues: {len(terminology_issues)}")

        if invalid_files > 0 or len(terminology_issues) > 0:
            return 1
        else:
            return 0

if __name__ == "__main__":
    checker = TranslationQualityChecker()
    sys.exit(checker.run_check())
