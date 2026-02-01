# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Depth Anything 3 is a depth estimation and camera pose estimation system that supports multiple input types (images, videos, COLMAP data) and exports to various 3D formats. The project includes:
- A PyTorch-based depth estimation model with DinoV2 backbone
- Camera pose estimation capabilities
- 3D Gaussian Splatting (3DGS) support
- Gradio web interface for interactive use
- CLI tool (`da3`) for batch processing
- FastAPI backend service for remote inference
- Gallery system for visualizing results

## Installation & Setup

```bash
# Install the package in development mode
pip install -e .

# For Gradio app support
pip install -e ".[app]"

# For 3D Gaussian Splatting support
pip install -e ".[gs]"

# Install all optional dependencies
pip install -e ".[all]"
```

**Note**: The project requires Python 3.11+ and PyTorch 2.0+. The `gsplat` dependency requires CUDA during build.

## Local Model Configuration

The project is configured to use local models by default (avoiding Hugging Face Hub downloads):

**Available Local Models** (in `models/` directory):
- `da3nested-giant-large-1.1/` - Default nested model (6.3GB)
- `da3-giant-1.1/` - Giant model (6.3GB)
- `da3-large/` - Large model

**Configuration**: The default model path is set in `depth_anything_3/utils/constants.py`:
```python
DEFAULT_MODEL = os.path.join(PROJECT_ROOT, "models/da3nested-giant-large-1.1")
```

To use a different model, either:
1. Set the `DA3_MODEL_DIR` environment variable
2. Pass `--model-dir` flag to CLI commands
3. Modify `DEFAULT_MODEL` in `constants.py`

## Common Commands

### CLI Usage

The main CLI entry point is `da3` (defined in `pyproject.toml`):

```bash
# Auto-detect input type and process
da3 auto <input_path>

# Process single image
da3 image <image_path>

# Process directory of images
da3 images <images_dir>

# Process video (extracts frames)
da3 video <video_path> --fps 1.0

# Process COLMAP data
da3 colmap <colmap_dir> --sparse-subdir 0

# Launch Gradio web interface
da3 gradio --host 127.0.0.1 --port 7860

# Start backend service
da3 backend --host 127.0.0.1 --port 8008

# Launch gallery viewer
da3 gallery --host 127.0.0.1 --port 8007
```

### Running the Gradio App

```bash
# Recommended: Use the startup script (handles port conflicts and GPU cleanup)
./start_app.sh

# Or run directly
python app.py

# Or via CLI
da3 gradio --workspace-dir workspace/gradio --gallery-dir workspace/gallery
```

The `app.py` file is specifically configured for Hugging Face Spaces deployment with the `@spaces.GPU` decorator.

**Startup Script Features** (`start_app.sh`):
- Automatically detects and kills processes using port 7860
- Cleans GPU memory before launch
- Sets optimal environment variables (`PYTORCH_CUDA_ALLOC_CONF`, `HF_ENDPOINT`)
- Provides clear status messages and error handling

### Backend Service

```bash
# Start the inference backend
da3 backend --model-dir depth-anything/DA3NESTED-GIANT-LARGE --device cuda

# Use backend for inference (from another terminal)
da3 auto <input> --use-backend --backend-url http://localhost:8008
```

## Code Architecture

### High-Level Structure

```
depth_anything_3/
├── api.py                    # Main API class (DepthAnything3)
├── cli.py                    # CLI commands and routing
├── cfg.py                    # Configuration loading utilities
├── registry.py               # Model registry (scans configs/)
├── specs.py                  # Data structures (Prediction, etc.)
├── configs/                  # Model configuration YAML files
│   ├── da3-giant.yaml
│   ├── da3-large.yaml
│   ├── da3nested-giant-large.yaml  # Nested model (anyview + metric)
│   └── ...
├── model/                    # Neural network implementations
│   ├── da3.py               # DepthAnything3Net (main network)
│   ├── cam_dec.py           # Camera decoder (pose estimation)
│   ├── gs_adapter.py        # 3D Gaussian Splatting adapter
│   ├── dinov2/              # DinoV2 backbone
│   └── utils/               # Model utilities
├── app/                     # Gradio web interface
│   ├── gradio_app.py        # Main Gradio app class
│   ├── css_and_html.py      # UI styling
│   └── modules/             # UI components and handlers
│       ├── ui_components.py
│       ├── event_handlers.py
│       ├── model_inference.py
│       └── ...
├── services/                # Backend services
│   ├── backend.py           # FastAPI backend server
│   ├── inference_service.py # Unified inference interface
│   ├── input_handlers.py    # Input processing (image/video/COLMAP)
│   └── gallery.py           # Gallery server
└── utils/                   # Utilities
    ├── constants.py         # Default paths and settings
    ├── geometry.py          # 3D geometry operations
    ├── pose_align.py        # Pose alignment (Umeyama)
    ├── alignment.py         # Metric depth alignment
    ├── export/              # Export to GLB, PLY, NPZ, etc.
    └── io/                  # Input/output processors
```

### Key Components

#### 1. Model Architecture (`model/da3.py`)

The core network is `DepthAnything3Net`, which consists of:
- **Backbone**: DinoV2 feature extractor (patch size 14)
- **Head**: DPT or DualDPT for depth prediction
- **Camera Decoder** (`cam_dec`): Predicts camera pose (translation, quaternion, FOV)
- **Camera Encoder** (`cam_enc`): Encodes known camera poses
- **GS Adapter** (`gs_adapter`): Converts depth to 3D Gaussian Splats

For nested models (e.g., `da3nested-giant-large`), there are two sub-networks:
- `anyview`: For multi-view depth estimation (giant model)
- `metric`: For metric depth scaling (large model)

#### 2. API Layer (`api.py`)

`DepthAnything3` is the main user-facing class:
- Inherits from `PyTorchModelHubMixin` for Hugging Face Hub integration
- Loads models via `from_pretrained()` or by preset name
- Main method: `inference()` - processes images and exports results
- Handles input preprocessing, model forward pass, and output export

#### 3. Configuration System (`cfg.py`, `registry.py`)

- Model configs are YAML files in `configs/`
- `registry.py` scans configs and builds `MODEL_REGISTRY`
- `cfg.py` provides `load_config()` and `create_object()` for dynamic instantiation
- Configs support inheritance via `__inherit__` key

#### 4. Input Processing (`services/input_handlers.py`)

Handlers for different input types:
- `ImageHandler`: Single image
- `ImagesHandler`: Directory of images
- `VideoHandler`: Video file (extracts frames with moviepy)
- `ColmapHandler`: COLMAP reconstruction (reads sparse/cameras.bin, images.bin)

#### 5. Export System (`utils/export/`)

Supports multiple export formats:
- `glb`: 3D point cloud with cameras (for web viewers)
- `ply`: Point cloud
- `npz`: NumPy arrays (depth, confidence, poses)
- `feat_vis`: Feature visualization videos
- Combinations: `mini_npz-glb`, `npz-glb`, etc.

#### 6. Gradio App (`app/`)

Modular Gradio interface:
- `DepthAnything3App`: Main app class
- `UIComponents`: Builds UI elements
- `EventHandlers`: Handles user interactions
- `ModelInference`: Runs inference (decorated with `@spaces.GPU` in `app.py`)

The app supports:
- Scene selection from examples
- Resolution settings (low/high)
- 3D visualization options
- Point cloud filtering
- 3DGS rendering with trajectory generation

### Important Patterns

#### Model Loading

Models are loaded from Hugging Face Hub or local directories:

```python
# From Hub
model = DepthAnything3.from_pretrained("depth-anything/DA3NESTED-GIANT-LARGE")

# From local directory
model = DepthAnything3.from_pretrained("/path/to/model")

# By preset name (requires config in configs/)
model = DepthAnything3(model_name="da3-large")
```

#### Inference Flow

1. Input processing: Load images, extract frames, or read COLMAP data
2. Model forward pass: Predict depth, confidence, and camera poses
3. Post-processing: Metric alignment, sky masking, confidence filtering
4. Export: Save to specified format(s)

#### Camera Pose Handling

- **Predicted poses**: When no extrinsics provided, model predicts them
- **Known poses**: When extrinsics provided (COLMAP), model uses them for conditioning
- **Alignment**: Predicted poses can be aligned to input scale via Umeyama algorithm

#### 3D Gaussian Splatting

When `infer_gs=True`:
1. Depth maps are converted to 3D Gaussians
2. Gaussians are optimized for novel view synthesis
3. Trajectory videos can be generated with `gs_trj_mode` (smooth/orbit/etc.)

## Code Style

The project uses:
- **Black** formatter (line length 99)
- **isort** for import sorting (black profile)
- **pre-commit** hooks for automated formatting
- Type hints where applicable
- Docstrings for public APIs

Format code before committing:
```bash
black depth_anything_3 --line-length 99
isort depth_anything_3
```

Install and run pre-commit hooks:
```bash
pre-commit install
pre-commit run --all-files
```

## Testing

**Current Status**: The project does not have automated tests yet. This is a high-priority item for future development.

**Planned Testing Areas**:
- Unit tests for model components
- Integration tests for CLI commands
- End-to-end tests for inference pipeline
- Performance benchmarks

To add tests, create a `tests/` directory and use pytest as the testing framework.

## Environment Variables

- `DA3_MODEL_DIR`: Default model directory (default: `depth-anything/DA3NESTED-GIANT-LARGE`)
  - For local models, set to absolute path like `/root/depth-anything-3/models/da3nested-giant-large-1.1`
- `DA3_WORKSPACE_DIR`: Workspace directory for Gradio (default: `workspace/gradio`)
- `DA3_GALLERY_DIR`: Gallery directory (default: `workspace/gallery`)
- `DA3_CACHE_EXAMPLES`: Enable example caching (default: auto-detect)
- `DA3_CACHE_GS_TAG`: Tag for high-res+3DGS caching (default: `dl3dv`)
- `PYTORCH_CUDA_ALLOC_CONF`: Set to `expandable_segments:True` for better memory management
- `HF_ENDPOINT`: Hugging Face mirror endpoint (e.g., `http://hf.x-gpu.com` for faster downloads in China)

## Hugging Face Spaces Deployment

The `app.py` file is configured for Spaces:
- Uses `@spaces.GPU` decorator for GPU allocation
- Reads config from `README.md` frontmatter
- Supports example pre-caching via `DA3_CACHE_EXAMPLES`
- Binds to `0.0.0.0:7860` for Spaces routing

## Common Gotchas

1. **Model paths**: Default model is on Hugging Face Hub. For local models, ensure the directory contains `model.safetensors` and `config.json`. The project is configured to use local models in `models/` directory by default (see `utils/constants.py`).

2. **COLMAP format**: Expects `images/` and `sparse/` subdirectories. Use `--sparse-subdir 0` if reconstruction is in `sparse/0/`.

3. **Export directory**: CLI auto-creates export directories with timestamps (format: `outputs/outputs_YYYYMMDDHHMMSS`) to prevent overwriting previous results. Use `--auto-cleanup` to skip confirmation prompts.

4. **GPU memory**: For large scenes, reduce `process_res` or use `num_max_points` to limit point cloud size.

5. **gsplat dependency**: Requires CUDA during installation. If build fails, install from pre-built wheel (see `requirements.txt`).

6. **Nested models**: `da3nested-giant-large` combines two models (anyview + metric). Inference is slower but more accurate.

7. **Port conflicts**: If port 7860 is in use, the `start_app.sh` script will automatically handle it. For manual cleanup: `kill -9 $(lsof -ti:7860)`.

8. **Gradio version**: The project uses Gradio 6.4.0+. Some parameters like `show_download_button` are not supported in newer versions.

## Additional Documentation

For more detailed information, refer to:
- **[用户使用手册.md](用户使用手册.md)** - Complete user guide in Chinese
- **[todo.md](todo.md)** - Development log with fixes, optimizations, and known issues
- **[README.md](README.md)** - Quick start guide and main features

## Citation

If using this code in research, cite:
```bibtex
@article{depthanything3,
  title={Depth Anything 3: Recovering the visual space from any views},
  author={Haotong Lin and Sili Chen and Jun Hao Liew and Donny Y. Chen and Zhenyu Li and Guang Shi and Jiashi Feng and Bingyi Kang},
  journal={arXiv preprint arXiv:2511.10647},
  year={2025}
}
```
