# 项目结构

```
stroke-assistant/
├── data/                    # 存放各类原始数据
│   ├── scan/               # 各类 CT/MRI 的原始数据
│   │   ├── image/         # CT 影像
│   │   ├── document/      # 诊断文件
│   │   └── video/         # CT 视频
│   ├── test/              # 各类检验报告的原始数据（PDF）
│   ├── record/            # 经过数据提取的中间产出（JSON/MD 格式）
│   │   ├── scan/         # 影像检查记录
│   │   └── test/         # 检验报告记录
│   ├── database/          # 可用于后续诊断分析的清洗后数据（CSV 格式）
│   └── diagnosis/         # 每日诊断结果存储
│
├── src/                    # 代码项目
│   ├── tools/             # 各类工具，未来成为 agent 的 tools
│   └── agents/            # 目前是脚本，未来会成为 agent 流程
│
├── diagnosis.py           # 诊断主程序
├── expert_diagnosis.py    # 专家诊断程序
├── pyproject.toml         # 项目依赖配置
├── poetry.lock            # 依赖锁定文件
└── README.md              # 项目说明文档
```

## 目录说明

### 1. data 文件夹
存放各类原始数据和处理结果：

- **scan/**: 各类 CT/MRI 的原始数据
  - `image/`: CT 影像文件
  - `document/`: 诊断文件（PDF）
  - `video/`: CT 视频文件

- **test/**: 各类检验报告的原始数据（PDF 格式）

- **record/**: 经过数据提取的中间产出，一般是 JSON 或 MD 格式
  - `scan/`: 从影像诊断文件中提取的结构化数据
  - `test/`: 从检验报告中提取的结构化数据

- **database/**: 可用于后续诊断分析的清洗后数据，目前以 CSV 形式存储

- **diagnosis/**: 每日诊断结果存储，按日期组织

### 2. src 代码项目

- **tools/**: 各类工具函数和脚本，未来将成为 agent 的 tools
  - `parse_test_pdf.py`: 解析检验报告 PDF
  - `parse_scan_pdf.py`: 解析影像检查 PDF
  - `integrate_test_records.py`: 整合检验记录
  - `create_video.py`: 创建视频工具

- **agents/**: 目前是脚本，未来会成为 agent 流程

