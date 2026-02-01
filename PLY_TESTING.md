# PLY Export Testing

This directory contains test scripts to verify the PLY point cloud export functionality.

## Test Scripts

### 1. Full MVP Test (`test_ply_export.py`)

Comprehensive end-to-end test that validates the complete PLY export pipeline.

**What it tests:**
- Test image creation
- Model loading and inference
- GLB export
- PLY export
- File format validation
- Vertex data verification

**Usage:**
```bash
python3 test_ply_export.py
```

**Expected output:**
- Creates 3 test images (640x480)
- Runs full reconstruction
- Generates PLY file with 100,000 points
- Validates PLY format
- Shows sample vertices

**Time:** ~3-5 minutes (depending on GPU)

### 2. Quick Test (`test_ply_quick.py`)

Lightweight test for rapid verification.

**What it tests:**
- Basic PLY export functionality
- File creation and format

**Usage:**
```bash
python3 test_ply_quick.py
```

**Expected output:**
- Creates 2 test images
- Generates PLY file with 10,000 points
- Quick format validation

**Time:** ~2-3 minutes

## Test Results

Both tests should output:
```
✅ TEST PASSED!
```

If tests fail, check:
1. Model is properly installed
2. CUDA is available (for GPU inference)
3. All dependencies are installed

## Viewing PLY Files

Generated PLY files can be opened in:
- **MeshLab**: Free, cross-platform point cloud viewer
- **CloudCompare**: Advanced point cloud processing
- **Blender**: 3D modeling software (File > Import > Stanford PLY)

## Test Artifacts

Test files are saved in temporary directories:
- `/tmp/ply_test_*` (full test)
- `/tmp/ply_quick_test_*` (quick test)

To keep test files for inspection, modify the scripts to use a fixed directory instead of `tempfile.mkdtemp()`.

## Troubleshooting

### Model not found
```bash
export DA3_MODEL_DIR=/path/to/your/model
```

### Out of memory
Reduce `num_max_points` in the test scripts:
```python
export_to_ply(prediction, export_dir=output_dir, num_max_points=5000)
```

### Import errors
Make sure the package is installed:
```bash
pip install -e .
```

## Integration with CI/CD

To run tests in CI/CD pipelines:

```bash
# Run quick test
python3 test_ply_quick.py || exit 1

# Or run full test
python3 test_ply_export.py || exit 1
```

## Manual Testing

To manually test the Gradio interface:

1. Start the app:
   ```bash
   ./start_app.sh
   ```

2. Open browser: http://localhost:7860

3. Upload images or select an example scene

4. Click "Reconstruct"

5. Go to "PLY File Download" tab

6. Download the PLY file

7. Open in MeshLab or CloudCompare to verify

## Expected PLY File Structure

```
ply
format ascii 1.0
element vertex [N]
property float x
property float y
property float z
property uchar red
property uchar green
property uchar blue
end_header
[vertex data lines...]
```

Where `[N]` is the number of vertices (up to `num_max_points`).
