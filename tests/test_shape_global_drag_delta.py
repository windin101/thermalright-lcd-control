from PySide6.QtCore import QPoint


def test_global_delta_drag_calculation():
    # Simulate a widget at origin (100, 100), user presses at global (200, 250)
    orig_pos = QPoint(100, 100)
    start_global = QPoint(200, 250)
    # User moves cursor to (225, 270)
    new_global = QPoint(225, 270)
    delta = new_global - start_global
    new_pos = QPoint(orig_pos.x() + delta.x(), orig_pos.y() + delta.y())
    assert new_pos.x() == 125
    assert new_pos.y() == 120
