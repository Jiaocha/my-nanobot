#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全面汉化检查脚本
用于扫描项目中所有用户可见文本，生成汉化状态报告
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List


class LocalizationAuditor:
    """
    汉化审计器
    """

    def __init__(self, project_dir: str = ".", localization_dir: str = "localization"):
        """
        初始化汉化审计器
        
        Args:
            project_dir: 项目根目录
            localization_dir: 本地化文件夹路径
        """
        self.project_dir = Path(project_dir)
        self.localization_dir = Path(localization_dir)
        self.translations_dir = self.localization_dir / "translations"

        # 需要检查的文件模式
        self.file_patterns = ["*.py", "*.md", "*.json", "*.yaml", "*.yml"]

        # 排除的目录
        self.exclude_dirs = {
            "__pycache__", ".git", "node_modules", "venv", ".venv",
            "build", "dist", ".pytest_cache", ".mypy_cache"
        }

        # 已加载的翻译
        self.loaded_translations: Dict[str, Dict] = {}

        # 审计结果
        self.audit_results = {
            "scanned_files": 0,
            "user_visible_strings": [],
            "hardcoded_strings": [],
            "error_messages": [],
            "cli_texts": [],
            "template_texts": [],
            "already_localized": [],
            "needs_localization": [],
            "excluded_patterns": []
        }

    def load_existing_translations(self):
        """
        加载现有的翻译文件
        """
        if not self.translations_dir.exists():
            return

        for lang_file in self.translations_dir.rglob("*.json"):
            lang_code = lang_file.stem
            try:
                with open(lang_file, "r", encoding="utf-8") as f:
                    content = json.load(f)
                    self.loaded_translations[lang_code] = content
            except Exception as e:
                print(f"Error loading {lang_file}: {e}")

    def is_excluded(self, path: Path) -> bool:
        """
        检查路径是否应该被排除
        
        Args:
            path: 文件路径
        
        Returns:
            是否应该排除
        """
        for part in path.parts:
            if part in self.exclude_dirs or part.startswith("."):
                return True
        return False

    def extract_strings_from_file(self, file_path: Path) -> List[Dict]:
        """
        从文件中提取用户可见字符串
        
        Args:
            file_path: 文件路径
        
        Returns:
            提取的字符串列表
        """
        strings = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")
        except Exception:
            return strings

        # Python 文件中的字符串模式
        if file_path.suffix == ".py":
            # print() 语句中的字符串
            print_pattern = r'print\([\'"]([^\'"]+)[\'"]\)'
            for i, line in enumerate(lines, 1):
                matches = re.findall(print_pattern, line)
                for match in matches:
                    if len(match) > 3:  # 忽略太短的字符串
                        strings.append({
                            "file": str(file_path),
                            "line": i,
                            "content": match,
                            "type": "print",
                            "context": line.strip()
                        })

            # console.print() 语句
            console_pattern = r'console\.print\([\'"\[]([^\'"]+)[\'"]'
            for i, line in enumerate(lines, 1):
                matches = re.findall(console_pattern, line)
                for match in matches:
                    if len(match) > 3:
                        strings.append({
                            "file": str(file_path),
                            "line": i,
                            "content": match,
                            "type": "console",
                            "context": line.strip()
                        })

            # raise 语句中的错误信息
            raise_pattern = r'raise \w+\([\'"]([^\'"]+)[\'"]'
            for i, line in enumerate(lines, 1):
                matches = re.findall(raise_pattern, line)
                for match in matches:
                    strings.append({
                        "file": str(file_path),
                        "line": i,
                        "content": match,
                        "type": "error",
                        "context": line.strip()
                    })

            # logger 语句
            logger_pattern = r'logger\.(info|warning|error|debug)\([\'"]([^\'"]+)[\'"]'
            for i, line in enumerate(lines, 1):
                matches = re.findall(logger_pattern, line)
                for match in matches:
                    log_type, log_msg = match
                    if len(log_msg) > 3:
                        strings.append({
                            "file": str(file_path),
                            "line": i,
                            "content": log_msg,
                            "type": f"logger.{log_type}",
                            "context": line.strip()
                        })

            # return 语句中的字符串
            return_pattern = r'return [\'"]([^\'"]+)[\'"]'
            for i, line in enumerate(lines, 1):
                matches = re.findall(return_pattern, line)
                for match in matches:
                    if len(match) > 3 and not match.startswith("_"):
                        strings.append({
                            "file": str(file_path),
                            "line": i,
                            "content": match,
                            "type": "return",
                            "context": line.strip()
                        })

            # description 赋值
            desc_pattern = r'description\s*=\s*[\'"]([^\'"]+)[\'"]'
            for i, line in enumerate(lines, 1):
                matches = re.findall(desc_pattern, line)
                for match in matches:
                    if len(match) > 3:
                        strings.append({
                            "file": str(file_path),
                            "line": i,
                            "content": match,
                            "type": "description",
                            "context": line.strip()
                        })

        # Markdown 文件中的标题和列表
        elif file_path.suffix == ".md":
            for i, line in enumerate(lines, 1):
                # 标题
                if line.startswith("#"):
                    strings.append({
                        "file": str(file_path),
                        "line": i,
                        "content": line.lstrip("#").strip(),
                        "type": "markdown_heading",
                        "context": line.strip()
                    })
                # 列表项
                elif line.strip().startswith("- ") or re.match(r'^\d+\.', line.strip()):
                    strings.append({
                        "file": str(file_path),
                        "line": i,
                        "content": line.strip(),
                        "type": "markdown_list",
                        "context": line.strip()
                    })

        return strings

    def is_chinese(self, text: str) -> bool:
        """
        检查文本是否包含中文
        
        Args:
            text: 文本内容
        
        Returns:
            是否包含中文
        """
        chinese_pattern = re.compile(r'[\u4e00-\u9fff]')
        return bool(chinese_pattern.search(text))

    def is_user_visible(self, string_info: Dict) -> bool:
        """
        判断字符串是否对用户可见
        
        Args:
            string_info: 字符串信息
        
        Returns:
            是否对用户可见
        """
        # 排除日志信息（通常不直接显示给用户）
        if string_info["type"].startswith("logger"):
            return False

        # 排除内部返回值
        if string_info["type"] == "return":
            excluded_returns = ["call_", "exec", "photo", "voice", "audio", "document", "file"]
            for excluded in excluded_returns:
                if string_info["content"].startswith(excluded):
                    return False

        # 排除太短的字符串（可能是变量名等）
        if len(string_info["content"]) < 3:
            return False

        return True

    def scan_project(self):
        """
        扫描整个项目
        """
        print("Scanning project for user-visible strings...")

        # 加载现有翻译
        self.load_existing_translations()

        # 扫描 Python 和 Markdown 文件
        for pattern in ["**/*.py", "**/*.md"]:
            for file_path in self.project_dir.glob(pattern):
                if self.is_excluded(file_path):
                    continue

                # 排除 localization 目录本身
                if "localization" in str(file_path):
                    continue

                self.audit_results["scanned_files"] += 1
                strings = self.extract_strings_from_file(file_path)

                for string_info in strings:
                    if self.is_user_visible(string_info):
                        self.audit_results["user_visible_strings"].append(string_info)

                        # 分类
                        if string_info["type"] == "error":
                            self.audit_results["error_messages"].append(string_info)
                        elif string_info["type"] in ["console", "print"]:
                            self.audit_results["cli_texts"].append(string_info)
                        elif string_info["type"] in ["markdown_heading", "markdown_list"]:
                            self.audit_results["template_texts"].append(string_info)
                        else:
                            self.audit_results["hardcoded_strings"].append(string_info)

        print(f"Scanned {self.audit_results['scanned_files']} files")
        print(f"Found {len(self.audit_results['user_visible_strings'])} user-visible strings")

    def analyze_localization_status(self):
        """
        分析汉化状态
        """
        print("\nAnalyzing localization status...")

        for string_info in self.audit_results["user_visible_strings"]:
            # 检查是否已汉化
            if self.is_chinese(string_info["content"]):
                self.audit_results["already_localized"].append(string_info)
            else:
                self.audit_results["needs_localization"].append(string_info)

        print(f"Already localized: {len(self.audit_results['already_localized'])}")
        print(f"Needs localization: {len(self.audit_results['needs_localization'])}")

    def generate_report(self, output_file: str = "localization_audit_report.json"):
        """
        生成审计报告
        
        Args:
            output_file: 输出文件路径
        """
        report = {
            "summary": {
                "scanned_files": self.audit_results["scanned_files"],
                "total_user_visible_strings": len(self.audit_results["user_visible_strings"]),
                "already_localized": len(self.audit_results["already_localized"]),
                "needs_localization": len(self.audit_results["needs_localization"]),
                "localization_coverage": f"{len(self.audit_results['already_localized']) / max(1, len(self.audit_results['user_visible_strings'])) * 100:.1f}%"
            },
            "by_category": {
                "error_messages": len(self.audit_results["error_messages"]),
                "cli_texts": len(self.audit_results["cli_texts"]),
                "template_texts": len(self.audit_results["template_texts"]),
                "hardcoded_strings": len(self.audit_results["hardcoded_strings"])
            },
            "needs_localization": self.audit_results["needs_localization"],
            "already_localized": self.audit_results["already_localized"]
        }

        # 保存 JSON 报告
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\nReport saved to {output_file}")

        # 打印摘要
        self._print_summary(report)

        return report

    def _print_summary(self, report: Dict):
        """
        打印报告摘要
        
        Args:
            report: 报告内容
        """
        print("\n" + "=" * 60)
        print("汉化状态报告摘要")
        print("=" * 60)
        print(f"扫描文件数：{report['summary']['scanned_files']}")
        print(f"用户可见文本总数：{report['summary']['total_user_visible_strings']}")
        print(f"已汉化：{report['summary']['already_localized']}")
        print(f"待汉化：{report['summary']['needs_localization']}")
        print(f"汉化覆盖率：{report['summary']['localization_coverage']}")
        print("\n按类别分类:")
        print(f"  - 错误信息：{report['by_category']['error_messages']}")
        print(f"  - CLI 文本：{report['by_category']['cli_texts']}")
        print(f"  - 模板文本：{report['by_category']['template_texts']}")
        print(f"  - 硬编码字符串：{report['by_category']['hardcoded_strings']}")

        # 显示前 10 个待汉化的内容
        if report["needs_localization"]:
            print("\n待汉化内容示例 (前 10 个):")
            for i, item in enumerate(report["needs_localization"][:10], 1):
                print(f"  {i}. [{item['type']}] {item['file']}:{item['line']}")
                print(f"     内容：{item['content']}")

        print("=" * 60)

    def run_audit(self, output_file: str = "localization_audit_report.json"):
        """
        运行完整审计
        
        Args:
            output_file: 输出文件路径
        
        Returns:
            审计报告
        """
        self.scan_project()
        self.analyze_localization_status()
        return self.generate_report(output_file)

if __name__ == "__main__":
    auditor = LocalizationAuditor()
    report = auditor.run_audit()
    sys.exit(0 if report["summary"]["needs_localization"] == 0 else 1)
