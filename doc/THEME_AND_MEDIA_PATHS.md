# Theme and Media Paths Structure

## Current Path Configuration

### Source Code Paths (from config.yaml)
Based on code analysis:

1. **Backgrounds Directory:**
   ```python
   self.backgrounds_dir = paths.get('backgrounds_dir', './themes/backgrounds')
   ```
   - Used by MediaTab to show background images/videos

2. **Themes Directory:**
   ```python
   themes_dir = f"{self.config.get('paths', {}).get('themes_dir', './themes')}/{dev_width}{dev_height}"
   ```
   - Used by ThemesTab for saving/loading themes
   - Organized by resolution: `{themes_dir}/{width}{height}/`

3. **Service Config Directory:**
   ```python
   service_config_dir = self.config.get('paths', {}).get('service_config', './config')
   service_config_path = f"{service_config_dir}/config_{dev_width}{dev_height}.yaml"
   ```
   - Where current config is saved for service to read
   - Service monitors this directory for changes

### Installed Application Paths (Actual)
From debugging sessions:

1. **Service Config Location:**
   ```
   /home/leeo/.config/thermalright-lcd-control/config/config_320240.yaml
   ```

2. **Themes Presets Location:**
   ```
   /home/leeo/.config/thermalright-lcd-control/themes/presets/320240/
   ├── config_1.yaml
   ├── config_2.yaml
   └── ...
   ```

3. **Background Media Location:**
   - Unknown - Need to check where media files are stored
   - Likely: `/home/leeo/.config/thermalright-lcd-control/themes/backgrounds/`

## Path Resolution Logic

The application uses **relative paths in config** that get resolved to **absolute paths at runtime**:

```
Relative path in config → Resolved to user config directory
```

### Expected Full Structure:
```
~/.config/thermalright-lcd-control/
├── config/
│   └── config_{width}{height}.yaml          # Current active config
├── themes/
│   ├── backgrounds/                         # Background images/videos
│   │   ├── y010.png
│   │   ├── a001.mp4
│   │   └── ...
│   └── presets/
│       └── {width}{height}/                 # Organized by resolution
│           ├── config_1.yaml
│           ├── config_2.yaml
│           └── ...
└── (other app data)
```

## Media Tab Functionality

### Current Implementation:
- `MediaTab` class in `src/thermalright_lcd_control/gui/tabs/media_tab.py`
- Shows thumbnails of media files in `backgrounds_dir`
- Allows adding new media files
- Emits `thumbnail_clicked` signal when media selected

### Integration in Main Window:
```python
media_tab = MediaTab(self.backgrounds_dir, self.config, "Media")
self.tab_widget.addTab(media_tab, "Media")
```

### Missing Connections:
1. **Media selection → Background update**
   - Need to connect `thumbnail_clicked` signal to set background
   - Update `preview_manager.current_background_path`
   - Update `preview_manager.background_type` (IMAGE/VIDEO/GIF)

2. **Background type switching**
   - Currently only COLOR background type is fully implemented
   - Need to handle IMAGE/VIDEO/GIF background types

## Themes Tab Functionality

### Current Implementation:
- `ThemesTab` class in `src/thermalright_lcd_control/gui/tabs/themes_tab.py`
- Loads theme files from `themes_dir/{width}{height}/`
- Shows theme thumbnails
- Emits `theme_selected` signal

### Integration:
```python
themes_tab = ThemesTab(themes_dir, dev_width=self.device_width, dev_height=self.device_height)
self.tab_widget.addTab(themes_tab, "Themes")
```

### Missing Connections:
1. **Theme selection → Config load**
   - Need to load selected theme config
   - Apply to unified widgets
   - Update preview

2. **Save current as theme**
   - Save current config to themes directory
   - Generate thumbnail preview

## Required Implementation Steps

### Phase 1: Media Background Support
1. Connect MediaTab signals to set background
2. Update `preview_manager` with selected media path and type
3. Implement `set_background()` for image/video files
4. Update config generator to include media paths

### Phase 2: Theme Management
1. Connect ThemesTab signals to load themes
2. Implement theme loading (config → unified widgets)
3. Implement "Save as theme" functionality
4. Generate theme thumbnails

### Phase 3: Path Validation
1. Verify all directories exist
2. Handle missing media files gracefully
3. Copy media files to correct locations when added

## Critical Questions to Resolve

1. **Where are background media files actually stored in installed app?**
   - Check: `~/.config/thermalright-lcd-control/themes/backgrounds/`
   - Check: `/usr/share/thermalright-lcd-control/themes/backgrounds/`

2. **How are media file paths stored in config?**
   - Absolute paths? Relative paths? Paths with variables?

3. **Does service support image/video backgrounds?**
   - Yes, based on `BackgroundType` enum: IMAGE, VIDEO, GIF
   - Need to verify `frame_manager` handles these types

4. **Theme file format compatibility?**
   - Are theme YAML files compatible with current config format?
   - Need to test loading existing theme files