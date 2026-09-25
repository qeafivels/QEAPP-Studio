"""Original compact code editor chrome: line numbers, current-line cue, Go to line."""
from __future__ import annotations
from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import QColor, QPainter, QTextCursor, QTextFormat
from PySide6.QtWidgets import QPlainTextEdit, QTextEdit, QWidget

class _Gutter(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.gutter_width(), 0)

    def paintEvent(self, event):
        self.editor.draw_gutter(event)

class EditorBase(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.gutter = _Gutter(self)
        self.blockCountChanged.connect(self._margin_changed)
        self.updateRequest.connect(self._update_gutter)
        self.cursorPositionChanged.connect(self._highlight_line)
        self._margin_changed()
        self._highlight_line()

    def gutter_width(self):
        digits = len(str(max(1, self.blockCount())))
        return 13 + self.fontMetrics().horizontalAdvance('9') * max(2, digits)

    def _margin_changed(self, *_):
        self.setViewportMargins(self.gutter_width(), 0, 0, 0)

    def _update_gutter(self, rect, dy):
        if dy:
            self.gutter.scroll(0, dy)
        else:
            self.gutter.update(0, rect.y(), self.gutter.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._margin_changed()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        area = self.contentsRect()
        self.gutter.setGeometry(QRect(area.left(), area.top(), self.gutter_width(), area.height()))

    def draw_gutter(self, event):
        painter = QPainter(self.gutter)
        painter.fillRect(event.rect(), QColor('#101a2e'))
        block = self.firstVisibleBlock()
        n = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                current = self.textCursor().blockNumber() == n
                painter.setPen(QColor('#c6bcff') if current else QColor('#687795'))
                painter.drawText(0, top, self.gutter.width()-6, self.fontMetrics().height(),
                                 Qt.AlignRight, str(n+1))
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            n += 1

    def _highlight_line(self):
        if self.isReadOnly():
            return
        selected = QTextEdit.ExtraSelection()
        selected.format.setBackground(QColor('#202b45'))
        selected.format.setProperty(QTextFormat.FullWidthSelection, True)
        selected.cursor = self.textCursor()
        selected.cursor.clearSelection()
        self.setExtraSelections([selected])
        self.gutter.update()

    def goto(self, line: int, column: int = 1):
        if not 1 <= line <= self.blockCount() or column < 1:
            return False
        block = self.document().findBlockByNumber(line-1)
        cursor = QTextCursor(block)
        cursor.setPosition(block.position() + min(column-1, max(0, block.length()-1)))
        self.setTextCursor(cursor)
        self.centerCursor()
        self.setFocus()
        return True
