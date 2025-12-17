# ThermalRight LCD USB Device Working State Documentation

## Overview
This document describes the verified working configuration for the ThermalRight LCD display device. This serves as a reference to quickly restore the device to a functional state if configuration changes cause issues.

## Device Specifications

### Hardware Identification
- **Vendor ID (VID)**: 0x0416
- **Product ID (PID)**: 0x5302
- **Manufacturer**: Winbond
- **Display Resolution**: 320x240 pixels
- **Interface**: HID (Human Interface Device) over USB

### Communication Protocol
- **Protocol**: HID
- **Chunk Size**: 512 bytes
- **Data Format**: Raw pixel data with header

## Image Encoding Specification

### Color Format
- **Format**: RGB565 (16-bit color)
- **Bit Layout**: RRRRRGGG GGGBBBBB
- **Byte Order**: Little-endian (low byte first, high byte second)

### Pixel Traversal Order
- **Order**: Column-major
- **Traversal**: Left to right, then bottom to top
- **Code Implementation**:
  ```python
  for x in range(width):      # Columns first (left to right)
      for y in range(height-1, -1, -1): # Rows reversed (bottom to top)
          # Process pixel at (x, y)
  ```

### RGB565 Calculation
```python
r, g, b = img.getpixel((x, y))
val565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
hi = (val565 >> 8) & 0xFF
lo = val565 & 0xFF
out.extend((lo, hi))  # Little-endian: low byte, high byte
```

## Data Packet Structure

### Header Format
- **Prefix**: 4 bytes - `0xDA 0xDB 0xDC 0xDD`
- **Body**: 20 bytes (struct format: `<6HIH`)
  - Field 1: 2 (uint32)
  - Field 2: 1 (uint32)
  - Field 3: 320 (width, uint32)
  - Field 4: 240 (height, uint32)
  - Field 5: 2 (uint32)
  - Field 6: 0 (uint32)
  - Field 7: 153600 (payload size in bytes, uint32)
  - Field 8: 0 (uint16)
- **Total Header Size**: 24 bytes

### Payload
- **Size**: 153600 bytes (320 × 240 × 2 bytes per pixel)
- **Format**: RGB565 encoded pixels in column-major order
- **Chunking**: Split into 512-byte HID packets for transmission

## Metrics Handling

### Working State Behavior
- **Themes without metrics**: Display correctly
- **Themes with metrics**: Service fails to initialize (raises exception on metrics collection failure)
- **Reason**: Metrics collection requires system permissions that may not be available in service context

### Code Location
- File: `src/thermalright_lcd_control/device_controller/display/frame_manager.py`
- Method: `_get_current_metric()`
- Behavior: Raises exception on any CPU/GPU metrics collection failure

## Verification Steps

### 1. Build and Install
```bash
make clean && make
sudo ./install.sh
```

### 2. Start Service
```bash
sudo systemctl start thermalright-lcd-control.service
systemctl status thermalright-lcd-control.service
```

### 3. Test Display
- **Expected**: Clear, correctly oriented display
- **Colors**: Natural (no pink/green garbling)
- **Orientation**: Correct (not rotated)
- **Themes**: Static backgrounds work, metric themes fail gracefully

### 4. Troubleshooting
If display shows:
- **Garbled colors**: Check RGB565 encoding and endianness
- **Rotation**: Verify column-major traversal
- **No display**: Check device connection and service logs
- **Service crashes**: Check metrics configuration in themes

## Configuration Files
- **Service File**: `/etc/systemd/system/thermalright-lcd-control.service`
- **Config Directory**: `~/.config/thermalright-lcd-control/`
- **Application Directory**: `~/.local/share/thermalright-lcd-control/`

## Key Code Locations
- **Device Detection**: `src/thermalright_lcd_control/device_controller/display/device_loader.py`
- **Image Encoding**: `src/thermalright_lcd_control/device_controller/display/display_device.py`
- **Frame Management**: `src/thermalright_lcd_control/device_controller/display/frame_manager.py`
- **HID Implementation**: `src/thermalright_lcd_control/device_controller/display/hid_devices.py`

## Notes
- This configuration is verified to work with the ThermalRight LCD device
- Changes to image encoding or header format may break display functionality
- Metrics collection requires additional error handling for production use
- Always test with static themes first before enabling metrics