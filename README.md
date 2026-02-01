---
title: Depth Anything 3
emoji: 🏢
colorFrom: indigo
colorTo: pink
sdk: gradio
sdk_version: 5.49.1
app_file: app.py
python_version: 3.11
pinned: false
license: cc-by-nc-4.0
---

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference

## 快速开始

### 启动 WebUI

```bash
./start_app.sh
```

访问：http://localhost:7860

### 命令行使用

```bash
# 自动检测输入类型
da3 auto <输入路径>

# 处理单张图像
da3 image photo.jpg

# 处理视频
da3 video video.mp4 --fps 2.0

# 处理 COLMAP 数据
da3 colmap project/ --sparse-subdir 0
```

## 文档

- **[用户使用手册](用户使用手册.md)** - 完整的使用指南和示例
- **[开发记录](todo.md)** - 二次开发、优化和修复记录
- **[CLAUDE.md](CLAUDE.md)** - Claude Code AI 助手集成文档

## 主要特性

- ✅ 本地模型配置（无需下载）
- ✅ 时间戳输出目录（防止覆盖）
- ✅ 自动端口管理
- ✅ GPU 内存优化
- ✅ 支持多种输入格式（图像、视频、COLMAP）
- ✅ 多种输出格式（GLB、PLY、NPZ）
- ✅ 3D 高斯溅射支持

## Citation

If you find Depth Anything 3 useful in your research or projects, please cite:

```bibtex
@article{depthanything3,
  title={Depth Anything 3: Recovering the visual space from any views},
  author={Haotong Lin and Sili Chen and Jun Hao Liew and Donny Y. Chen and Zhenyu Li and Guang Shi and Jiashi Feng and Bingyi Kang},
  journal={arXiv preprint arXiv:2511.10647},
  year={2025}
```
