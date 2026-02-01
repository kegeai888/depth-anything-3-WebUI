#!/usr/bin/env python3
"""
PLY Export MVP Test Script
Tests the end-to-end functionality of PLY file generation after reconstruction.
"""

import os
import sys
import tempfile
import shutil
import numpy as np
from PIL import Image

def create_test_images(output_dir, num_images=3):
    """Create simple test images for reconstruction."""
    print(f"Creating {num_images} test images in {output_dir}...")

    os.makedirs(output_dir, exist_ok=True)

    for i in range(num_images):
        # Create a simple gradient image
        width, height = 640, 480
        img = np.zeros((height, width, 3), dtype=np.uint8)

        # Create different patterns for each image
        if i == 0:
            # Red gradient
            img[:, :, 0] = np.linspace(0, 255, width, dtype=np.uint8)
        elif i == 1:
            # Green gradient
            img[:, :, 1] = np.linspace(0, 255, height, dtype=np.uint8).reshape(-1, 1)
        else:
            # Blue checkerboard
            for y in range(0, height, 40):
                for x in range(0, width, 40):
                    if (x // 40 + y // 40) % 2 == 0:
                        img[y:y+40, x:x+40, 2] = 255

        # Save image
        img_path = os.path.join(output_dir, f"test_{i:04d}.jpg")
        Image.fromarray(img).save(img_path)
        print(f"  ✓ Created {img_path}")

    return output_dir


def run_reconstruction(image_dir, output_dir):
    """Run reconstruction using the CLI."""
    print(f"\nRunning reconstruction...")
    print(f"  Input: {image_dir}")
    print(f"  Output: {output_dir}")

    # Import the API
    from depth_anything_3.api import DepthAnything3
    from depth_anything_3.utils.export.glb import export_to_glb
    from depth_anything_3.utils.export.ply import export_to_ply
    import glob

    # Get model directory
    model_dir = os.environ.get("DA3_MODEL_DIR", "depth-anything/DA3NESTED-GIANT-LARGE")
    print(f"  Model: {model_dir}")

    # Load model
    print("  Loading model...")
    model = DepthAnything3.from_pretrained(model_dir)
    model.eval()

    # Get image paths
    image_paths = sorted(glob.glob(os.path.join(image_dir, "*.jpg")))
    print(f"  Found {len(image_paths)} images")

    # Run inference
    print("  Running inference...")
    prediction = model.inference(
        image_paths,
        export_dir=None,
        process_res_method="upper_bound_resize",
        infer_gs=False
    )

    # Export to GLB
    print("  Exporting to GLB...")
    export_to_glb(
        prediction,
        export_dir=output_dir,
        show_cameras=True,
        conf_thresh_percentile=40.0,
        num_max_points=100000
    )

    # Export to PLY
    print("  Exporting to PLY...")
    ply_path = export_to_ply(
        prediction,
        export_dir=output_dir,
        conf_thresh_percentile=40.0,
        num_max_points=100000
    )

    print(f"  ✓ Reconstruction complete")
    return ply_path


def verify_ply_file(ply_path):
    """Verify the PLY file was created and has valid format."""
    print(f"\nVerifying PLY file: {ply_path}")

    # Check file exists
    if not os.path.exists(ply_path):
        print(f"  ✗ FAIL: PLY file not found")
        return False
    print(f"  ✓ File exists")

    # Check file size
    file_size = os.path.getsize(ply_path)
    if file_size == 0:
        print(f"  ✗ FAIL: PLY file is empty")
        return False
    print(f"  ✓ File size: {file_size:,} bytes")

    # Read and verify content
    try:
        with open(ply_path, 'r') as f:
            lines = f.readlines()

        # Check header
        if lines[0].strip() != 'ply':
            print(f"  ✗ FAIL: Invalid PLY header")
            return False
        print(f"  ✓ Valid PLY header")

        if 'format ascii 1.0' not in lines[1]:
            print(f"  ✗ FAIL: Invalid format line")
            return False
        print(f"  ✓ Valid format (ASCII 1.0)")

        # Find vertex count
        vertex_count = 0
        header_end = 0
        for i, line in enumerate(lines):
            if line.startswith('element vertex'):
                vertex_count = int(line.split()[2])
            if line.strip() == 'end_header':
                header_end = i + 1
                break

        if vertex_count == 0:
            print(f"  ✗ FAIL: No vertices in PLY file")
            return False
        print(f"  ✓ Vertex count: {vertex_count:,}")

        # Verify we have the right number of data lines
        data_lines = len(lines) - header_end
        if data_lines < vertex_count:
            print(f"  ✗ FAIL: Not enough data lines ({data_lines} < {vertex_count})")
            return False
        print(f"  ✓ Data lines: {data_lines}")

        # Verify first few vertices have valid format
        print(f"  Checking vertex data format...")
        for i in range(min(5, vertex_count)):
            line = lines[header_end + i].strip()
            parts = line.split()
            if len(parts) != 6:
                print(f"    ✗ FAIL: Invalid vertex format at line {i}")
                return False

            # Check coordinate values
            try:
                x, y, z = float(parts[0]), float(parts[1]), float(parts[2])
                r, g, b = int(parts[3]), int(parts[4]), int(parts[5])

                # Validate ranges
                if not (-10000 < x < 10000 and -10000 < y < 10000 and -10000 < z < 10000):
                    print(f"    ✗ FAIL: Coordinates out of range at line {i}")
                    return False

                if not (0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255):
                    print(f"    ✗ FAIL: Color values out of range at line {i}")
                    return False

            except ValueError:
                print(f"    ✗ FAIL: Invalid numeric values at line {i}")
                return False

        print(f"  ✓ Vertex data format valid")

        # Show sample vertices
        print(f"\n  Sample vertices:")
        for i in range(min(3, vertex_count)):
            line = lines[header_end + i].strip()
            parts = line.split()
            print(f"    Vertex {i}: pos=({parts[0]}, {parts[1]}, {parts[2]}), "
                  f"color=({parts[3]}, {parts[4]}, {parts[5]})")

    except Exception as e:
        print(f"  ✗ FAIL: Error reading PLY file: {e}")
        return False

    print(f"\n  ✓ PLY file validation PASSED")
    return True


def main():
    """Main test function."""
    print("=" * 70)
    print("PLY Export MVP Test")
    print("=" * 70)

    # Create temporary directories
    test_dir = tempfile.mkdtemp(prefix="ply_test_")
    image_dir = os.path.join(test_dir, "images")
    output_dir = os.path.join(test_dir, "output")

    print(f"\nTest directory: {test_dir}")

    try:
        # Step 1: Create test images
        print("\n" + "=" * 70)
        print("Step 1: Create Test Images")
        print("=" * 70)
        create_test_images(image_dir, num_images=3)

        # Step 2: Run reconstruction
        print("\n" + "=" * 70)
        print("Step 2: Run Reconstruction")
        print("=" * 70)
        ply_path = run_reconstruction(image_dir, output_dir)

        # Step 3: Verify PLY file
        print("\n" + "=" * 70)
        print("Step 3: Verify PLY File")
        print("=" * 70)
        success = verify_ply_file(ply_path)

        # Results
        print("\n" + "=" * 70)
        if success:
            print("✅ TEST PASSED!")
            print("=" * 70)
            print(f"\nPLY file successfully generated at:")
            print(f"  {ply_path}")
            print(f"\nYou can open this file in:")
            print(f"  • MeshLab")
            print(f"  • CloudCompare")
            print(f"  • Blender")
            print(f"\nTest artifacts saved in: {test_dir}")
            return 0
        else:
            print("❌ TEST FAILED!")
            print("=" * 70)
            print(f"\nTest artifacts saved in: {test_dir}")
            return 1

    except Exception as e:
        print(f"\n❌ TEST FAILED WITH EXCEPTION!")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        print(f"\nTest artifacts saved in: {test_dir}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
