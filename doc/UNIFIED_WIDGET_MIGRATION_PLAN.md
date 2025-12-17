# Unified Widget Migration Plan

## Current State Analysis

### Legacy System (Working)
- **main_window.py**: 557 lines, clean, working
- **Widgets**: `DateWidget`, `TimeWidget`, `MetricWidget` from `draggable_widget.py`
- **Service Integration**: Working USB service communication
- **Config Generation**: Working YAML format that service understands
- **GUI**: Functional with drag-and-drop, property editing

### Unified Widget System (Developed)
- **UnifiedGraphicsView**: Central QGraphicsView for all widgets
- **Widget Types**: Date, Time, Metric, Text, BarGraph, CircularGraph, Shape
- **Adapter**: `UnifiedToDisplayAdapter` converts to display configs
- **Integration**: `unified_integration.py` bridges GUI and backend
- **Property Editor**: Unified property editing system

## Migration Strategy: Phased Approach

### Phase 1: Foundation Setup (Day 1)
**Goal**: Get unified system running alongside legacy, no breaking changes

1. **Copy unified widget code** to new project:
   - `gui/widgets/unified/` directory
   - `gui/unified_integration.py`
   - `gui/widgets/unified/adapter.py`

2. **Create compatibility layer**:
   - `gui/components/unified_manager.py` - Manages unified system
   - Keep legacy widgets functional during transition

3. **Update main_window.py**:
   - Add unified view as alternative display
   - Add toggle between legacy/unified (hidden flag)
   - Initialize unified system alongside legacy

### Phase 2: Date/Time Widget Migration (Day 2)
**Goal**: Replace legacy DateWidget/TimeWidget with unified versions

1. **Modify `create_overlay_widgets()`**:
   - Create unified date/time widgets instead of legacy
   - Keep same positions and properties
   - Update event handlers to use unified system

2. **Update config generation**:
   - Modify `config_generator.py` to accept unified widgets
   - Or use adapter to convert unified → legacy for config generation
   - Ensure YAML output remains identical

3. **Test**:
   - GUI shows unified date/time widgets
   - Drag-and-drop works
   - Config saves correctly
   - Service receives and displays correctly

### Phase 3: Metric Widget Migration (Day 3)
**Goal**: Replace legacy MetricWidget with unified metric widgets

1. **Create unified metric widgets** for all metric types:
   - CPU temperature, usage, frequency
   - GPU temperature, usage, frequency
   - Support labels, units, positioning

2. **Update controls manager**:
   - Metric controls work with unified widgets
   - Property editing uses unified property editor

3. **Test metric functionality**:
   - Live metric updates
   - Config persistence
   - USB display updates

### Phase 4: Advanced Widget Migration (Day 4-5)
**Goal**: Add new widget types not in legacy system

1. **Text widgets**: Custom text display
2. **Graph widgets**: Bar graphs, circular graphs
3. **Shape widgets**: Rectangles, circles, rounded rectangles

2. **Update GUI controls**:
   - Add palette for new widget types
   - Property editing for new widget types

### Phase 5: Legacy Code Removal (Day 6)
**Goal**: Remove all legacy widget code

1. **Remove `draggable_widget.py`**
2. **Remove legacy widget references** from:
   - `main_window.py`
   - `controls_manager.py`
   - `config_generator.py`
3. **Clean up compatibility layer**
4. **Final testing**: Full regression test

### Phase 6: Enhancement (Day 7+)
**Goal**: Add new features enabled by unified system

1. **Layout management**: Save/load widget layouts
2. **Advanced properties**: More customization options
3. **Widget groups**: Group operations
4. **Alignment tools**: Grid, distribute, align
5. **Z-ordering**: Layer management

## Technical Implementation Details

### File Structure After Migration
```
src/thermalright_lcd_control/gui/
├── main_window.py              # Updated to use unified system
├── components/
│   ├── config_generator.py     # Updated for unified widgets
│   ├── controls_manager.py     # Updated for unified widgets
│   ├── preview_manager.py      # Unchanged (already uses adapter)
│   └── unified_manager.py      # NEW: Manages unified system
├── widgets/
│   ├── unified/                # Unified widget system
│   │   ├── base.py
│   │   ├── text_widgets.py
│   │   ├── metric_widgets.py
│   │   ├── graph_widgets.py
│   │   ├── shape_widgets.py
│   │   ├── property_editor.py
│   │   ├── layout_manager.py
│   │   └── adapter.py
│   └── widget_palette.py       # Updated for unified widgets
└── unified_integration.py      # Integration layer
```

### Key Integration Points

1. **Widget Creation**:
   ```python
   # Old:
   self.date_widget = DateWidget(self.preview_widget)
   
   # New:
   self.unified_view.create_date_widget("date", x, y, width, height, ...)
   ```

2. **Config Generation**:
   ```python
   # Use adapter to convert unified widgets to display configs
   configs = UnifiedToDisplayAdapter.get_all_configs_from_view(
       self.unified_view, self.preview_scale
   )
   # Pass to preview_manager
   self.preview_manager.update_widget_configs(**configs)
   ```

3. **Property Editing**:
   ```python
   # Unified property editor handles all widget types
   self.property_editor = PropertyEditor()
   self.property_editor.edit_widget(unified_widget)
   ```

### Risk Mitigation

1. **Backward Compatibility**:
   - Keep legacy system working during transition
   - Feature flag to switch between systems
   - Rollback plan if issues arise

2. **Config Format Stability**:
   - Ensure YAML output matches service expectations
   - Test with existing service before removing legacy
   - Validate config files before and after migration

3. **Testing Strategy**:
   - Unit tests for unified widgets
   - Integration tests for config generation
   - Manual testing of USB service integration
   - Regression testing of all legacy features

## Success Criteria

1. ✅ All existing features work with unified system
2. ✅ USB service receives and displays configs correctly
3. ✅ Config files are backward compatible
4. ✅ Performance equal or better than legacy
5. ✅ Codebase is cleaner and more maintainable
6. ✅ New widget types can be added easily

## Timeline Estimate

- **Phase 1-2**: 3 days (get basic unified system working)
- **Phase 3**: 2 days (metric widgets)
- **Phase 4**: 2 days (new widget types)
- **Phase 5**: 1 day (cleanup)
- **Phase 6**: Ongoing (enhancements)

**Total**: 8 days for complete migration

## Next Steps

1. **Start Phase 1**: Copy unified code to new project
2. **Create compatibility layer**
3. **Test that legacy system still works**
4. **Begin Phase 2**: Date/Time widget migration

## Notes

- Keep legacy folder as reference/backup
- Document any differences in behavior
- Maintain git commits for each phase
- Test after each phase before proceeding
