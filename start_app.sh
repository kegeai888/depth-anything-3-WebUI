#!/bin/bash

# Depth Anything 3 WebUI Startup Script
# This script manages port conflicts and GPU memory before launching the Gradio interface

set -e

PORT=7860
HOST="0.0.0.0"

echo "=== Depth Anything 3 WebUI Startup ==="
echo "Port: $PORT"
echo "Host: $HOST"
echo ""

# Function to check if port is in use
check_port() {
    lsof -ti:$PORT 2>/dev/null
}

# Function to kill process on port
kill_port_process() {
    local pid=$(check_port)
    if [ -n "$pid" ]; then
        echo "Found process $pid using port $PORT"
        echo "Terminating process..."
        kill -9 $pid 2>/dev/null || true
        echo "Process terminated"
        return 0
    fi
    return 1
}

# Function to clean GPU memory
clean_gpu_memory() {
    echo "Cleaning GPU memory..."

    # Try to use nvidia-smi to reset GPU
    if command -v nvidia-smi &> /dev/null; then
        # Get list of processes using GPU
        gpu_pids=$(nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null || true)

        if [ -n "$gpu_pids" ]; then
            echo "Found GPU processes: $gpu_pids"
            # Note: We don't kill these automatically as they might be important
            # Just report them
            echo "Warning: GPU is currently in use by other processes"
        fi

        # Force garbage collection in Python can help, but we'll do this in the app
        echo "GPU memory cleanup will be handled by the application"
    else
        echo "nvidia-smi not found, skipping GPU cleanup"
    fi
}

# Check and handle port conflict
if check_port; then
    echo "Port $PORT is currently in use"
    kill_port_process

    # Wait 2 seconds after killing process
    echo "Waiting 2 seconds for port to be released..."
    sleep 2

    # Verify port is now free
    if check_port; then
        echo "Error: Port $PORT is still in use after cleanup"
        exit 1
    fi
    echo "Port $PORT is now available"
else
    echo "Port $PORT is available"
fi

# Clean GPU memory
clean_gpu_memory

echo ""
echo "Starting Depth Anything 3 WebUI..."
echo "Access the interface at: http://localhost:$PORT"
echo "Press Ctrl+C to stop the server"
echo ""

# Set environment variables for optimal performance
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export HF_ENDPOINT=http://hf.x-gpu.com

# Launch the Gradio app
cd "$(dirname "$0")"
da3 gradio --host $HOST --port $PORT
