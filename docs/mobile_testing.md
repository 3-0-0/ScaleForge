


# Mobile Testing Strategy

## Platform Detection
The app automatically detects platform via `kivy.utils.platform`:
```python
from kivy.utils import platform
print(f"Running on: {platform}")  # 'android', 'ios', 'win', 'linux', etc.
```

## Testing Approach

### Emulator Testing
1. **Android Studio Emulator**:
   ```bash
   # After setting up Buildozer:
   buildozer android debug deploy run
   ```

2. **Physical Device Testing**:
   ```bash
   adb logcat | grep python
   ```

### Known Mobile Considerations
- Touch input vs mouse events
- Screen density variations
- Permission handling (storage, camera etc.)

### TODO Items
- [ ] Set up Buildozer environment
- [ ] Create mobile-specific test cases
- [ ] Document performance benchmarks
- [ ] Add CI integration for mobile builds

## Kivy Mobile Quirks
- Limited background processing on iOS
- Android storage access requires permissions
- Virtual keyboard may overlap UI elements


