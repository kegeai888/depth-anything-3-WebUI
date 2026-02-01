# Copyright (c) 2025 ByteDance Ltd. and/or its affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
PLY point cloud export module for Depth Anything 3.

This module exports depth predictions as standard PLY point cloud files.
"""

from __future__ import annotations

import os
import numpy as np

from depth_anything_3.specs import Prediction
from depth_anything_3.utils.logger import logger

from .glb import (
    _as_homogeneous44,
    _depths_to_world_points_with_colors,
    _filter_and_downsample,
    get_conf_thresh,
    set_sky_depth,
)


def export_to_ply(
    prediction: Prediction,
    export_dir: str,
    num_max_points: int = 1_000_000,
    conf_thresh: float = 1.05,
    filter_black_bg: bool = False,
    filter_white_bg: bool = False,
    conf_thresh_percentile: float = 40.0,
    ensure_thresh_percentile: float = 90.0,
    sky_depth_def: float = 98.0,
) -> str:
    """Export depth predictions as a standard PLY point cloud file.

    This function generates a colored point cloud from depth maps and saves it
    as a PLY file. The point cloud is created by back-projecting depth values
    to 3D world coordinates using camera intrinsics and extrinsics.

    Args:
        prediction: Model prediction containing depth, confidence, intrinsics,
            extrinsics, and pre-processed images.
        export_dir: Output directory where the PLY file will be written.
        num_max_points: Maximum number of points retained after downsampling.
        conf_thresh: Base confidence threshold used before percentile adjustments.
        filter_black_bg: Mark near-black background pixels for removal.
        filter_white_bg: Mark near-white background pixels for removal.
        conf_thresh_percentile: Lower percentile used when adapting confidence threshold.
        ensure_thresh_percentile: Upper percentile clamp for the adaptive threshold.
        sky_depth_def: Percentile used to fill sky pixels with plausible depth values.

    Returns:
        Path to the exported PLY file.
    """
    # Validate required prediction data
    assert (
        prediction.processed_images is not None
    ), "Export to PLY: prediction.processed_images is required but not available"
    assert (
        prediction.depth is not None
    ), "Export to PLY: prediction.depth is required but not available"
    assert (
        prediction.intrinsics is not None
    ), "Export to PLY: prediction.intrinsics is required but not available"
    assert (
        prediction.extrinsics is not None
    ), "Export to PLY: prediction.extrinsics is required but not available"
    assert (
        prediction.conf is not None
    ), "Export to PLY: prediction.conf is required but not available"

    logger.info(f"Exporting to PLY with num_max_points: {num_max_points}")

    images_u8 = prediction.processed_images  # (N,H,W,3) uint8

    # Sky processing (if sky_mask is provided)
    if getattr(prediction, "sky_mask", None) is not None:
        set_sky_depth(prediction, prediction.sky_mask, sky_depth_def)

    # Confidence threshold filtering
    if filter_black_bg:
        prediction.conf[(prediction.processed_images < 16).all(axis=-1)] = 1.0
    if filter_white_bg:
        prediction.conf[(prediction.processed_images >= 240).all(axis=-1)] = 1.0

    conf_thr = get_conf_thresh(
        prediction,
        getattr(prediction, "sky_mask", None),
        conf_thresh,
        conf_thresh_percentile,
        ensure_thresh_percentile,
    )

    # Back-project to world coordinates and get colors
    points, colors = _depths_to_world_points_with_colors(
        prediction.depth,
        prediction.intrinsics,
        prediction.extrinsics,
        images_u8,
        prediction.conf,
        conf_thr,
    )

    # Filter and downsample
    points, colors = _filter_and_downsample(points, colors, num_max_points)

    # Create output directory
    os.makedirs(export_dir, exist_ok=True)
    out_path = os.path.join(export_dir, "scene.ply")

    # Write PLY file
    _write_ply(out_path, points, colors)

    logger.info(f"Exported PLY point cloud to: {out_path}")
    logger.info(f"Total points: {points.shape[0]}")

    return out_path


def _write_ply(filepath: str, points: np.ndarray, colors: np.ndarray) -> None:
    """Write point cloud data to a PLY file.

    Args:
        filepath: Path to the output PLY file.
        points: Point coordinates array of shape (N, 3).
        colors: RGB color array of shape (N, 3) with uint8 values.
    """
    num_points = points.shape[0]

    # PLY header
    header = f"""ply
format ascii 1.0
element vertex {num_points}
property float x
property float y
property float z
property uchar red
property uchar green
property uchar blue
end_header
"""

    with open(filepath, "w") as f:
        f.write(header)

        # Write vertex data
        for i in range(num_points):
            x, y, z = points[i]
            r, g, b = colors[i]
            f.write(f"{x:.6f} {y:.6f} {z:.6f} {int(r)} {int(g)} {int(b)}\n")


def _write_ply_binary(filepath: str, points: np.ndarray, colors: np.ndarray) -> None:
    """Write point cloud data to a binary PLY file (faster for large point clouds).

    Args:
        filepath: Path to the output PLY file.
        points: Point coordinates array of shape (N, 3).
        colors: RGB color array of shape (N, 3) with uint8 values.
    """
    num_points = points.shape[0]

    # PLY header for binary format
    header = f"""ply
format binary_little_endian 1.0
element vertex {num_points}
property float x
property float y
property float z
property uchar red
property uchar green
property uchar blue
end_header
"""

    # Create structured array for binary output
    dtype = np.dtype([
        ("x", "<f4"),
        ("y", "<f4"),
        ("z", "<f4"),
        ("red", "u1"),
        ("green", "u1"),
        ("blue", "u1"),
    ])

    vertex_data = np.zeros(num_points, dtype=dtype)
    vertex_data["x"] = points[:, 0].astype(np.float32)
    vertex_data["y"] = points[:, 1].astype(np.float32)
    vertex_data["z"] = points[:, 2].astype(np.float32)
    vertex_data["red"] = colors[:, 0].astype(np.uint8)
    vertex_data["green"] = colors[:, 1].astype(np.uint8)
    vertex_data["blue"] = colors[:, 2].astype(np.uint8)

    with open(filepath, "wb") as f:
        f.write(header.encode("ascii"))
        vertex_data.tofile(f)
