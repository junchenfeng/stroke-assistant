"""
整合测试记录 - 使用 GPT-5 将多个 JSON 文件整合为结构化 CSV
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


class TestRecordIntegrator:
    """测试记录整合器 - 使用 GPT-5 提取结构化数据"""
    
    def __init__(self):
        """初始化整合器"""
        # 从环境变量加载配置
        self.api_key = os.getenv("FAST_MODEL_API_KEY")
        self.model_name = os.getenv("FAST_MODEL_MODEL_NAME")
        self.endpoint = os.getenv("FAST_MODEL_ENDPOINT")
        
        # 初始化 Azure OpenAI 客户端
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.endpoint
        )
    
    def load_json_files(self, input_dir: Path) -> List[Dict[str, Any]]:
        """
        加载目录下所有 JSON 文件
        
        Args:
            input_dir: 输入目录路径
            
        Returns:
            JSON 数据列表
        """
        json_files = list(input_dir.glob("*.json"))
        
        if not json_files:
            print(f"警告：在 {input_dir} 中没有找到 JSON 文件")
            return []
        
        print(f"找到 {len(json_files)} 个 JSON 文件")
        
        records = []
        for json_file in sorted(json_files):
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                records.append(data)
        
        return records
    
    def build_prompt(self, records: List[Dict[str, Any]]) -> str:
        """
        构建整合提示词
        
        Args:
            records: 记录列表
            
        Returns:
            提示词字符串
        """
        # 构建包含所有记录内容的文本
        all_content = []
        
        for i, record in enumerate(records, 1):
            content_block = f"""
=== 报告 {i}: {record['filename']} ===
{record['content']}
"""
            all_content.append(content_block)
        
        combined_content = "\n".join(all_content)
        
        return combined_content
    
    def save_prompt(self, user_prompt: str, output_path: Path = None):
        """
        保存 prompt 到 markdown 文件
        
        Args:
            user_prompt: 用户提示词
            output_path: 输出路径（默认为 prompt.md）
        """
        if output_path is None:
            output_path = Path(__file__).parent / "prompt.md"
        
        content = f"""# 数据整合 Prompt


## input

```
{user_prompt}
```

---

**统计信息:**
- User Prompt 字符数: {len(user_prompt)}
- 总字符数: {+len(user_prompt)}
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"\nPrompt 已保存到: {output_path}")
        print(f"总字符数: { len(user_prompt)}")
    
    def integrate_records(self, records: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        使用 GPT-5 整合记录
        
        Args:
            records: 记录列表
            
        Returns:
            结构化数据列表
        """
        print("\n开始整合记录...")
        print("=" * 60)
        
        # 构建提示词
        content_text = self.build_prompt(records)
        
        
        user_prompt = f"""
        你是一个专业的医疗数据提取助手，专门从医疗检验报告中提取结构化数据。
请仔细分析所有的检验报告，提取每一个检验项目的详细数据。

输出要求：
1. 提取所有检验项目的数据
2. 每个检验项目单独成行
3. 严格按照指定的 JSON 格式返回
4. 确保数据的准确性
5. 如果某个字段没有信息，使用空字符串 ""

        请从以下医疗检验报告中提取所有检验项目的数据，按照指定格式整理成结构化数据。

{content_text}

请提取每个检验项目的以下信息：
- test_name: 检验项目名称（如"急诊血TNI"、"血气分析"等）
- test_time: 检验时间（格式：YYYY-MM-DD HH:MM:SS，如果只有日期则补00:00:00）
- item: 具体检测指标的中文名称（如"肌钙蛋白I定量"、"碱剩余"等）
- val: 结果值（只包含数值部分，如"<0.034"、"-12.13"）
- unit: 单位（如"ug/L"、"mmol/L"等）
- ref_range: 参考值范围（如"0-0.034"、"-1.0-3.0"等，如果有多个范围描述请取数值范围）

返回 JSON 格式：
{{
  "records": [
    {{
      "test_name": "检验项目名称",
      "test_time": "检验时间",
      "item": "检测指标",
      "val": "结果值",
      "unit": "单位",
      "ref_range": "参考范围"
    }}
  ]
}}

注意事项：
1. 每个具体的检测指标都要单独提取为一条记录
2. 如果报告中有多个检验项目，每个项目下的每个指标都要提取
3. 时间格式统一为 YYYY-MM-DD HH:MM:SS
4. 参考值如果有文字描述（如"阴性"、"阳性"），请也包含在 ref_range 中
5. 如果某个字段确实没有信息，使用空字符串 ""


"""
        
        # 保存 prompt 到文件
        self.save_prompt(user_prompt)
        
        try:
            print(f"\n正在调用 {self.model_name} 进行数据整合...")
            
            # 使用 Responses API
            response = self.client.responses.create(model=self.model_name,input=user_prompt,reasoning={"effort": "medium"})
            
            content = response.output[1].content[0].text # output 0 is reasoning
            
            if not content or content.strip() == "":
                print(f"警告：API 返回了空内容")
                print(f"Response 对象: {response}")
                return []
            
            # 解析 JSON
            result = json.loads(content)
            
            records_data = result.get("records", [])
            
            print(f"✓ 整合完成！提取了 {len(records_data)} 条记录")
            print("=" * 60)
            
            return records_data
            
        except Exception as e:
            print(f"整合失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def save_to_csv(self, records: List[Dict[str, str]], output_path: Path):
        """
        保存记录为 CSV 文件
        
        Args:
            records: 记录列表
            output_path: 输出文件路径
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # CSV 表头
        fieldnames = ['test_name', 'test_time', 'item', 'val', 'unit', 'ref_range']
        
        with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for record in records:
                # 确保所有字段都存在
                row = {field: record.get(field, '') for field in fieldnames}
                writer.writerow(row)
        
        print(f"\n结果已保存到: {output_path}")
        print(f"共 {len(records)} 条记录")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="整合测试记录为 CSV 表格",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 整合 data/record/test 目录下的所有 JSON
  python integrate_test_records.py
  
  # 指定输入目录
  python integrate_test_records.py --input-dir data/record/test
  
  # 指定输出文件
  python integrate_test_records.py -o output/integrated_records.csv
        """
    )
    
    parser.add_argument(
        "--input-dir",
        type=str,
        default="data/record/test",
        help="输入目录路径（默认：data/record/test）"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        help="输出 CSV 文件路径（默认：data/integrated_test_records.csv）"
    )
    
    args = parser.parse_args()
    
    # 确定项目根目录
    root_dir = Path(__file__).parent
    
    # 确定输入目录
    input_dir = Path(args.input_dir)
    if not input_dir.is_absolute():
        input_dir = root_dir / input_dir
    
    # 确定输出路径
    if args.output:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = root_dir / output_path
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = root_dir / "data" / f"integrated_test_records_{timestamp}.csv"
    
    # 创建整合器
    integrator = TestRecordIntegrator()
    
    # 加载 JSON 文件
    records = integrator.load_json_files(input_dir)
    
    if not records:
        print("没有找到可处理的记录")
        return
    
    # 整合记录
    integrated_data = integrator.integrate_records(records)
    
    if not integrated_data:
        print("整合失败，没有提取到数据")
        return
    
    # 保存为 CSV
    integrator.save_to_csv(integrated_data, output_path)
    
    # 打印摘要
    print("\n" + "=" * 60)
    print("整合摘要:")
    print(f"  输入文件数: {len(records)}")
    print(f"  提取记录数: {len(integrated_data)}")
    print(f"  输出文件: {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()

