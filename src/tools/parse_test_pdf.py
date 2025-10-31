"""
测试 PDF 解析工具 - 使用 markitdown 提取文本内容
"""
import json
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

try:
    from markitdown import MarkItDown
except ImportError:
    print("错误：未找到 markitdown 库")
    print("请安装: pip install markitdown[all]")
    sys.exit(1)


class TestPDFParser:
    """测试 PDF 解析器 - 使用 markitdown 提取文本内容"""
    
    def __init__(self):
        """初始化解析器"""
        self.markitdown = MarkItDown()
    
    def parse_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """
        解析 PDF 文件
        
        Args:
            pdf_path: PDF 文件路径
            
        Returns:
            包含解析结果的字典
        """
        print(f"\n开始解析 PDF: {pdf_path.name}")
        print("=" * 60)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"文件不存在: {pdf_path}")
        
        # 使用 markitdown 解析 PDF
        try:
            result = self.markitdown.convert(str(pdf_path))
            
            # 构建结果字典
            document = {
                "filename": pdf_path.name,
                "source_path": str(pdf_path),
                "parsed_at": datetime.now().isoformat(),
                "content": result.text_content,
                "metadata": {
                    "parser": "markitdown",
                    "file_size_bytes": pdf_path.stat().st_size,
                }
            }
            
            # 如果 markitdown 提供了额外的元数据，也包含进来
            if hasattr(result, 'metadata') and result.metadata:
                document["metadata"]["markitdown"] = result.metadata
            
            print(f"解析完成！提取文本长度: {len(result.text_content)} 字符")
            print("=" * 60)
            
            return document
            
        except Exception as e:
            print(f"解析失败: {str(e)}")
            raise
    
    def save_results(self, document: Dict[str, Any], output_path: Path):
        """
        保存解析结果为 JSON 文件
        
        Args:
            document: 文档字典
            output_path: 输出文件路径
        """
        # 创建输出目录
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 保存为 JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(document, f, ensure_ascii=False, indent=2)
        
        print(f"\n结果已保存到: {output_path}")


def parse_test_pdf(
    pdf_file: str,
    output_file: Optional[str] = None,
    verbose: bool = True
) -> Path:
    """
    解析测试 PDF 文件的便捷函数
    
    Args:
        pdf_file: PDF 文件名或路径（相对于 data/test）
        output_file: 输出文件路径（可选，默认为 data/record/test/<name>.json）
        verbose: 是否显示详细信息
        
    Returns:
        输出文件的路径
    """
    # 确定项目根目录
    root_dir = Path(__file__).parent
    
    # 确定输入文件路径
    pdf_path = Path(pdf_file)
    if not pdf_path.is_absolute():
        # 如果是相对路径，假设相对于 data/test
        pdf_path = root_dir / "data" / "test" / pdf_file
    
    if not pdf_path.exists():
        raise FileNotFoundError(f"文件不存在: {pdf_path}")
    
    # 确定输出路径
    if output_file:
        output_path = Path(output_file)
        if not output_path.is_absolute():
            output_path = root_dir / output_file
    else:
        # 默认输出到 data/record/test/<name>.json
        output_path = root_dir / "data" / "record" / "test" / f"{pdf_path.stem}.json"
    
    # 创建解析器并解析
    parser = TestPDFParser()
    document = parser.parse_pdf(pdf_path)
    parser.save_results(document, output_path)
    
    # 打印摘要
    if verbose:
        print("\n" + "=" * 60)
        print("解析摘要:")
        print(f"  文件名: {document['filename']}")
        print(f"  解析时间: {document['parsed_at']}")
        print(f"  文本长度: {len(document['content'])} 字符")
        print(f"  文件大小: {document['metadata']['file_size_bytes']:,} 字节")
        print(f"  输出文件: {output_path}")
        print("=" * 60)
    
    return output_path


def batch_parse_test_pdfs(
    input_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    skip_existing: bool = False
):
    """
    批量解析测试目录下的所有 PDF 文件
    
    Args:
        input_dir: 输入目录路径（默认：data/test）
        output_dir: 输出目录路径（默认：data/record/test）
        skip_existing: 是否跳过已存在的 JSON 文件
    """
    # 确定项目根目录
    root_dir = Path(__file__).parent
    
    # 确定输入目录
    if input_dir is None:
        input_dir = root_dir / "data" / "test"
    
    # 确定输出目录
    if output_dir is None:
        output_dir = root_dir / "data" / "record" / "test"
    
    # 确保输入目录存在
    if not input_dir.exists():
        print(f"错误：输入目录不存在 - {input_dir}")
        sys.exit(1)
    
    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 获取所有 PDF 文件
    pdf_files = list(input_dir.glob("*.pdf"))
    
    if not pdf_files:
        print(f"警告：在 {input_dir} 中没有找到 PDF 文件")
        return
    
    print(f"找到 {len(pdf_files)} 个 PDF 文件")
    print("=" * 60)
    
    # 创建解析器
    parser = TestPDFParser()
    
    # 解析统计
    success_count = 0
    fail_count = 0
    skip_count = 0
    
    # 逐个处理
    for i, pdf_file in enumerate(pdf_files, 1):
        # 确定输出路径
        output_path = output_dir / f"{pdf_file.stem}.json"
        
        # 检查是否跳过已存在的文件
        if skip_existing and output_path.exists():
            skip_count += 1
            print(f"\n[{i}/{len(pdf_files)}] ⊘ 跳过: {pdf_file.name} (已存在)")
            continue
        
        print(f"\n[{i}/{len(pdf_files)}] 处理: {pdf_file.name}")
        
        try:
            # 解析 PDF
            document = parser.parse_pdf(pdf_file)
            
            # 保存结果
            parser.save_results(document, output_path)
            
            # 统计
            success_count += 1
            
            print(f"✓ 成功: 提取 {len(document['content'])} 字符")
            
        except Exception as e:
            fail_count += 1
            print(f"✗ 失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # 打印总结
    print("\n" + "=" * 60)
    print("批量处理完成！")
    print(f"  总文件数: {len(pdf_files)}")
    print(f"  成功: {success_count}")
    print(f"  失败: {fail_count}")
    if skip_existing:
        print(f"  跳过: {skip_count}")
    print("=" * 60)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="解析测试 PDF 文件（使用 markitdown）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 解析单个文件（默认从 data/test 读取）
  python parse_test_pdf.py "251028JJJ00518.pdf"
  
  # 指定完整路径
  python parse_test_pdf.py /path/to/file.pdf
  
  # 指定输出路径
  python parse_test_pdf.py "251028JJJ00518.pdf" -o custom/output.json
  
  # 批量处理所有测试文档
  python parse_test_pdf.py --batch
  
  # 批量处理并跳过已存在的文件
  python parse_test_pdf.py --batch --skip-existing
        """
    )
    
    parser.add_argument(
        "pdf_file",
        type=str,
        nargs="?",
        help="PDF 文件名（相对于 data/test）或完整路径"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        help="输出 JSON 文件路径（默认：data/record/test/<name>.json）"
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="批量处理 data/test 目录下的所有 PDF"
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        help="批量处理时的输入目录（默认：data/test）"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        help="批量处理时的输出目录（默认：data/record/test）"
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="批量处理时跳过已存在的 JSON 文件"
    )
    
    args = parser.parse_args()
    
    # 批量处理模式
    if args.batch:
        input_dir = Path(args.input_dir) if args.input_dir else None
        output_dir = Path(args.output_dir) if args.output_dir else None
        
        batch_parse_test_pdfs(
            input_dir=input_dir,
            output_dir=output_dir,
            skip_existing=args.skip_existing
        )
        return
    
    # 单文件处理模式
    if not args.pdf_file:
        parser.error("请指定 PDF 文件或使用 --batch 进行批量处理")
    
    try:
        parse_test_pdf(
            pdf_file=args.pdf_file,
            output_file=args.output,
            verbose=True
        )
    except Exception as e:
        print(f"\n错误: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

