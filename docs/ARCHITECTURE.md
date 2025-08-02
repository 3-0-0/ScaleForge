
# ScaleForge Architecture

## GPU Processing Flow

```mermaid
flowchart LR
  A[gpu_caps.json] --> G[load_caps / probe_limits]
  G --> B[selector]
  B --> C{Env override?}
  C -->|yes| D[Forced backend]
  C -->|no| E[Vendor-based selection]
  E --> F[Backend (Torch / Vulkan)]
  B --> H[fallbacks]
```

### Key Components

1. **gpu_caps.json** - Cache file storing:
   - Detected GPU vendor
   - Maximum tile size
   - Maximum pixel capacity
   - Timestamp of last probe

2. **Backend Selector**:
   - Checks for environment overrides first
   - Falls back to vendor-specific selection
   - Provides safe defaults when detection fails

3. **Oversize Protection**:
   - Calculates: width × height × scale²
   - Compares against cached max_pixels
   - Skips with status: skipped_oversize
   - Records reason in job.extra

4. **Probe Limits**:
   - Runs tiny test upscale
   - Measures memory usage
   - Determines safe working parameters
