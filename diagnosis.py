"""
诊断分析 - 使用 Base Model 分析扫描报告和检验报告历史
"""
import os
import json
import csv
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from dotenv import load_dotenv
from openai import OpenAI

# 加载环境变量
load_dotenv()


class DiagnosisAnalyzer:
    """诊断分析器 - 使用 Base Model 进行病情分析"""
    
    def __init__(self):
        """初始化分析器"""
        # 从环境变量加载配置（使用 BASE_MODEL）
        self.api_key = os.getenv("BASE_MODEL_API_KEY")
        self.model_name = os.getenv("BASE_MODEL_MODEL_NAME")
        self.endpoint = os.getenv("BASE_MODEL_ENDPOINT")
        
        # 初始化 OpenAI 客户端
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.endpoint
        )
    
    def load_scan_reports(self, scan_dir: Path) -> List[Dict[str, Any]]:
        """
        加载扫描报告 JSON 文件
        
        Args:
            scan_dir: 扫描报告目录路径
            
        Returns:
            扫描报告列表
        """
        json_files = list(scan_dir.glob("*.json"))
        
        if not json_files:
            print(f"警告：在 {scan_dir} 中没有找到 JSON 文件")
            return []
        
        print(f"找到 {len(json_files)} 个扫描报告")
        
        reports = []
        for json_file in sorted(json_files):
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                reports.append(data)
        
        return reports
    
    def load_test_records_csv(self, csv_path: Path) -> str:
        """
        加载检验报告 CSV 文件并转换为文本
        
        Args:
            csv_path: CSV 文件路径
            
        Returns:
            格式化的检验报告文本
        """
        if not csv_path.exists():
            print(f"警告：CSV 文件不存在: {csv_path}")
            return ""
        
        records = []
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(row)
        
        print(f"加载了 {len(records)} 条检验记录")
        
        # 格式化为文本表格
        if not records:
            return ""
        
        # 构建文本表格
        lines = []
        lines.append("检验项目名称 | 检验时间 | 检测指标 | 结果值 | 单位 | 参考范围")
        lines.append("-" * 100)
        
        for record in records:
            line = f"{record.get('test_name', '')} | {record.get('test_time', '')} | {record.get('item', '')} | {record.get('val', '')} | {record.get('unit', '')} | {record.get('ref_range', '')}"
            lines.append(line)
        
        return "\n".join(lines)
    
    def build_diagnosis_prompt(
        self, 
        scan_reports: List[Dict[str, Any]], 
        test_records_text: str
    ) -> str:
        """
        构建诊断分析提示词
        
        Args:
            scan_reports: 扫描报告列表
            test_records_text: 检验报告文本
            
        Returns:
            提示词字符串
        """
        # 构建扫描报告部分
        scan_content_parts = []
        for i, report in enumerate(scan_reports, 1):
            part = f"""
=== 扫描报告 {i}: {report['filename']} ===
{report['content']}
"""
            scan_content_parts.append(part)
        
        scan_content = "\n".join(scan_content_parts)
        
        # 构建完整的提示词
        prompt = f"""你是一个心脑血管医生
你的病人做了一个三叉神经微血管减压术，导致小脑出血。

你的病人的CT内容是：

{scan_content}

你的病人的检验报告历史是：

{test_records_text}

请分析病人最新的疾病发展情况，给出理由，并分析潜在的风险点以及下一步高优的医疗措施。
"""
        
        return prompt
    
    def save_prompt(self, user_prompt: str, output_path: Path | None = None):
        """
        保存 prompt 到 markdown 文件
        
        Args:
            user_prompt: 用户提示词
            output_path: 输出路径（默认为 diagnosis_prompt.md）
        """
        if output_path is None:
            output_path = Path(__file__).parent / "diagnosis_prompt.md"  # type: ignore
        
        content = f"""# 诊断分析 Prompt

## input

```
{user_prompt}
```

---

**统计信息:**
- User Prompt 字符数: {len(user_prompt)}
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"\nPrompt 已保存到: {output_path}")
        print(f"总字符数: {len(user_prompt)}")
    
    def analyze_diagnosis(
        self, 
        scan_reports: List[Dict[str, Any]], 
        test_records_text: str
    ) -> Dict[str, Any]:
        """
        使用 Base Model 进行诊断分析
        
        Args:
            scan_reports: 扫描报告列表
            test_records_text: 检验报告文本
            
        Returns:
            分析结果
        """
        print("\n开始诊断分析...")
        print("=" * 60)
        
        # 构建提示词
        user_prompt = self.build_diagnosis_prompt(scan_reports, test_records_text)
        
        # 保存 prompt 到文件
        self.save_prompt(user_prompt)
        
        try:
            print(f"\n正在调用 {self.model_name} 进行诊断分析...")
            
            # 使用 Responses API，reasoning effort 设置为 high
            response = self.client.responses.create(
                model=self.model_name,  # type: ignore
                input=user_prompt,
                reasoning={"effort": "high"}
            )
            
            # 记录 output 中的 2 个元素
            # output[0] 是 reasoning，output[1] 是 response
            reasoning_content = ""
            response_content = ""
            
            # 安全地提取 reasoning 内容
            if len(response.output) > 0 and hasattr(response.output[0], 'content'):
                content_items = response.output[0].content  # type: ignore
                if content_items and len(content_items) > 0:
                    if hasattr(content_items[0], 'text'):
                        reasoning_content = content_items[0].text  # type: ignore
            
            # 安全地提取 response 内容
            if len(response.output) > 1 and hasattr(response.output[1], 'content'):
                content_items = response.output[1].content  # type: ignore
                if content_items and len(content_items) > 0:
                    if hasattr(content_items[0], 'text'):
                        response_content = content_items[0].text  # type: ignore
            
            result = {
                "reasoning": {
                    "type": response.output[0].type if len(response.output) > 0 else "",
                    "content": reasoning_content
                },
                "response": {
                    "type": response.output[1].type if len(response.output) > 1 else "",
                    "content": response_content
                }
            }
            
            print(f"✓ 诊断分析完成！")
            print("=" * 60)
            
            return result
            
        except Exception as e:
            print(f"诊断分析失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {}
    
    def save_diagnosis_result(self, result: Dict[str, Any], output_path: Path):
        """
        保存诊断结果为 JSON 文件
        
        Args:
            result: 诊断结果
            output_path: 输出文件路径
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n诊断结果已保存到: {output_path}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="基于扫描报告和检验报告历史进行诊断分析",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 使用默认路径进行诊断分析
  python diagnosis.py
  
  # 指定扫描报告目录
  python diagnosis.py --scan-dir data/record/scan
  
  # 指定检验报告 CSV
  python diagnosis.py --test-csv data/integrated_test_records_20251029_224600.csv
  
  # 指定输出文件
  python diagnosis.py -o output/diagnosis_result.json
        """
    )
    
    parser.add_argument(
        "--scan-dir",
        type=str,
        default="data/record/scan",
        help="扫描报告目录路径（默认：data/record/scan）"
    )
    parser.add_argument(
        "--test-csv",
        type=str,
        default="data/integrated_test_records_20251029_224600.csv",
        help="检验报告 CSV 文件路径（默认：data/integrated_test_records_20251029_224600.csv）"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        help="输出 JSON 文件路径（默认：data/diagnosis_result_TIMESTAMP.json）"
    )
    
    args = parser.parse_args()
    
    # 确定项目根目录
    root_dir = Path(__file__).parent
    
    # 确定扫描报告目录
    scan_dir = Path(args.scan_dir)
    if not scan_dir.is_absolute():
        scan_dir = root_dir / scan_dir
    
    # 确定检验报告 CSV 路径
    test_csv = Path(args.test_csv)
    if not test_csv.is_absolute():
        test_csv = root_dir / test_csv
    
    # 确定输出路径
    if args.output:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = root_dir / output_path
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = root_dir / "data" / f"diagnosis_result_{timestamp}.json"
    
    # 创建分析器
    analyzer = DiagnosisAnalyzer()
    
    # 加载扫描报告
    scan_reports = analyzer.load_scan_reports(scan_dir)
    
    if not scan_reports:
        print("没有找到扫描报告")
        return
    
    # 加载检验报告
    test_records_text = analyzer.load_test_records_csv(test_csv)
    
    if not test_records_text:
        print("警告：没有找到检验报告数据，将仅使用扫描报告进行分析")
    
    # 进行诊断分析
    result = analyzer.analyze_diagnosis(scan_reports, test_records_text)
    
    if not result:
        print("诊断分析失败")
        return
    
    # 保存结果
    analyzer.save_diagnosis_result(result, output_path)
    
    # 打印摘要
    print("\n" + "=" * 60)
    print("诊断分析摘要:")
    print(f"  扫描报告数: {len(scan_reports)}")
    print(f"  检验记录数: {len(test_records_text.splitlines()) - 2 if test_records_text else 0}")
    print(f"  输出文件: {output_path}")
    print("\n推理类型:", result.get("reasoning", {}).get("type", "N/A"))
    print("响应类型:", result.get("response", {}).get("type", "N/A"))
    print("=" * 60)
    
    # 打印诊断结果（响应内容）
    print("\n" + "=" * 60)
    print("诊断结果:")
    print("=" * 60)
    print(result.get("response", {}).get("content", ""))
    print("=" * 60)


if __name__ == "__main__":
    main()

