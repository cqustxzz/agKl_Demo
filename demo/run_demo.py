"""
运行演示：用多Agent代码审查器分析一段有问题的代码
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import json
from reviewer import ReviewOrchestrator


def main():
    print("=" * 60)
    print("  多Agent代码审查引擎 Demo")
    print("=" * 60)
    print()

    orchestrator = ReviewOrchestrator()

    # 审查示例文件
    filepath = "sample_bad_code.py"
    print(f"正在审查文件: {filepath}")
    print(f"启动 3 个审查Agent (Security / Performance / Style)...")
    print()

    result = orchestrator.review_file(filepath)

    # 打印概要
    print(f"审查完成！共发现 {result['total_issues']} 个问题:")
    print(f"  [CRITICAL] 严重: {result['critical']}")
    print(f"  [WARNING]  警告: {result['warning']}")
    print(f"  [INFO]     建议: {result['info']}")
    print()

    # 各Agent耗时
    print("各Agent执行情况:")
    for agent, stats in result["agents"].items():
        print(f"  {agent}: {stats['issues_found']} 个问题, 耗时 {stats['elapsed']}s")
    print()

    # 打印问题详情（前15个）
    print("-" * 60)
    print("问题详情 (按严重程度排序):")
    print("-" * 60)
    for i, issue in enumerate(result["issues"][:15], 1):
        print(f"\n{i}. [{issue['severity']}] {issue['rule']} (line {issue['line']})")
        print(f"   审查方: {issue['agent']}")
        print(f"   问题  : {issue['message']}")
        if issue["suggestion"]:
            print(f"   建议  : {issue['suggestion']}")

    if len(result["issues"]) > 15:
        print(f"\n... 还有 {len(result['issues']) - 15} 个问题未展示")

    # 保存完整报告
    report = orchestrator.generate_report(result)
    with open("review_report.md", "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n完整报告已保存到: review_report.md")

    # 保存JSON格式
    with open("review_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"结构化数据已保存到: review_result.json")


if __name__ == "__main__":
    main()
