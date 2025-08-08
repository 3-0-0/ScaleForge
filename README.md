# ScaleForge

Image upscaling and enhancement toolkit

## GPU Detection & Capability Cache

ScaleForge automatically detects your GPU capabilities and caches the results for optimal performance:

- **Cache Location**: `${APP_ROOT}/gpu_caps.json`  
- **Key Information**:
  - GPU vendor (nvidia/amd/intel)
  - Recommended backend (torch-cuda/torch-rocm/torch-cpu/ncnn-vulkan)
  - Performance capabilities (max tile size, megapixels)
  - Detection timestamp

### Commands
- `scaleforge detect-backend`: Show current backend info
  - `--probe`: Force fresh GPU detection
  - `--debug`: Show detailed capability info

### Environment Overrides  
Set `SCALEFORGE_BACKEND` to override auto-selection:
- `torch-cuda`: NVIDIA GPUs
- `torch-rocm`: AMD GPUs
- `torch-cpu`: CPU fallback  
- `ncnn-vulkan`: Vulkan-based acceleration

Note: Values are conservatively tuned for stability. Advanced users can adjust via settings.


GPU Detection & Capability Cache
- Location: APP_ROOT/gpu_caps.json
- Fields: vendor, backend, max_tile_size, max_megapixels, detected_at, source
- Commands: scaleforge detect-backend --probe, scaleforge detect-backend --debug
- Env overrides: environment variables that can influence vendor/backend or capabilities (see docs for exact names)
