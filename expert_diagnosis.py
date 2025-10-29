"""
专家诊断分析 - 使用 Expert Model 基于修改后的 prompt 进行深度分析
"""
import os
import re
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from openai import OpenAI

# 加载环境变量
load_dotenv()


class ExpertDiagnosisAnalyzer:
    """专家诊断分析器 - 使用 Expert Model 进行深度诊断分析"""
    
    def __init__(self):
        """初始化分析器"""
        # 从环境变量加载配置（使用 EXPERT_MODEL）
        self.api_key = os.getenv("EXPERT_MODEL_API_KEY")
        self.model_name = os.getenv("EXPERT_MODEL_MODEL_NAME")
        self.endpoint = os.getenv("EXPERT_MODEL_ENDPOINT")
        
        # 初始化 OpenAI 客户端
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.endpoint
        )
    
    def load_prompt_from_md(self, md_path: Path) -> str:
        """
        从 markdown 文件中提取 prompt
        
        Args:
            md_path: markdown 文件路径
            
        Returns:
            提取的 prompt 文本
        """
        if not md_path.exists():
            print(f"警告：文件不存在: {md_path}")
            return ""
        
        with open(md_path, 'r', encoding='utf-8') as f:
            return f.read()
        
        
    
    def analyze_with_expert(self, prompt: str) -> dict:
        """
        使用 Expert Model 进行专家级诊断分析
        
        Args:
            prompt: 输入的诊断 prompt
            
        Returns:
            分析结果字典
        """
        print("\n开始专家级诊断分析...")
        print("=" * 60)
        
        try:
            print(f"\n正在调用 {self.model_name} 进行深度分析...")
            
            response = self.client.responses.create(
                model=self.model_name,  # type: ignore
                input=prompt,
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
            print(f"专家诊断分析失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {}
    
    def save_to_markdown(self, result: dict, output_path: Path, original_prompt: str):
        """
        保存专家诊断结果为 Markdown 文件
        
        Args:
            result: 诊断结果
            output_path: 输出文件路径
            original_prompt: 原始 prompt
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 提取 reasoning 和 response 内容
        reasoning = result.get('reasoning', {})
        response = result.get('response', {})
        
        reasoning_type = reasoning.get('type', 'N/A')
        reasoning_content = reasoning.get('content', '')
        
        response_type = response.get('type', 'N/A')
        response_content = response.get('content', '')
        
        # 构建 Markdown 内容
        content = f"""# 专家诊断分析报告

**生成时间:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**使用模型:** {self.model_name}


{response_content}

---

*此报告由 Expert Model 生成，仅供医疗专业人员参考*
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"\n专家诊断报告已保存到: {output_path}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="使用 Expert Model 进行专家级诊断分析",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 使用默认路径进行专家诊断
  python expert_diagnosis.py
  
  # 指定输入的 prompt 文件
  python expert_diagnosis.py --input-prompt diagnosis_prompt.md
  
  # 指定输出文件
  python expert_diagnosis.py -o expert_diagnosis.md
        """
    )
    
    parser.add_argument(
        "--input-prompt",
        type=str,
        default="diagnosis_prompt.md",
        help="输入的 prompt markdown 文件路径（默认：diagnosis_prompt.md）"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="expert_diagnosis.md",
        help="输出 markdown 文件路径（默认：expert_diagnosis.md）"
    )
    
    args = parser.parse_args()
    
    # 确定项目根目录
    root_dir = Path(__file__).parent
    
    # 确定输入 prompt 文件路径
    input_prompt_path = Path(args.input_prompt)
    if not input_prompt_path.is_absolute():
        input_prompt_path = root_dir / input_prompt_path
    
    # 确定输出路径
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = root_dir / output_path
    
    # 创建分析器
    analyzer = ExpertDiagnosisAnalyzer()
    
    # 从 markdown 文件中加载 prompt
    prompt = analyzer.load_prompt_from_md(input_prompt_path)
    
    if not prompt:
        print("无法加载 prompt，分析终止")
        return
    
    # 进行专家诊断分析
    result = analyzer.analyze_with_expert(prompt)
    
    if not result:
        print("专家诊断分析失败")
        return
    
    # 保存结果
    analyzer.save_to_markdown(result, output_path, prompt)
    
    # 打印摘要
    print("\n" + "=" * 60)
    print("专家诊断分析摘要:")
    print(f"  输入文件: {input_prompt_path}")
    print(f"  输出文件: {output_path}")
    print(f"  推理类型: {result.get('reasoning', {}).get('type', 'N/A')}")
    print(f"  响应类型: {result.get('response', {}).get('type', 'N/A')}")
    print("=" * 60)
    
    # 打印诊断结论预览
    response_content = result.get('response', {}).get('content', '')
    if response_content:
        print("\n" + "=" * 60)
        print("专家诊断结论（前 500 字符预览）:")
        print("=" * 60)
        print(response_content[:500] + ("..." if len(response_content) > 500 else ""))
        print("=" * 60)


if __name__ == "__main__":
    main()

