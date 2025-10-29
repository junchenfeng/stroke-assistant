#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将CT图像序列转换为MP4视频
"""

import cv2
import os
from pathlib import Path
import argparse
import re
from datetime import datetime


def create_video_from_images(image_folder, output_video, fps=10, fourcc_code='mp4v'):
    """
    从图像文件夹创建视频
    
    Args:
        image_folder: 包含JPEG图像的文件夹路径
        output_video: 输出视频文件路径
        fps: 视频帧率（默认10帧/秒）
        fourcc_code: 视频编码格式（默认'mp4v'）
    """
    # 获取所有jpg文件并按文件名排序
    image_folder_path = Path(image_folder)
    image_files = sorted(image_folder_path.glob('*.jpg'))
    
    if not image_files:
        print(f"错误：在 {image_folder} 中没有找到.jpg文件")
        return
    
    print(f"找到 {len(image_files)} 张图像")
    print(f"第一张: {image_files[0].name}")
    print(f"最后一张: {image_files[-1].name}")
    
    # 检测最常见的图像尺寸（排除可能的封面图）
    size_counts = {}
    sample_size = min(10, len(image_files))
    for img_file in image_files[:sample_size]:
        img = cv2.imread(str(img_file))
        if img is not None:
            size = (img.shape[1], img.shape[0])  # (width, height)
            size_counts[size] = size_counts.get(size, 0) + 1
    
    # 使用最常见的尺寸
    target_size = max(size_counts.items(), key=lambda x: x[1])[0]
    width, height = target_size
    print(f"使用图像尺寸: {width}x{height}")
    
    # 过滤掉尺寸不同的图像（如封面图）
    valid_images = []
    for img_file in image_files:
        img = cv2.imread(str(img_file))
        if img is not None and img.shape[1] == width and img.shape[0] == height:
            valid_images.append(img_file)
    
    if not valid_images:
        print("错误：没有找到符合尺寸的图像")
        return
    
    print(f"有效CT切片: {len(valid_images)} 张")
    image_files = valid_images
    
    # 创建视频写入器
    fourcc = cv2.VideoWriter_fourcc(*fourcc_code)
    video_writer = cv2.VideoWriter(output_video, fourcc, fps, (width, height))
    
    if not video_writer.isOpened():
        print("错误：无法创建视频写入器")
        return
    
    # 逐帧写入视频
    print(f"正在创建视频，帧率: {fps} fps...")
    for idx, image_file in enumerate(image_files, 1):
        img = cv2.imread(str(image_file))
        if img is None:
            print(f"警告：无法读取图像 {image_file}，跳过")
            continue
        
        video_writer.write(img)
        
        if idx % 10 == 0:
            print(f"已处理 {idx}/{len(image_files)} 张图像...")
    
    # 释放资源
    video_writer.release()
    print(f"\n视频创建成功！")
    print(f"输出文件: {output_video}")
    print(f"总帧数: {len(image_files)}")
    print(f"视频时长: {len(image_files)/fps:.2f} 秒")


def find_ct_folders(base_path='.'):
    """
    查找所有符合 CT_YYYY-MM-DD HH 格式的文件夹
    
    Args:
        base_path: 搜索的基础路径
        
    Returns:
        排序后的文件夹路径列表
    """
    base_path = Path(base_path)
    # 匹配 CT_YYYY-MM-DD HHAM/PM 格式
    ct_pattern = re.compile(r'^CT_\d{4}-\d{2}-\d{2}\s+\d{1,2}(AM|PM)$')
    
    ct_folders = []
    for item in base_path.iterdir():
        if item.is_dir() and ct_pattern.match(item.name):
            ct_folders.append(item)
    
    # 按名称排序
    ct_folders.sort(key=lambda x: x.name)
    return ct_folders


def generate_output_filename(folder_name):
    """
    根据文件夹名称生成输出视频文件名
    
    Args:
        folder_name: 文件夹名称 (如 'CT_2025-10-29 10AM')
        
    Returns:
        视频文件名 (如 'CT_2025-10-29_10AM.mp4')
    """
    # 将空格替换为下划线
    name = folder_name.replace(' ', '_')
    return f"{name}.mp4"


def main():
    parser = argparse.ArgumentParser(
        description='将CT图像序列转换为MP4视频',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                           # 处理所有CT文件夹
  %(prog)s -i "CT_2025-10-29 10AM"  # 处理指定文件夹
  %(prog)s --fps 15                  # 处理所有文件夹，使用15fps
        """
    )
    parser.add_argument(
        '--input',
        '-i',
        default=None,
        help='输入图像文件夹路径。如果不指定，将处理所有符合格式的CT文件夹'
    )
    parser.add_argument(
        '--output',
        '-o',
        default=None,
        help='输出视频文件路径。如果不指定，将根据文件夹名自动生成'
    )
    parser.add_argument(
        '--fps',
        '-f',
        type=int,
        default=10,
        help='视频帧率（默认: 10）'
    )
    parser.add_argument(
        '--base-path',
        default='.',
        help='搜索CT文件夹的基础路径（默认: 当前目录）'
    )
    
    args = parser.parse_args()
    
    # 如果指定了输入文件夹，只处理该文件夹
    if args.input:
        if not os.path.exists(args.input):
            print(f"错误：文件夹 '{args.input}' 不存在")
            return
        
        output = args.output if args.output else generate_output_filename(Path(args.input).name)
        print(f"\n{'='*60}")
        print(f"处理文件夹: {args.input}")
        print(f"输出视频: {output}")
        print(f"{'='*60}\n")
        create_video_from_images(args.input, output, args.fps)
    else:
        # 查找所有CT文件夹
        ct_folders = find_ct_folders(args.base_path)
        
        if not ct_folders:
            print(f"在 '{args.base_path}' 中没有找到符合格式的CT文件夹")
            print("文件夹格式应为: CT_YYYY-MM-DD HHAM/PM")
            return
        
        print(f"找到 {len(ct_folders)} 个CT文件夹:")
        for folder in ct_folders:
            print(f"  - {folder.name}")
        print()
        
        # 处理每个文件夹
        success_count = 0
        for idx, folder in enumerate(ct_folders, 1):
            output = generate_output_filename(folder.name)
            print(f"\n{'='*60}")
            print(f"[{idx}/{len(ct_folders)}] 处理文件夹: {folder.name}")
            print(f"输出视频: {output}")
            print(f"{'='*60}\n")
            
            try:
                create_video_from_images(str(folder), output, args.fps)
                success_count += 1
            except Exception as e:
                print(f"错误：处理 {folder.name} 时出错: {e}")
                continue
        
        print(f"\n{'='*60}")
        print(f"完成！成功处理 {success_count}/{len(ct_folders)} 个文件夹")
        print(f"{'='*60}")


if __name__ == '__main__':
    main()

