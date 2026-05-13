"""
多Agent代码审查引擎 Demo
支持安全/性能/规范 三个Agent并行审查
"""
import ast
import re
import json
import os
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
from typing import Optional


class Severity(Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class Issue:
    agent: str
    severity: str
    line: int
    rule: str
    message: str
    suggestion: str = ""


@dataclass
class ReviewResult:
    agent_name: str
    issues: list = field(default_factory=list)
    elapsed: float = 0.0


# ==================== 安全审查Agent ====================
class SecurityAgent:
    """检测常见安全漏洞"""
    name = "SecurityAgent"

    RULES = [
        {
            "id": "SEC-001",
            "pattern": r"eval\s*\(",
            "severity": Severity.CRITICAL,
            "msg": "使用了eval()，可能导致代码注入",
            "fix": "改用ast.literal_eval()或json.loads()"
        },
        {
            "id": "SEC-002",
            "pattern": r"exec\s*\(",
            "severity": Severity.CRITICAL,
            "msg": "使用了exec()，存在任意代码执行风险",
            "fix": "移除exec调用，改用安全的替代方案"
        },
        {
            "id": "SEC-003",
            "pattern": r"subprocess\.call\(.*shell\s*=\s*True",
            "severity": Severity.CRITICAL,
            "msg": "subprocess使用shell=True，存在命令注入风险",
            "fix": "传入参数列表而非字符串，去掉shell=True"
        },
        {
            "id": "SEC-004",
            "pattern": r"os\.system\s*\(",
            "severity": Severity.CRITICAL,
            "msg": "使用os.system()执行命令，存在命令注入风险",
            "fix": "改用subprocess.run()并传入参数列表"
        },
        {
            "id": "SEC-005",
            "pattern": r"password\s*=\s*[\"'][^\"']+[\"']",
            "severity": Severity.CRITICAL,
            "msg": "检测到硬编码密码",
            "fix": "使用环境变量或配置文件存储敏感信息"
        },
        {
            "id": "SEC-006",
            "pattern": r"api_key\s*=\s*[\"'][^\"']+[\"']",
            "severity": Severity.CRITICAL,
            "msg": "检测到硬编码API密钥",
            "fix": "使用环境变量存储API密钥"
        },
        {
            "id": "SEC-007",
            "pattern": r"secret\s*=\s*[\"'][^\"']+[\"']",
            "severity": Severity.WARNING,
            "msg": "检测到硬编码secret",
            "fix": "使用环境变量或密钥管理服务"
        },
        {
            "id": "SEC-008",
            "pattern": r"pickle\.loads?\s*\(",
            "severity": Severity.WARNING,
            "msg": "使用pickle反序列化，可能导致远程代码执行",
            "fix": "改用json或安全的序列化方式"
        },
        {
            "id": "SEC-009",
            "pattern": r"hashlib\.md5\s*\(",
            "severity": Severity.INFO,
            "msg": "使用MD5哈希，该算法已不安全",
            "fix": "改用SHA-256或bcrypt"
        },
        {
            "id": "SEC-010",
            "pattern": r"verify\s*=\s*False",
            "severity": Severity.WARNING,
            "msg": "禁用了SSL证书验证，存在中间人攻击风险",
            "fix": "移除verify=False，或配置正确的CA证书"
        },
    ]

    def review(self, source: str, filename: str) -> ReviewResult:
        start = time.time()
        issues = []
        lines = source.split("\n")

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            for rule in self.RULES:
                if re.search(rule["pattern"], line):
                    issues.append(Issue(
                        agent=self.name,
                        severity=rule["severity"].value,
                        line=i,
                        rule=rule["id"],
                        message=rule["msg"],
                        suggestion=rule["fix"]
                    ))

        return ReviewResult(
            agent_name=self.name,
            issues=issues,
            elapsed=round(time.time() - start, 3)
        )


# ==================== 性能审查Agent ====================
class PerformanceAgent:
    """检测性能问题"""
    name = "PerformanceAgent"

    def review(self, source: str, filename: str) -> ReviewResult:
        start = time.time()
        issues = []
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return ReviewResult(agent_name=self.name, issues=[], elapsed=0)

        lines = source.split("\n")

        # 检测嵌套循环
        self._check_nested_loops(tree, lines, issues)

        # 检测超长函数
        self._check_long_functions(tree, lines, issues)

        # 检测频繁的字符串拼接
        self._check_string_concat(tree, lines, issues)

        # 检测全局变量在循环中被频繁访问
        self._check_global_in_loop(tree, lines, issues)

        return ReviewResult(
            agent_name=self.name,
            issues=issues,
            elapsed=round(time.time() - start, 3)
        )

    def _check_nested_loops(self, tree, lines, issues):
        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                for child in ast.walk(node):
                    if child is node:
                        continue
                    if isinstance(child, (ast.For, ast.While)):
                        issues.append(Issue(
                            agent=self.name,
                            severity=Severity.WARNING.value,
                            line=child.lineno,
                            rule="PERF-001",
                            message=f"检测到嵌套循环（外层第{node.lineno}行），可能导致O(n^2)复杂度",
                            suggestion="考虑使用字典/集合优化，或将内层逻辑提取为独立函数"
                        ))
                        break

    def _check_long_functions(self, tree, lines, issues):
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.end_lineno and (node.end_lineno - node.lineno) > 50:
                    issues.append(Issue(
                        agent=self.name,
                        severity=Severity.INFO.value,
                        line=node.lineno,
                        rule="PERF-002",
                        message=f"函数'{node.name}'长达{node.end_lineno - node.lineno}行，可读性和可维护性差",
                        suggestion="将大函数拆分为多个职责单一的小函数"
                    ))

    def _check_string_concat(self, tree, lines, issues):
        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                for child in ast.walk(node):
                    if isinstance(child, ast.AugAssign) and isinstance(child.op, ast.Add):
                        target = child.target
                        if isinstance(target, ast.Name):
                            issues.append(Issue(
                                agent=self.name,
                                severity=Severity.WARNING.value,
                                line=child.lineno,
                                rule="PERF-003",
                                message="循环内频繁字符串拼接，每次拼接都创建新字符串对象",
                                suggestion="改用列表收集字符串片段，循环外用''.join()合并"
                            ))

    def _check_global_in_loop(self, tree, lines, issues):
        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                for child in ast.walk(node):
                    if isinstance(child, ast.Global):
                        issues.append(Issue(
                            agent=self.name,
                            severity=Severity.INFO.value,
                            line=child.lineno,
                            rule="PERF-004",
                            message="循环中使用global变量，每次访问都有额外开销",
                            suggestion="将全局变量赋值给局部变量后再在循环中使用"
                        ))


# ==================== 代码规范审查Agent ====================
class StyleAgent:
    """检测代码规范问题"""
    name = "StyleAgent"

    def review(self, source: str, filename: str) -> ReviewResult:
        start = time.time()
        issues = []
        lines = source.split("\n")

        for i, line in enumerate(lines, 1):
            # 行长度
            if len(line) > 120:
                issues.append(Issue(
                    agent=self.name,
                    severity=Severity.INFO.value,
                    line=i,
                    rule="STYLE-001",
                    message=f"行长度{len(line)}超过120字符",
                    suggestion="拆分成多行或提取变量"
                ))

            # TODO/FIXME/HACK
            for tag in ["TODO", "FIXME", "HACK", "XXX"]:
                if tag in line.upper() and not line.strip().startswith("#"):
                    pass  # 注释里的TODO不管
                elif tag in line.upper() and line.strip().startswith("#"):
                    issues.append(Issue(
                        agent=self.name,
                        severity=Severity.INFO.value,
                        line=i,
                        rule="STYLE-002",
                        message=f"发现{tag}标记，可能有未完成的工作",
                        suggestion="在合并前处理或创建对应的issue跟踪"
                    ))

            # 检测魔法数字
            if re.search(r'\b(if|elif|while|return)\b.*\b\d{2,}\b', line):
                if not line.strip().startswith("#"):
                    match = re.search(r'\b(\d{2,})\b', line)
                    if match:
                        num = match.group(1)
                        if num not in ("100", "200", "404", "500", "1000", "1024"):
                            issues.append(Issue(
                                agent=self.name,
                                severity=Severity.INFO.value,
                                line=i,
                                rule="STYLE-003",
                                message=f"使用了魔法数字 {num}，降低代码可读性",
                                suggestion="提取为有意义的命名常量"
                            ))

        try:
            tree = ast.parse(source)
            # 检测过深的嵌套
            self._check_nesting_depth(tree, issues)
        except SyntaxError:
            pass

        return ReviewResult(
            agent_name=self.name,
            issues=issues,
            elapsed=round(time.time() - start, 3)
        )

    def _check_nesting_depth(self, tree, issues):
        def get_depth(node, depth=0):
            max_depth = depth
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                    child_depth = get_depth(child, depth + 1)
                    max_depth = max(max_depth, child_depth)
                else:
                    child_depth = get_depth(child, depth)
                    max_depth = max(max_depth, child_depth)
            return max_depth

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                depth = get_depth(node)
                if depth > 4:
                    issues.append(Issue(
                        agent=self.name,
                        severity=Severity.WARNING.value,
                        line=node.lineno,
                        rule="STYLE-004",
                        message=f"函数'{node.name}'嵌套深度达到{depth}层，代码难以阅读",
                        suggestion="使用早期返回（early return）减少嵌套，或提取子函数"
                    ))


# ==================== 编排引擎 ====================
class ReviewOrchestrator:
    """Agent编排引擎，负责调度多个审查Agent并行工作"""

    def __init__(self):
        self.agents = [
            SecurityAgent(),
            PerformanceAgent(),
            StyleAgent(),
        ]

    def review_file(self, filepath: str) -> dict:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()

        filename = os.path.basename(filepath)

        # 并行执行所有Agent
        results = []
        with ThreadPoolExecutor(max_workers=len(self.agents)) as executor:
            futures = {
                executor.submit(agent.review, source, filename): agent.name
                for agent in self.agents
            }
            for future in futures:
                results.append(future.result())

        # 汇总结果
        all_issues = []
        agent_stats = {}
        for r in results:
            all_issues.extend(r.issues)
            agent_stats[r.agent_name] = {
                "issues_found": len(r.issues),
                "elapsed": r.elapsed
            }

        # 按严重程度排序
        severity_order = {"CRITICAL": 0, "WARNING": 1, "INFO": 2}
        all_issues.sort(key=lambda x: severity_order.get(x.severity, 99))

        return {
            "file": filename,
            "total_issues": len(all_issues),
            "critical": sum(1 for i in all_issues if i.severity == "CRITICAL"),
            "warning": sum(1 for i in all_issues if i.severity == "WARNING"),
            "info": sum(1 for i in all_issues if i.severity == "INFO"),
            "agents": agent_stats,
            "issues": [asdict(i) for i in all_issues]
        }

    def generate_report(self, result: dict) -> str:
        """生成Markdown格式的审查报告"""
        lines = [
            f"# 代码审查报告",
            f"",
            f"**文件**: {result['file']}",
            f"**总问题数**: {result['total_issues']} "
            f"(严重: {result['critical']}, 警告: {result['warning']}, 建议: {result['info']})",
            f"",
            f"## Agent执行情况",
            f"",
        ]

        for agent_name, stats in result["agents"].items():
            lines.append(f"- **{agent_name}**: 发现 {stats['issues_found']} 个问题, 耗时 {stats['elapsed']}s")

        lines.append("")
        lines.append("## 问题详情")
        lines.append("")

        if not result["issues"]:
            lines.append("未发现问题，代码质量良好！")
        else:
            for i, issue in enumerate(result["issues"], 1):
                icon = {"CRITICAL": "🔴", "WARNING": "🟡", "INFO": "🔵"}.get(issue["severity"], "⚪")
                lines.append(f"### {i}. {icon} [{issue['severity']}] {issue['rule']}")
                lines.append(f"")
                lines.append(f"- **位置**: 第 {issue['line']} 行")
                lines.append(f"- **审查Agent**: {issue['agent']}")
                lines.append(f"- **问题**: {issue['message']}")
                if issue["suggestion"]:
                    lines.append(f"- **建议**: {issue['suggestion']}")
                lines.append("")

        return "\n".join(lines)
