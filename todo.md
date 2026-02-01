# Depth Anything 3 二次开发记录

**更新时间：** 2026-01-31

---

## 修复的问题

### 1. 包结构问题

**问题描述：**
- 缺少 `depth_anything_3/__init__.py` 文件，导致 Python 无法识别为包
- 执行 `da3` 命令时报错：`ModuleNotFoundError: No module named 'depth_anything_3'`

**解决方案：**
- 创建 `depth_anything_3/__init__.py` 文件
- 添加基本的包信息（版本号等）

**文件位置：** `depth_anything_3/__init__.py`

---

### 2. 可编辑安装失败

**问题描述：**
- `pip install -e .` 后包无法正常导入
- `.pth` 文件为空，editable install 未正确配置

**根本原因：**
- `pyproject.toml` 中的包路径配置错误
- 配置为 `src/depth_anything_3`，但实际包在 `depth_anything_3`

**解决方案：**
```toml
# 修改前
[tool.hatch.build.targets.wheel]
packages = ["src/depth_anything_3"]

# 修改后
[tool.hatch.build.targets.wheel]
packages = ["depth_anything_3"]
```

**文件位置：** `pyproject.toml`

---

### 3. Gradio 6.4.0 兼容性问题

**问题描述：**
- 启动 Gradio 应用时报错：`Gallery.__init__() got an unexpected keyword argument 'show_download_button'`
- Gradio 6.4.0 版本不支持 `show_download_button` 参数

**解决方案：**
- 从 `gr.Gallery()` 组件中移除 `show_download_button=True` 参数
- 该参数在新版本中已被移除或改名

**文件位置：** `depth_anything_3/app/modules/ui_components.py:59`

**修改内容：**
```python
# 修改前
image_gallery = gr.Gallery(
    label="Preview",
    columns=4,
    height="300px",
    show_download_button=True,  # 移除此行
    object_fit="contain",
    preview=True,
    interactive=False,
)

# 修改后
image_gallery = gr.Gallery(
    label="Preview",
    columns=4,
    height="300px",
    object_fit="contain",
    preview=True,
    interactive=False,
)
```

---

## 优化改进

### 1. 本地模型配置

**优化目标：**
- 避免每次运行都从 Hugging Face Hub 下载模型
- 提高启动速度和离线可用性

**实现方案：**
- 修改 `DEFAULT_MODEL` 常量，指向本地 `models/` 目录
- 使用绝对路径确保在任何工作目录下都能找到模型

**配置位置：** `depth_anything_3/utils/constants.py`

**修改内容：**
```python
# 修改前
DEFAULT_MODEL = "depth-anything/DA3NESTED-GIANT-LARGE"

# 修改后
import os
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_MODEL = os.path.join(PROJECT_ROOT, "models/da3nested-giant-large-1.1")
```

**本地模型列表：**
- `models/da3nested-giant-large-1.1/` (默认，6.3GB)
- `models/da3-giant-1.1/` (6.3GB)
- `models/da3-large/`

---

### 2. 时间戳输出目录

**优化目标：**
- 防止多次运行时输出文件相互覆盖
- 便于追踪和管理不同批次的输出结果

**实现方案：**
- 添加 `get_timestamped_output_dir()` 函数
- 自动生成格式为 `outputs/outputs_YYYYMMDDHHMMSS` 的目录

**配置位置：** `depth_anything_3/utils/constants.py`

**修改内容：**
```python
from datetime import datetime

def get_timestamped_output_dir():
    """生成带时间戳的输出目录路径"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return os.path.join(PROJECT_ROOT, f"outputs/outputs_{timestamp}")

DEFAULT_EXPORT_DIR = get_timestamped_output_dir()
```

**输出示例：**
- `outputs/outputs_20260131173421/`
- `outputs/outputs_20260131173422/`

---

### 3. 启动脚本优化

**新增功能：** `start_app.sh`

**功能特性：**
1. **端口冲突自动处理**
   - 检测端口 7860 是否被占用
   - 自动终止占用端口的进程
   - 等待 2 秒确保端口释放

2. **GPU 内存清理**
   - 检查 GPU 使用情况
   - 提示当前 GPU 进程信息
   - 为应用启动准备干净的 GPU 环境

3. **环境变量配置**
   - `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` - 优化 GPU 内存分配
   - `HF_ENDPOINT=http://hf.x-gpu.com` - 加速 Hugging Face 下载

4. **友好的用户提示**
   - 显示启动状态
   - 提供访问地址
   - 清晰的错误提示

**使用方法：**
```bash
./start_app.sh
```

**脚本位置：** `start_app.sh`

---

## 新增文档

### 1. CLAUDE.md

**用途：** 为 Claude Code AI 助手提供项目上下文和指导

**内容包括：**
- 项目概述和架构说明
- 安装和配置指南
- CLI 命令参考
- 代码结构说明
- 常见问题和解决方案
- 开发规范

**文件位置：** `CLAUDE.md`

---

## 开发经验总结

### 1. Python 包结构规范

**经验：**
- 即使使用 `pyproject.toml` 和现代构建工具，`__init__.py` 仍然是必需的
- 包路径配置必须与实际目录结构完全匹配
- 使用 `pip install -e .` 后，检查 `.pth` 文件内容确认安装正确

**检查方法：**
```bash
# 检查包是否可导入
python -c "import depth_anything_3; print(depth_anything_3.__file__)"

# 检查 .pth 文件
cat /path/to/site-packages/_depth_anything_3.pth
```

---

### 2. Gradio 版本兼容性

**经验：**
- Gradio 更新频繁，API 变化较大
- 不同版本的组件参数可能不兼容
- 建议在 `requirements.txt` 中固定 Gradio 版本

**调试方法：**
```python
# 测试组件参数是否支持
import gradio as gr
gallery = gr.Gallery(label='Test', columns=4)  # 逐步添加参数测试
```

**版本信息：**
- 当前使用：Gradio 6.4.0
- 已知问题：`show_download_button` 参数不支持

---

### 3. 模型路径管理

**经验：**
- 使用绝对路径避免工作目录变化导致的问题
- 通过 `__file__` 获取项目根目录
- 模型文件可以使用符号链接节省空间

**最佳实践：**
```python
# 获取项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 构建模型路径
model_path = os.path.join(PROJECT_ROOT, "models/model_name")
```

---

### 4. 端口管理和进程控制

**经验：**
- 开发环境中经常遇到端口被占用的问题
- 使用 `lsof -ti:PORT` 查找占用端口的进程
- `kill -9` 强制终止进程，但要等待端口完全释放（2秒）

**脚本示例：**
```bash
# 检查端口
lsof -ti:7860

# 终止进程
kill -9 $(lsof -ti:7860)

# 等待端口释放
sleep 2
```

---

### 5. GPU 内存管理

**经验：**
- 48GB VRAM 对于大模型推理足够
- 设置 `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` 优化内存分配
- 多个进程共享 GPU 时注意内存竞争

**监控命令：**
```bash
# 查看 GPU 使用情况
nvidia-smi

# 查看使用 GPU 的进程
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv
```

---

## 待优化项目

### 高优先级

- [ ] 添加自动化测试（单元测试、集成测试）
- [ ] 优化大批量图像处理的内存使用
- [ ] 添加进度条显示（长时间处理任务）
- [ ] 实现模型热加载（避免重启应用）

### 中优先级

- [ ] 支持更多输出格式（FBX, OBJ 等）
- [ ] 添加批处理队列系统
- [ ] 实现结果缓存机制
- [ ] 优化 Gradio 界面布局和交互

### 低优先级

- [ ] 添加 API 文档（Swagger/OpenAPI）
- [ ] 实现用户认证和权限管理
- [ ] 添加性能监控和日志系统
- [ ] 支持分布式推理

---

## 性能基准

**测试环境：**
- GPU: 48GB VRAM
- Python: 3.12.11
- PyTorch: 2.10.0
- CUDA: 12.8

**模型加载时间：**
- da3nested-giant-large-1.1: ~10-15 秒

**推理性能：**
- 单张图像（1080p）: 待测试
- 视频处理（1080p, 30fps）: 待测试
- COLMAP 数据集: 待测试

---

## 参考资源

**官方文档：**
- 原始项目: https://github.com/ByteDance-Seed/Depth-Anything-3
- WebUI 版本: https://github.com/kegeai888/depth-anything-3-WebUI
- Hugging Face: https://huggingface.co/depth-anything

**WebUI二次开发：**
- 开发者：科哥
- 微信：312088415
- 公众号：科哥玩AI

**相关技术：**
- Gradio 文档: https://www.gradio.app/docs
- PyTorch 文档: https://pytorch.org/docs
- DinoV2: https://github.com/facebookresearch/dinov2

**论文引用：**
```bibtex
@article{depthanything3,
  title={Depth Anything 3: Recovering the visual space from any views},
  author={Haotong Lin and Sili Chen and Jun Hao Liew and Donny Y. Chen and Zhenyu Li and Guang Shi and Jiashi Feng and Bingyi Kang},
  journal={arXiv preprint arXiv:2511.10647},
  year={2025}
}
```

---

## 更新日志

### 2026-01-31 - 生产环境部署

**修复：**
- 修复包结构问题（添加 __init__.py）
- 修复 pyproject.toml 路径配置
- 修复 Gradio 6.4.0 兼容性问题

**优化：**
- 配置本地模型路径
- 添加时间戳输出目录
- 创建启动脚本（端口管理、GPU 清理）

**新增：**
- start_app.sh 启动脚本
- CLAUDE.md 文档
- 完整的部署和测试流程

**测试：**
- ✅ 包安装和导入
- ✅ 模型加载
- ✅ WebUI 启动
- ✅ HTTP 服务响应

**提交：** ef8a2fc - "Deploy production setup with local models and startup script"
