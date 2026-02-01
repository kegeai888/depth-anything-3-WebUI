#!/usr/bin/env python3
"""
PLY Export Quick Test
A lightweight test to quickly verify PLY export functionality.
"""

import os
import sys
import tempfile
import numpy as np
from PIL import Image


def quick_test():
    """Quick test of PLY export functionality."""
    print("🧪 PLY Export Quick Test\n")

    # Create temp directory
    test_dir = tempfile.mkdtemp(prefix="ply_quick_test_")
    image_dir = os.path.join(test_dir, "images")
    output_dir = os.path.join(test_dir, "output")
    os.makedirs(image_dir, exist_ok=True)

    print(f"📁 Test directory: {test_dir}\n")

    try:
        # Create 2 simple test images
        print("1️⃣  Creating test images...")
        for i in range(2):
            img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            Image.fromarray(img).save(os.path.join(image_dir, f"test_{i:04d}.jpg"))
        print("   ✓ Created 2 test images\n")

        # Run reconstruction
        print("2️⃣  Running reconstruction...")
        from depth_anything_3.api import DepthAnything3
        from depth_anything_3.utils.export.ply import export_to_ply
        import glob

        model_dir = os.environ.get("DA3_MODEL_DIR", "depth-anything/DA3NESTED-GIANT-LARGE")
        model = DepthAnything3.from_pretrained(model_dir)
        model.eval()

        image_paths = sorted(glob.glob(os.path.join(image_dir, "*.jpg")))
        prediction = model.inference(image_paths, export_dir=None, process_res_method="upper_bound_resize")

        print("   ✓ Inference complete\n")

        # Export to PLY
        print("3️⃣  Exporting to PLY...")
        ply_path = export_to_ply(prediction, export_dir=output_dir, num_max_points=10000)
        print(f"   ✓ PLY exported to: {ply_path}\n")

        # Verify
        print("4️⃣  Verifying PLY file...")
        assert os.path.exists(ply_path), "PLY file not found"
        file_size = os.path.getsize(ply_path)
        assert file_size > 0, "PLY file is empty"

        with open(ply_path, 'r') as f:
            content = f.read()
        assert 'ply' in content and 'element vertex' in content, "Invalid PLY format"

        print(f"   ✓ File size: {file_size:,} bytes")
        print(f"   ✓ Format valid\n")

        # Success
        print("=" * 60)
        print("✅ QUICK TEST PASSED!")
        print("=" * 60)
        print(f"\n📄 PLY file: {ply_path}")
        print(f"📂 Test dir: {test_dir}")
        return 0

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(quick_test())
