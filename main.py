# Backup created on 2025-09-16
# Original file saved as: main_backup_20250916.py

import sys
import os
import logging
import base64
import io
from datetime import datetime, timedelta

# PyQt5 Imports
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, 
    QHBoxLayout, QListWidget, QListWidgetItem, QTextEdit, QLabel, 
    QPushButton, QInputDialog, QMessageBox, QSystemTrayIcon, QMenu,
    QSplitter, QLineEdit, QComboBox, QDateEdit, QAction, QFileDialog,
    QStackedWidget, QScrollArea, QToolTip, QFontDialog, QColorDialog, QStyle, QCheckBox, QDialog, QDialogButtonBox
)
from PyQt5.QtCore import Qt, QTimer, QSize, QMimeData, QDate, QBuffer, QRect
from PyQt5.QtGui import QIcon, QPixmap, QImage, QClipboard, QCursor, QFont, QColor, QPalette, QGuiApplication
import ctypes
from ctypes import wintypes

# Third-party imports
import pyperclip
from PIL import ImageGrab, Image
import pytz

import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# Local imports
from database import Database
from world_clock_tab_pyqt import WorldClockTab as WCNewTab
from ocr_utils import ocr_image, OCRPreprocessOptions

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('clip_snippet_manager.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SnippetsTab(QWidget):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.current_snippet_id = None
        self.init_ui()
        self.load_categories()
        self.load_snippets()
        
    def init_ui(self):
        layout = QHBoxLayout()
        
        # Left side: Snippet list and controls
        left_panel = QVBoxLayout()
        
        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search snippets...")
        self.search_box.textChanged.connect(self.on_search)
        left_panel.addWidget(self.search_box)
        
        # Categories + Manage button
        cat_row = QHBoxLayout()
        self.category_combo = QComboBox()
        self.category_combo.currentIndexChanged.connect(lambda: self.load_snippets())
        cat_row.addWidget(self.category_combo)
        self.manage_cats_btn = QPushButton("Manage…")
        self.manage_cats_btn.setToolTip("Rename or delete categories")
        self.manage_cats_btn.clicked.connect(self.manage_categories)
        cat_row.addWidget(self.manage_cats_btn)
        left_panel.addLayout(cat_row)
        
        # Snippets list
        self.snippets_list = QListWidget()
        self.snippets_list.itemClicked.connect(self.on_snippet_selected)
        self.snippets_list.itemDoubleClicked.connect(self.on_snippet_double_clicked)
        left_panel.addWidget(self.snippets_list)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Add")
        self.add_btn.clicked.connect(self.add_snippet)
        self.edit_btn = QPushButton("Edit")
        self.edit_btn.clicked.connect(self.edit_snippet)
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.delete_snippet)
        
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.delete_btn)
        left_panel.addLayout(btn_layout)
        
        # Right side: Preview/Edit
        right_panel = QVBoxLayout()
        self.preview_label = QLabel("Preview")
        right_panel.addWidget(self.preview_label)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        right_panel.addWidget(self.preview_text)
        
        # Add panels to splitter
        splitter = QSplitter(Qt.Horizontal)
        
        left_widget = QWidget()
        left_widget.setLayout(left_panel)
        splitter.addWidget(left_widget)
        
        right_widget = QWidget()
        right_widget.setLayout(right_panel)
        splitter.addWidget(right_widget)
        
        splitter.setSizes([300, 500])
        
        main_layout = QHBoxLayout()
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)
        
    def load_categories(self):
        self.category_combo.clear()
        self.category_combo.addItem("All Categories", "")
        for category in self.db.get_snippet_categories():
            self.category_combo.addItem(category, category)
        # Keep selection stable if possible
        try:
            # If current selection exists, keep it
            idx = self.category_combo.findData(self.category_combo.currentData())
            if idx >= 0:
                self.category_combo.setCurrentIndex(idx)
        except Exception:
            pass
            
    def load_snippets(self, search_term=None):
        import time
        start_time = time.time()
        
        self.snippets_list.clear()
        category = self.category_combo.currentData()
        
        # Convert empty string to None for "All Categories"
        if category == "":
            category = None
        
        if search_term:
            # Search within the current category filter
            snippets = self.db.search_snippets(search_term, category)
        else:
            # Apply category filter only
            snippets = self.db.get_all_snippets(category)
            
        for snippet in snippets:
            item = QListWidgetItem(snippet['title'])
            item.setData(Qt.UserRole, snippet['id'])
            self.snippets_list.addItem(item)
            
        end_time = time.time()
        ui_time = (end_time - start_time) * 1000  # Convert to milliseconds
        print(f"PERF: load_snippets UI - {len(snippets)} items displayed in {ui_time:.2f}ms")
                
    def on_search(self, text):
        if text.strip():
            # Search with text, ignore category filter for now
            self.load_snippets(text)
        else:
            # No search text, apply category filter
            self.load_snippets()
        
    def on_snippet_selected(self, item):
        snippet_id = item.data(Qt.UserRole)
        snippet = self.db.get_snippet(snippet_id)
        if snippet:
            self.current_snippet_id = snippet_id
            self.preview_text.setPlainText(snippet['content'])
            
    def on_snippet_double_clicked(self, item):
        snippet_id = item.data(Qt.UserRole)
        snippet = self.db.get_snippet(snippet_id)
        if snippet:
            pyperclip.copy(snippet['content'])
            
    def _choose_category_dialog(self, current_category=""):
        """Dialog to choose existing category or create new one"""
        dlg = QDialog(self)
        dlg.setWindowTitle("Choose Category")
        layout = QVBoxLayout(dlg)
        
        # Label
        label = QLabel("Select a category or add a new one:")
        layout.addWidget(label)
        
        # Combo box with existing categories
        combo = QComboBox()
        categories = self.db.get_snippet_categories()
        combo.addItem("No Category", "")
        for cat in categories:
            combo.addItem(cat, cat)
        combo.addItem("Add new…", "__new__")
        
        # Set current selection
        if current_category and current_category in categories:
            combo.setCurrentText(current_category)
        else:
            combo.setCurrentText("No Category")
            
        layout.addWidget(combo)
        
        # New category input (initially hidden)
        new_cat_widget = QWidget()
        new_cat_layout = QHBoxLayout(new_cat_widget)
        new_cat_layout.addWidget(QLabel("New category:"))
        new_cat_input = QLineEdit()
        new_cat_layout.addWidget(new_cat_input)
        layout.addWidget(new_cat_widget)
        new_cat_widget.hide()
        
        # Show/hide new category input based on combo selection
        def on_combo_changed():
            if combo.currentData() == "__new__":
                new_cat_widget.show()
                new_cat_input.setFocus()
            else:
                new_cat_widget.hide()
        combo.currentIndexChanged.connect(on_combo_changed)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        layout.addWidget(buttons)
        
        # Show dialog
        if dlg.exec_() == QDialog.Accepted:
            if combo.currentData() == "__new__":
                new_cat = new_cat_input.text().strip()
                return new_cat if new_cat else ""
            else:
                return combo.currentData()
        return None
            
    def add_snippet(self):
        title, ok = QInputDialog.getText(self, 'Add Snippet', 'Enter snippet title:')
        if ok and title:
            content, ok = QInputDialog.getMultiLineText(self, 'Add Snippet', 'Enter snippet content:')
            if ok and content:
                category = self._choose_category_dialog()
                if category is not None:
                    self.db.add_snippet(title, content, category)
                    self.load_snippets()
                    self.load_categories()
                    
    def edit_snippet(self):
        if not self.current_snippet_id:
            return
            
        snippet = self.db.get_snippet(self.current_snippet_id)
        if not snippet:
            return
            
        title, ok = QInputDialog.getText(self, 'Edit Snippet', 'Edit title:', text=snippet['title'])
        if ok and title:
            content, ok = QInputDialog.getMultiLineText(
                self, 'Edit Snippet', 'Edit content:', text=snippet['content']
            )
            if ok and content:
                category = self._choose_category_dialog(snippet.get('category', ''))
                if category is not None:
                    self.db.update_snippet(self.current_snippet_id, title, content, category)
                    self.load_snippets()
                    self.load_categories()
                    
    def delete_snippet(self):
        if not self.current_snippet_id:
            return
            
        reply = QMessageBox.question(
            self, 'Confirm Delete', 
            'Are you sure you want to delete this snippet?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.db.delete_snippet(self.current_snippet_id)
            self.current_snippet_id = None
            self.preview_text.clear()
            self.load_snippets()
            self.load_categories()

    def manage_categories(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Manage Categories")
        v = QVBoxLayout(dlg)
        info = QLabel("Select a category to Rename or Delete. Deleting will clear the category on its snippets.")
        info.setWordWrap(True)
        v.addWidget(info)
        self.cat_list = QListWidget()
        for c in self.db.get_snippet_categories():
            self.cat_list.addItem(c)
        v.addWidget(self.cat_list)
        btns = QHBoxLayout()
        btn_rename = QPushButton("Rename…")
        btn_delete = QPushButton("Delete…")
        btn_close = QPushButton("Close")
        btns.addWidget(btn_rename)
        btns.addWidget(btn_delete)
        btns.addStretch()
        btns.addWidget(btn_close)
        v.addLayout(btns)

        def do_rename():
            item = self.cat_list.currentItem()
            if not item:
                return
            old = item.text()
            new, ok = QInputDialog.getText(self, 'Rename Category', 'New name:', text=old)
            if not ok:
                return
            new = new.strip()
            if not new:
                QMessageBox.warning(self, 'Invalid', 'Category name cannot be empty.')
                return
            if new == old:
                return
            changed = self.db.rename_snippet_category(old, new)
            if changed >= 0:
                # Refresh UI
                self.load_categories()
                self.load_snippets()
                # Update dialog list
                self.cat_list.clear()
                for c in self.db.get_snippet_categories():
                    self.cat_list.addItem(c)

        def do_delete():
            item = self.cat_list.currentItem()
            if not item:
                return
            cat = item.text()
            reply = QMessageBox.question(
                self,
                'Delete Category',
                f'Remove category "{cat}" from all snippets?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
            affected = self.db.delete_snippet_category(cat)
            # Refresh UI
            self.load_categories()
            self.load_snippets()
            # Update dialog list
            self.cat_list.clear()
            for c in self.db.get_snippet_categories():
                self.cat_list.addItem(c)

        btn_rename.clicked.connect(do_rename)
        btn_delete.clicked.connect(do_delete)
        btn_close.clicked.connect(dlg.accept)
        dlg.exec_()


class ClipboardTab(QWidget):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.current_item_id = None
        self.last_refresh = None
        self._ocr_callback = None
        self.init_ui()
        self.load_clipboard_items()
        
    def refresh_data(self):
        """Force refresh all data"""
        self.load_dates()
        self.load_clipboard_items()
        
    def on_filter_changed(self):
        """Handle filter changes"""
        self.load_clipboard_items()
        
    def on_search(self, text):
        """Handle search text changes with debounce"""
        if hasattr(self, '_search_timer'):
            self._search_timer.stop()
            
        if not hasattr(self, '_search_timer'):
            self._search_timer = QTimer()
            self._search_timer.setSingleShot(True)
            self._search_timer.timeout.connect(
                lambda: self.load_clipboard_items(self.search_edit.text().strip())
            )
            
        self._search_timer.start(300)  # 300ms delay
        
    def load_dates(self):
        """Deprecated: no-op after switching to calendar date selector."""
        return
                
    def load_clipboard_items(self, search_term=None):
        """Load clipboard items with current filters"""
        import time
        start_time = time.time()
        
        self.items_list.clear()
        
        # Determine date filter and search scope
        search_all_dates = self.search_all_dates_cb.isChecked()
        
        if search_term and search_term.strip():
            # When searching, use search_all_dates setting
            date_filter = None
        else:
            # For non-search, use date filter as before
            date_filter = None if self.all_dates_cb.isChecked() else self.date_edit.date().toString('yyyy-MM-dd')
        
        content_type = self.type_combo.currentData()
        
        items = self.db.get_clipboard_items(
            start_date=date_filter if date_filter else None,
            content_type=content_type,
            search_term=search_term if search_term else None,
            search_all_dates=search_all_dates
        )
        
        for item in items:
            preview = item.get('preview', 'No preview')
            if len(preview) > 50:  # Shorter preview to make room for timestamp
                preview = preview[:47] + '...'
            
            # Format timestamp
            timestamp = item.get('created_at', '')
            if timestamp:
                try:
                    # Convert to local datetime object for formatting
                    dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                    timestamp = dt.strftime('%Y-%m-%d %H:%M:%S')
                except (ValueError, TypeError):
                    timestamp = ''
            
            # Create list item with type, preview and timestamp
            item_text = f"[{item['content_type'].capitalize()}] {preview.ljust(50)} {timestamp}"
            list_item = QListWidgetItem(item_text)
            list_item.setData(Qt.UserRole, item['id'])
            self.items_list.addItem(list_item)
        
        # Auto-select first item if available
        if self.items_list.count() > 0:
            self.items_list.setCurrentRow(0)
            
        end_time = time.time()
        ui_time = (end_time - start_time) * 1000  # Convert to milliseconds
        print(f"PERF: load_clipboard_items UI - {len(items)} items displayed in {ui_time:.2f}ms")
            
    def on_item_selected(self, item):
        """Handle item selection"""
        item_id = item.data(Qt.UserRole)
        self.current_item_id = item_id
        
        # Get item details from database
        items = self.db.get_clipboard_items()
        item_data = next((i for i in items if i['id'] == item_id), None)
        
        if not item_data:
            return
            
        content_type = item_data['content_type']
        # Enable OCR button only for images
        if hasattr(self, 'ocr_btn'):
            self.ocr_btn.setEnabled(content_type == 'image')
        
        if content_type == 'text':
            self.text_preview.setPlainText(item_data.get('content_text', ''))
            self.preview_stack.setCurrentIndex(0)  # Show text preview
        elif content_type == 'image':
            try:
                image_data = item_data.get('content_data')
                if image_data:
                    image = QImage.fromData(image_data)
                    if not image.isNull():
                        pixmap = QPixmap.fromImage(image)
                        
                        # Scale image to fit preview while maintaining aspect ratio
                        preview_size = self.image_preview.size()
                        scaled_pixmap = pixmap.scaled(
                            preview_size, 
                            Qt.KeepAspectRatio, 
                            Qt.SmoothTransformation
                        )
                        
                        self.image_preview.setPixmap(scaled_pixmap)
                        self.preview_stack.setCurrentIndex(1)  # Show image preview
                        return
            except Exception as e:
                logger.error(f"Error loading image preview: {e}")
                self.text_preview.setPlainText(f"[Error loading image: {str(e)}]")
                self.preview_stack.setCurrentIndex(0)  # Show text preview
        else:
            self.text_preview.setPlainText("Preview not available")
            self.preview_stack.setCurrentIndex(0)  # Show text preview
            
    def on_item_double_clicked(self, item):
        """Handle double click to copy to clipboard"""
        self.copy_to_clipboard()
    
    def set_ocr_callback(self, cb):
        """Set a callback callable(text: str) to receive OCR results."""
        self._ocr_callback = cb
    
    def extract_text(self):
        """Run OCR on selected image item and send text to OCR tab via callback."""
        if not self.current_item_id:
            return
        # Fetch the item again to ensure we have content_data
        items = self.db.get_clipboard_items()
        item_data = next((i for i in items if i['id'] == self.current_item_id), None)
        if not item_data or item_data.get('content_type') != 'image':
            QMessageBox.information(self, 'OCR', 'Please select an image item.')
            return
        try:
            img_bytes = item_data.get('content_data')
            if not img_bytes:
                raise ValueError('No image data found for this item')
            from io import BytesIO
            pil_img = Image.open(BytesIO(img_bytes))
            # Reasonable default options; can be made configurable later
            opt = OCRPreprocessOptions(upscale=1.5, grayscale=True, auto_contrast=True, sharpen=True)
            text = ocr_image(pil_img, lang='eng', opt=opt)
            if self._ocr_callback:
                self._ocr_callback(text)
        except Exception as e:
            QMessageBox.critical(self, 'OCR Error', f'Failed to extract text: {e}')
        
    def copy_to_clipboard(self):
        """Copy selected item to clipboard"""
        if not self.current_item_id:
            return
            
        items = self.db.get_clipboard_items()
        item_data = next((i for i in items if i['id'] == self.current_item_id), None)
        
        if not item_data:
            return
            
        clipboard = QApplication.clipboard()
        content_type = item_data['content_type']
        
        try:
            if content_type == 'text':
                clipboard.setText(item_data.get('content_text', ''))
            elif content_type == 'image':
                image_data = item_data.get('content_data')
                if image_data:
                    image = QImage.fromData(image_data)
                    if not image.isNull():
                        clipboard.setImage(image)
                        
            # Show brief notification
            QToolTip.showText(
                QCursor.pos(),
                f"{content_type.capitalize()} copied to clipboard",
                self,
                self.rect(),
                1000
            )
            
        except Exception as e:
            logger.error(f"Error copying to clipboard: {e}")
            QMessageBox.critical(self, 'Error', f'Failed to copy to clipboard: {str(e)}')
            
    def delete_item(self):
        """Delete the selected item"""
        if not self.current_item_id:
            return
            
        reply = QMessageBox.question(
            self, 'Confirm Delete', 
            'Are you sure you want to delete this item?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Delete from database
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM clipboard_history WHERE id = ?', (self.current_item_id,))
                conn.commit()
            
            # Refresh the list
            self.current_item_id = None
            self.load_clipboard_items()
            
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Filter controls
        filter_layout = QHBoxLayout()
        
        # Date filter (calendar + Today + All)
        filter_layout.addWidget(QLabel("Date:"))
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat('yyyy-MM-dd')
        self.date_edit.dateChanged.connect(self.on_filter_changed)
        filter_layout.addWidget(self.date_edit)
        today_btn = QPushButton("Latest")
        today_btn.setToolTip("Jump to the latest (today)")
        today_btn.clicked.connect(lambda: (self.date_edit.setDate(QDate.currentDate()), self.on_filter_changed()))
        filter_layout.addWidget(today_btn)
        self.all_dates_cb = QCheckBox("All dates")
        # Default to unchecked so only today's clips show on launch
        self.all_dates_cb.setChecked(False)
        self.all_dates_cb.toggled.connect(self.on_filter_changed)
        filter_layout.addWidget(self.all_dates_cb)
        
        # Content type filter
        filter_layout.addWidget(QLabel("Type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItem("All Types", "all")
        self.type_combo.addItem("Text", "text")
        self.type_combo.addItem("Images", "image")
        self.type_combo.currentIndexChanged.connect(self.on_filter_changed)
        filter_layout.addWidget(self.type_combo)
        
        # Search scope options
        self.search_all_dates_cb = QCheckBox("Search All Dates")
        self.search_all_dates_cb.setToolTip("Search across entire database instead of last 30 days")
        self.search_all_dates_cb.setChecked(False)
        self.search_all_dates_cb.toggled.connect(self.on_filter_changed)
        filter_layout.addWidget(self.search_all_dates_cb)
        
        # Search box
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search...")
        # Show a built-in clear (x) button
        try:
            self.search_edit.setClearButtonEnabled(True)
        except Exception:
            pass
        self.search_edit.textChanged.connect(self.on_search)
        filter_layout.addWidget(self.search_edit)
        
        # Removed standalone Refresh button; use 'Latest' to jump to today and reload
        
        layout.addLayout(filter_layout)
        
        # Split view
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - List of items
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        
        self.items_list = QListWidget()
        self.items_list.itemClicked.connect(self.on_item_selected)
        # Ensure keyboard navigation (Up/Down) previews current item
        self.items_list.currentItemChanged.connect(lambda current, prev: self.on_item_selected(current) if current else None)
        self.items_list.itemDoubleClicked.connect(self.on_item_double_clicked)
        left_layout.addWidget(self.items_list)
        
        left_panel.setLayout(left_layout)
        splitter.addWidget(left_panel)
        
        # Right panel - Preview
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        
        # Stacked widget for different preview types
        self.preview_stack = QStackedWidget()
        
        # Text preview
        self.text_preview = QTextEdit()
        self.text_preview.setReadOnly(True)
        self.preview_stack.addWidget(self.text_preview)
        
        # Image preview
        self.image_preview = QLabel()
        self.image_preview.setAlignment(Qt.AlignCenter)
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.image_preview)
        scroll_area.setWidgetResizable(True)
        self.preview_stack.addWidget(scroll_area)
        
        # Empty preview
        empty_preview = QLabel("Select an item to preview")
        empty_preview.setAlignment(Qt.AlignCenter)
        empty_preview.setStyleSheet("color: gray; font-style: italic;")
        self.preview_stack.addWidget(empty_preview)
        
        self.preview_stack.setCurrentIndex(2)  # Show empty preview by default
        right_layout.addWidget(self.preview_stack)
        
        # Action buttons
        btn_layout = QHBoxLayout()
        self.copy_btn = QPushButton("Copy to Clipboard")
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.delete_item)
        self.ocr_btn = QPushButton("Extract Text (OCR)")
        self.ocr_btn.setToolTip("Run OCR on selected image and show text")
        self.ocr_btn.setEnabled(False)
        self.ocr_btn.clicked.connect(self.extract_text)
        
        btn_layout.addWidget(self.copy_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.ocr_btn)
        right_layout.addLayout(btn_layout)
        
        right_panel.setLayout(right_layout)
        splitter.addWidget(right_panel)
        
        # Set splitter sizes
        splitter.setSizes([self.width() // 3, 2 * self.width() // 3])
        
        layout.addWidget(splitter)
        self.setLayout(layout)


class OCRTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.text = QTextEdit()
        self.text.setReadOnly(False)
        layout.addWidget(QLabel("Extracted Text:"))
        layout.addWidget(self.text)
        # Quick actions
        actions = QHBoxLayout()
        copy_btn = QPushButton("Copy Text")
        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(self.text.toPlainText()))
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.text.clear)
        actions.addWidget(copy_btn)
        actions.addWidget(clear_btn)
        actions.addStretch()
        layout.addLayout(actions)
        self.setLayout(layout)

    def set_text(self, value: str):
        self.text.setPlainText(value or "")


class WorldClockTab(QWidget):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.timer = QTimer(self)
        self.timer.setInterval(1000)  # update every second
        self.timer.timeout.connect(self.update_times)
        # Load display prefs
        self.show_seconds = (self.db.get_setting('wc_show_seconds', '1') == '1')
        self.use_24h = (self.db.get_setting('wc_use_24h', '1') == '1')
        self.init_ui()
        self.load_clocks()
        self.timer.start()
 
    def init_ui(self):
        layout = QVBoxLayout()
 
        # Predefined controls
        top_controls = QHBoxLayout()
        self.predefined_combo = QComboBox()
        self.predefined_combo.setMinimumWidth(250)
        self._populate_predefined_timezones()
        add_pre_btn = QPushButton("Add Predefined")
        add_pre_btn.clicked.connect(self.add_predefined)
        top_controls.addWidget(QLabel("Quick Add:"))
        top_controls.addWidget(self.predefined_combo)
        top_controls.addWidget(add_pre_btn)
        top_controls.addStretch()
        layout.addLayout(top_controls)
 
        # Display options
        display_controls = QHBoxLayout()
        self.format_btn = QPushButton("Toggle 12/24h")
        self.format_btn.setToolTip("Switch between 12-hour and 24-hour clocks")
        self.format_btn.clicked.connect(self.toggle_24h)
        self.seconds_btn = QPushButton("Toggle Seconds")
        self.seconds_btn.setToolTip("Show or hide seconds in clock display")
        self.seconds_btn.clicked.connect(self.toggle_seconds)
        display_controls.addWidget(self.format_btn)
        display_controls.addWidget(self.seconds_btn)
        display_controls.addStretch()
        layout.addLayout(display_controls)
 
        # List of clocks
        self.clock_list = QListWidget()
        self.clock_list.currentItemChanged.connect(self.on_selection_changed)
        layout.addWidget(self.clock_list)
 
        # Buttons
        btns = QHBoxLayout()
        self.add_btn = QPushButton("Add City")
        self.add_btn.clicked.connect(self.add_city)
        self.edit_btn = QPushButton("Edit Selected")
        self.edit_btn.clicked.connect(self.edit_selected)
        self.del_btn = QPushButton("Delete Selected")
        self.del_btn.clicked.connect(self.delete_selected)
        self.toggle_dst_btn = QPushButton("Toggle DST for Selected")
        self.toggle_dst_btn.setToolTip("Enable/disable DST adjustment for this timezone (only if it observes DST)")
        self.toggle_dst_btn.clicked.connect(self.toggle_selected_dst)
        self.toggle_dst_btn.setEnabled(False)
        btns.addWidget(self.add_btn)
        btns.addWidget(self.edit_btn)
        btns.addWidget(self.del_btn)
        btns.addWidget(self.toggle_dst_btn)
 
        layout.addLayout(btns)
        self.setLayout(layout)
 
    def _populate_predefined_timezones(self):
        # Common cities/timezones (IANA)
        predefined = [
            ("UTC", "UTC"),
            ("San Francisco", "America/Los_Angeles"),
            ("Houston", "America/Chicago"),
            ("New York", "America/New_York"),
            ("London", "Europe/London"),
            ("Zurich", "Europe/Zurich"),
            ("Paris", "Europe/Paris"),
            ("Dubai", "Asia/Dubai"),
            ("Mumbai", "Asia/Kolkata"),
            ("Singapore", "Asia/Singapore"),
            ("Hong Kong", "Asia/Hong_Kong"),
            ("Tokyo", "Asia/Tokyo"),
            ("Seoul", "Asia/Seoul"),
            ("Sydney", "Australia/Sydney"),
            ("Auckland", "Pacific/Auckland"),
        ]
        self.predefined_combo.clear()
        for label, tz in predefined:
            self.predefined_combo.addItem(f"{label} — {tz}", (label, tz))
 
    def load_clocks(self):
        self.clock_list.clear()
        for entry in self.db.get_world_clocks():
            city = entry['city']
            tz = entry['timezone']
            use_dst = int(entry.get('use_dst', 1))
            observes = self._timezone_observes_dst(tz)
            item = QListWidgetItem()
            item.setData(Qt.UserRole, entry['id'])
            item.setData(Qt.UserRole + 1, tz)
            item.setData(Qt.UserRole + 2, city)
            item.setData(Qt.UserRole + 3, use_dst)
            item.setData(Qt.UserRole + 4, observes)
            # initial text
            item.setText(self._format_item_text(city, tz, use_dst))
            # Annotate if no DST support
            if not observes:
                item.setToolTip("This timezone does not observe DST")
            self.clock_list.addItem(item)
        self.on_selection_changed(self.clock_list.currentItem(), None)
 
    def update_times(self):
        for i in range(self.clock_list.count()):
            item = self.clock_list.item(i)
            city = item.data(Qt.UserRole + 2)
            tz = item.data(Qt.UserRole + 1)
            use_dst = int(item.data(Qt.UserRole + 3) or 1)
            item.setText(self._format_item_text(city, tz, use_dst))
 
    def _format_item_text(self, city: str, tz_name: str, use_dst: int) -> str:
        try:
            tz = pytz.timezone(tz_name)
            now_tz = datetime.now(tz)
            if not use_dst:
                # Show standard time by subtracting DST delta if any
                try:
                    dst = now_tz.dst() or timedelta(0)
                    now_tz = now_tz - dst
                except Exception:
                    pass
            fmt = '%Y-%m-%d ' + ('%H:%M' if self.use_24h else '%I:%M %p')
            if self.show_seconds:
                fmt = fmt.replace('%M', '%M:%S') if '%S' not in fmt else fmt
            return f"{city} ({tz_name}) — {now_tz.strftime(fmt)}"
        except Exception:
            return f"{city} ({tz_name}) — [Invalid Timezone]"
 
    def _timezone_observes_dst(self, tz_name: str) -> bool:
        try:
            tz = pytz.timezone(tz_name)
            y = datetime.now().year
            winter = tz.localize(datetime(y, 1, 1, 12, 0, 0), is_dst=None)
            summer = tz.localize(datetime(y, 7, 1, 12, 0, 0), is_dst=None)
            return (winter.utcoffset() != summer.utcoffset())
        except Exception:
            return False
 
    def on_selection_changed(self, current: QListWidgetItem, previous: QListWidgetItem):
        if not current:
            self.toggle_dst_btn.setEnabled(False)
            return
        observes = bool(current.data(Qt.UserRole + 4))
        self.toggle_dst_btn.setEnabled(observes)
 
    def add_predefined(self):
        data = self.predefined_combo.currentData()
        if not data:
            return
        city, tz = data
        # default use_dst = 1 if timezone observes DST, else 0
        use_dst = 1 if self._timezone_observes_dst(tz) else 0
        self.db.add_world_clock(city, tz, use_dst)
        self.load_clocks()
 
    def add_city(self):
        # Ask for city name
        city, ok = QInputDialog.getText(self, 'Add City', 'Enter city label (e.g., Tokyo):')
        if not (ok and city.strip()):
            return
        city = city.strip()
 
        # Choose timezone from list
        tz_list = pytz.common_timezones
        tz, ok = QInputDialog.getItem(self, 'Select Timezone', 'Choose timezone:', tz_list, 0, False)
        if not ok:
            return
 
        # Save to DB with default use_dst based on whether zone observes DST
        use_dst = 1 if self._timezone_observes_dst(tz) else 0
        self.db.add_world_clock(city, tz, use_dst)
        self.load_clocks()
 
    def delete_selected(self):
        item = self.clock_list.currentItem()
        if not item:
            return
        clock_id = item.data(Qt.UserRole)
        reply = QMessageBox.question(self, 'Confirm Delete', 'Delete selected city/timezone?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db.delete_world_clock(clock_id)
            self.load_clocks()
 
    def toggle_selected_dst(self):
        item = self.clock_list.currentItem()
        if not item:
            return
        observes = bool(item.data(Qt.UserRole + 4))
        if not observes:
            # Should not be enabled, but guard anyway
            return
        clock_id = int(item.data(Qt.UserRole))
        current_use = int(item.data(Qt.UserRole + 3) or 1)
        new_use = 0 if current_use == 1 else 1
        if self.db.update_world_clock_dst(clock_id, new_use):
            # Reload from DB to avoid UI state drifting and ensure persistence
            self.load_clocks()
 
    def edit_selected(self):
        item = self.clock_list.currentItem()
        if not item:
            return
        clock_id = int(item.data(Qt.UserRole))
        current_city = item.data(Qt.UserRole + 2)
        current_tz = item.data(Qt.UserRole + 1)
        current_use_dst = int(item.data(Qt.UserRole + 3) or 1)
 
        # Edit city
        city, ok = QInputDialog.getText(self, 'Edit City', 'City label:', text=current_city)
        if not ok or not city.strip():
            return
        city = city.strip()
 
        # Edit timezone
        tz_list = pytz.common_timezones
        try:
            idx = tz_list.index(current_tz)
        except ValueError:
            idx = 0
        tz, ok = QInputDialog.getItem(self, 'Edit Timezone', 'Choose timezone:', tz_list, idx, False)
        if not ok:
            return
 
        # Determine if timezone observes DST and allow toggling only if yes
        observes = self._timezone_observes_dst(tz)
        use_dst = current_use_dst
        if observes:
            # Ask to enable/disable DST for this clock
            choice = QMessageBox.question(
                self,
                'DST Setting',
                'Enable DST adjustments for this timezone?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes if current_use_dst == 1 else QMessageBox.No
            )
            use_dst = 1 if choice == QMessageBox.Yes else 0
        else:
            use_dst = 0
 
        if self.db.update_world_clock(clock_id, city, tz, use_dst):
            self.load_clocks()
 
    def toggle_24h(self):
        self.use_24h = not self.use_24h
        self.db.set_setting('wc_use_24h', '1' if self.use_24h else '0')
        self.update_times()
 
    def toggle_seconds(self):
        self.show_seconds = not self.show_seconds
        self.db.set_setting('wc_show_seconds', '1' if self.show_seconds else '0')
        self.update_times()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        # Apply saved Tesseract path early if present
        try:
            saved_tess = self.db.get_setting('tesseract_path', '')
            if saved_tess and os.path.exists(saved_tess):
                pytesseract.pytesseract.tesseract_cmd = saved_tess
        except Exception:
            pass
        # Appearance state
        self.dark_mode_enabled = (self.db.get_setting('app_dark_mode', '1') == '1')
        self.custom_text_color = QColor(self.db.get_setting('app_text_color', '')) if self.db.get_setting('app_text_color', '') else None
        bg_hex = self.db.get_setting('app_bg_color', '')
        self.custom_bg_color = QColor(bg_hex) if bg_hex else None
        font_str = self.db.get_setting('app_font', '')
        self.custom_font = QFont() if font_str else None
        if font_str:
            self.custom_font.fromString(font_str)
        self.init_ui()
        self.setup_system_tray()
        self.setup_clipboard_monitoring()
        # Cleanup old items and VACUUM on startup (one-time per launch)
        self.cleanup_old_items()
        # Try to register native clipboard listener (Windows)
        self._clipboard_listener_registered = False
        try:
            self.register_clipboard_listener()
        except Exception as e:
            logger.warning(f"Could not register native clipboard listener: {e}")
        # Populate launch details in status bar once
        try:
            self.update_launch_details()
        except Exception as e:
            logger.warning(f"Failed to update launch details: {e}")
         
    def init_ui(self):
        self.setWindowTitle('ClipSnippet Manager')
        self.setGeometry(100, 100, 1000, 700)
        # Try to set a custom window icon from assets
        try:
            icon_path_ico = os.path.join('assets', 'app.ico')
            icon_path_png = os.path.join('assets', 'app.png')
            icon = None
            if os.path.exists(icon_path_ico):
                icon = QIcon(icon_path_ico)
            elif os.path.exists(icon_path_png):
                icon = QIcon(icon_path_png)
            if icon is not None and not icon.isNull():
                self.setWindowIcon(icon)
        except Exception:
            pass
         
        # Create tabs
        self.tabs = QTabWidget()
         
        # Snippets tab
        self.snippets_tab = SnippetsTab(self.db)
        self.tabs.addTab(self.snippets_tab, "Snippets")
         
        # Clipboard tab
        self.clipboard_tab = ClipboardTab(self.db)
        self.tabs.addTab(self.clipboard_tab, "Clipboard History")
        # Hook OCR callback from Clipboard tab later after OCR tab is created
 
        # OCR tab
        self.ocr_tab = OCRTab()
        self.tabs.addTab(self.ocr_tab, "OCR")

        # World Clock tab (new implementation)
        self.world_clock_tab = WCNewTab(self.db, dark_mode=self.dark_mode_enabled)
        self.tabs.addTab(self.world_clock_tab, "World Clock")

        # Connect OCR callback now that tab exists
        self.clipboard_tab.set_ocr_callback(self.show_ocr_text)
        # Detect Tesseract availability and set up tab behavior
        self.tesseract_available = self._detect_tesseract()
        self._last_tab_index = self.tabs.currentIndex()
        self.tabs.currentChanged.connect(self.on_tab_changed)
        self.update_ocr_availability_ui()
         
        # Set central widget
        self.setCentralWidget(self.tabs)
         
        # Status bar
        self.statusBar().showMessage('Ready')
        # Persistent launch details on the right
        from PyQt5.QtWidgets import QLabel
        self.details_label = QLabel()
        self.details_label.setStyleSheet("color: gray;")
        self.statusBar().addPermanentWidget(self.details_label)
 
        # Menu bar
        menubar = self.menuBar()
        # Primary menu (renamed from 'View' to 'Menu')
        view_menu = menubar.addMenu("Menu")
        # Retention option under Menu
        retention_action = QAction("Retention...", self)
        retention_action.triggered.connect(self.configure_retention)
        view_menu.addAction(retention_action)
        # Tesseract path chooser under Menu
        tess_action = QAction("Tesseract Path...", self)
        tess_action.setToolTip("Set the path to tesseract.exe to enable OCR")
        tess_action.triggered.connect(self.choose_tesseract_path)
        view_menu.addAction(tess_action)
        # World Clock Integrations under Menu
        url_manager_action = QAction("World Clock Integrations...", self)
        url_manager_action.setToolTip("Manage custom meeting URLs for third-party integrations")
        url_manager_action.triggered.connect(self.open_custom_url_manager)
        view_menu.addAction(url_manager_action)
        
        # Add separator
        view_menu.addSeparator()
        
        # Move Exit under Menu
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close_application)
        view_menu.addAction(exit_action)

        self.dark_mode_action = QAction("Dark Mode", self, checkable=True)
        self.dark_mode_action.setChecked(self.dark_mode_enabled)
        self.dark_mode_action.toggled.connect(self.toggle_dark_mode)
        view_menu.addAction(self.dark_mode_action)

        font_action = QAction("Font...", self)
        font_action.triggered.connect(self.choose_font)
        view_menu.addAction(font_action)

        text_color_action = QAction("Text Color...", self)
        text_color_action.triggered.connect(self.choose_text_color)
        view_menu.addAction(text_color_action)

        bg_color_action = QAction("Background Color...", self)
        bg_color_action.triggered.connect(self.choose_background_color)
        view_menu.addAction(bg_color_action)
        
        # Add About as a separate top-level menu
        about_menu = menubar.addMenu("About")
        about_action = QAction("About SupportHelper", self)
        about_action.triggered.connect(self.show_about_dialog)
        about_menu.addAction(about_action)
 
        # Apply initial appearance
        self.apply_appearance()

    def show_ocr_text(self, text: str):
        try:
            self.ocr_tab.set_text(text)
            # Switch to OCR tab
            idx = self.tabs.indexOf(self.ocr_tab)
            if idx != -1:
                self.tabs.setCurrentIndex(idx)
            self.statusBar().showMessage('OCR extraction complete', 2000)
        except Exception as e:
            logger.error(f"Error showing OCR text: {e}")

    def _detect_tesseract(self) -> bool:
        """Return True if Tesseract OCR is available on this machine."""
        try:
            import shutil
            # If an explicit cmd path is set and exists
            cmd = getattr(pytesseract.pytesseract, 'tesseract_cmd', '')
            if cmd and os.path.exists(cmd):
                return True
            # Otherwise search PATH
            return (shutil.which('tesseract') is not None) or (shutil.which('tesseract.exe') is not None)
        except Exception:
            return False

    def on_tab_changed(self, new_index: int):
        """Intercept switching to OCR tab if Tesseract is missing and revert to previous tab with a message."""
        try:
            if not getattr(self, 'tesseract_available', True):
                if self.tabs.widget(new_index) is self.ocr_tab:
                    QMessageBox.information(
                        self,
                        'OCR Unavailable',
                        'Tesseract OCR was not detected on this system.\n\n'
                        'Please install Tesseract to enable OCR:\n'
                        'https://github.com/tesseract-ocr/tesseract'
                    )
                    # Revert to the previous working tab
                    self.tabs.blockSignals(True)
                    self.tabs.setCurrentIndex(self._last_tab_index)
                    self.tabs.blockSignals(False)
                    return
            # Update last index if navigation went through
            self._last_tab_index = new_index
        except Exception:
            # Best-effort; if anything goes wrong, do not block navigation
            self._last_tab_index = new_index

    def choose_tesseract_path(self):
        """Allow user to browse to tesseract.exe, persist it, and update OCR availability."""
        try:
            start_dir = os.path.dirname(getattr(pytesseract.pytesseract, 'tesseract_cmd', '') or r"C:\\Program Files\\Tesseract-OCR")
        except Exception:
            start_dir = r"C:\\Program Files\\Tesseract-OCR"
        path, _ = QFileDialog.getOpenFileName(self, 'Select tesseract.exe', start_dir, 'Executable (tesseract.exe)')
        if not path:
            return
        if not os.path.basename(path).lower().startswith('tesseract'):
            QMessageBox.warning(self, 'Invalid File', 'Please select tesseract.exe')
            return
        try:
            pytesseract.pytesseract.tesseract_cmd = path
            # Persist in DB
            self.db.set_setting('tesseract_path', path)
            # Re-evaluate availability and update UI
            self.tesseract_available = self._detect_tesseract()
            self.update_ocr_availability_ui()
            if self.tesseract_available:
                QMessageBox.information(self, 'OCR Ready', 'Tesseract detected. OCR features are now enabled.')
            else:
                QMessageBox.warning(self, 'OCR Unavailable', 'Tesseract still not detected. Please verify the path or installation.')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to set Tesseract path: {e}')

    def open_custom_url_manager(self):
        """Open the Custom URL Manager dialog"""
        from world_clock_tab_pyqt import CustomUrlManagerDialog
        dialog = CustomUrlManagerDialog(self.world_clock_tab)
        dialog.exec_()

    def update_ocr_availability_ui(self):
        """Enable/disable OCR affordances based on availability."""
        try:
            if hasattr(self.clipboard_tab, 'ocr_btn'):
                self.clipboard_tab.ocr_btn.setEnabled(bool(self.tesseract_available))
                if self.tesseract_available:
                    self.clipboard_tab.ocr_btn.setToolTip('Run OCR on selected image and show text')
                else:
                    self.clipboard_tab.ocr_btn.setToolTip('Install or set Tesseract path to enable OCR (Menu → Tesseract Path...)')
        except Exception:
            pass
 
    def setup_system_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        # Set a reliable tray icon with fallback
        icon = QIcon.fromTheme('edit-copy')
        if icon.isNull():
            icon = self.style().standardIcon(QStyle.SP_ComputerIcon)
        self.tray_icon.setIcon(icon)
         
        # Create menu
        tray_menu = QMenu()
         
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
         
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close_application)
        tray_menu.addAction(exit_action)
         
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
         
    def setup_clipboard_monitoring(self):
        self.clipboard = QApplication.clipboard()
        try:
            self.clipboard.dataChanged.disconnect()
        except Exception:
            pass
        self.clipboard.dataChanged.connect(self.on_clipboard_changed)
        self.last_clip = None
        # Rebind after app state changes (e.g., resume)
        try:
            QGuiApplication.instance().applicationStateChanged.disconnect(self.on_app_state_changed)
        except Exception:
            pass
        QGuiApplication.instance().applicationStateChanged.connect(self.on_app_state_changed)
        
    def on_clipboard_changed(self):
        try:
            # Get clipboard data
            mime_data = self.clipboard.mimeData()
            
            if mime_data.hasImage():
                # Handle image
                image = self.clipboard.image()
                if not image.isNull():
                    # Convert to bytes for comparison
                    buffer = QBuffer()
                    buffer.open(QBuffer.ReadWrite)
                    image.save(buffer, 'PNG')
                    current_image_data = buffer.data()
                    
                    # Get the most recent image from database
                    recent_items = self.db.get_clipboard_items(content_type='image', limit=1)
                    if recent_items:
                        recent_data = recent_items[0].get('content_data')
                        if recent_data and recent_data == current_image_data:
                            return  # Skip if same as last image
                    
                    # Create preview
                    preview_pixmap = QPixmap.fromImage(image)
                    preview_pixmap = preview_pixmap.scaled(
                        100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation
                    )
                    
                    # Save to database
                    self.db.add_clipboard_item(
                        content_type='image',
                        content_data=current_image_data,
                        content_text='[Image]',
                        preview='[Image]'
                    )
                    
                    logger.info('Image captured to clipboard history')
                    
            elif mime_data.hasText():
                # Handle text
                text = mime_data.text().strip()
                
                # Skip if text is too short or same as last clip
                if len(text) < 3 or text == self.last_clip:
                    return
                    
                self.last_clip = text
                
                # Create preview (first 100 chars)
                preview = text[:100]
                if len(text) > 100:
                    preview += '...'
                
                # Save to database
                self.db.add_clipboard_item(
                    content_type='text',
                    content_text=text,
                    preview=preview
                )
                
                logger.info('Text captured to clipboard history')
                
            # Refresh clipboard tab UI only if visible
            if hasattr(self, 'clipboard_tab') and self.clipboard_tab.isVisible():
                self.clipboard_tab.load_clipboard_items()
                
        except Exception as e:
            logger.error(f'Error handling clipboard change: {str(e)}')
            
    def on_app_state_changed(self, state):
        try:
            self.setup_clipboard_monitoring()
        except Exception as e:
            logger.error(f'Error reinitializing clipboard monitoring: {e}')

    # ===== Windows native clipboard listener =====
    def register_clipboard_listener(self):
        if self._clipboard_listener_registered:
            return
        try:
            hwnd = int(self.winId())
            user32 = ctypes.windll.user32
            if not user32.AddClipboardFormatListener(wintypes.HWND(hwnd)):
                raise RuntimeError('AddClipboardFormatListener failed')
            self._clipboard_listener_registered = True
        except Exception as e:
            raise

    def unregister_clipboard_listener(self):
        if not getattr(self, '_clipboard_listener_registered', False):
            return
        try:
            hwnd = int(self.winId())
            user32 = ctypes.windll.user32
            user32.RemoveClipboardFormatListener(wintypes.HWND(hwnd))
        except Exception:
            pass
        self._clipboard_listener_registered = False

    def nativeEvent(self, eventType, message):
        try:
            if eventType == 'windows_generic_MSG':
                MSG = wintypes.MSG
                msg = MSG.from_address(int(message))
                WM_CLIPBOARDUPDATE = 0x031D
                if msg.message == WM_CLIPBOARDUPDATE:
                    # Defer handling to Qt event loop to avoid reentrancy
                    QTimer.singleShot(0, self.on_clipboard_changed)
                    return True, 0
        except Exception:
            pass
        return False, 0
            
    def cleanup_old_items(self):
        """Remove clipboard items older than 1 Year"""
        days = self.get_retention_days()
        deleted_count = self.db.cleanup_old_items(days)
        if deleted_count > 0:
            logger.info(f'Cleaned up {deleted_count} old clipboard items')
            
    def closeEvent(self, event):
        """Override close event to minimize to system tray"""
        event.ignore()
        self.hide()

    def update_launch_details(self):
        """Compute and display DB size and total history days once at launch."""
        try:
            # Compute DB size
            db_path = self.db.db_path
            size_bytes = os.path.getsize(db_path) if os.path.exists(db_path) else 0
            size_str = self._format_size(size_bytes)
            # Total history days (distinct local dates)
            try:
                days = len(self.db.get_clipboard_dates())
            except Exception:
                days = 0
            text = f"Details (last launch): DB {size_str} • History: {days} day{'s' if days != 1 else ''}"
            if hasattr(self, 'details_label') and self.details_label is not None:
                self.details_label.setText(text)
            else:
                self.statusBar().showMessage(text)
        except Exception as e:
            logger.warning(f"update_launch_details failed: {e}")

    def _format_size(self, num: int) -> str:
        for unit in ['B','KB','MB','GB','TB']:
            if num < 1024.0:
                return f"{num:.1f} {unit}"
            num /= 1024.0
        return f"{num:.1f} PB"
    
    def show_about_dialog(self):
        """Show About dialog with application and author information"""
        about_text = """
        <h2>SupportHelper</h2>
        <p>Version 26.2.5.2</p>
        <p>A comprehensive support helper tool with World Clock features, meeting scheduling capabilities, and custom integrations.</p>
        <br>
        <p><b>Features:</b></p>
        <ul>
            <li>World Clock with multiple time zones</li>
            <li>Meeting scheduling with Teams/Outlook integration</li>
            <li>Varios World Clock Integrations possible</li>
            <li>Clipboard history management</li>
            <li>OCR capabilities</li>
            <li>Text snippets management</li>
        </ul>
        <br>
        <p><b>Architected by: Rehan Mansury</b></p>
        <br>
        <p><b>GitHub Repository:</b></p>
        <p><a href='https://github.com/rehanmansury/SupportHelper'>https://github.com/rehanmansury/SupportHelper</a></p>
        <br>
        <p>© 2026 All rights reserved.</p>
        """
        
        QMessageBox.about(self, "About SupportHelper", about_text)
    
    def close_application(self):
        """Fully close the application"""
        try:
            self.unregister_clipboard_listener()
        except Exception:
            pass
        self.tray_icon.hide()
        QApplication.quit()
    
    def show_tray_message(self):
        """Show message when minimizing to tray"""
        self.tray_icon.showMessage(
            'SupportHelper',
            'The application is still running in the system tray.',
            QSystemTrayIcon.Information,
            2000
        )

    # ===== Retention configuration =====
    def get_retention_days(self) -> int:
        try:
            val = int(self.db.get_setting('retention_days', '366') or '366')
            return max(1, min(3650, val))
        except Exception:
            return 366

    def configure_retention(self):
        current = self.get_retention_days()
        days_str, ok = QInputDialog.getText(
            self,
            'Retention',
            'Delete clipboard items older than N days (applies on next launch):',
            text=str(current)
        )
        if not ok:
            return
        try:
            days = max(1, min(3650, int(days_str.strip())))
        except Exception:
            QMessageBox.warning(self, 'Invalid Input', 'Please enter a valid number of days (1-3650).')
            return
        self.db.set_setting('retention_days', str(days))
        # Ask if user wants to run cleanup now
        reply = QMessageBox.question(
            self,
            'Retention Saved',
            f'Retention set to {days} days.\n\nRun cleanup now?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.cleanup_old_items()
            # Refresh launch details label
            try:
                self.update_launch_details()
            except Exception:
                pass
            # Refresh clipboard tab list if visible
            try:
                if hasattr(self, 'clipboard_tab') and self.clipboard_tab.isVisible():
                    self.clipboard_tab.load_clipboard_items()
            except Exception:
                pass
            QMessageBox.information(self, 'Cleanup Complete', 'Old items deleted as per retention. Database has been vacuumed.')
        else:
            QMessageBox.information(self, 'Retention Saved', 'Changes will take effect on next launch.')
 
    # ===== Appearance controls =====
    def toggle_dark_mode(self, checked: bool):
        self.dark_mode_enabled = checked
        self.db.set_setting('app_dark_mode', '1' if checked else '0')
        self.apply_appearance()
        try:
            if hasattr(self, 'world_clock_tab') and hasattr(self.world_clock_tab, 'update_theme'):
                self.world_clock_tab.update_theme(self.dark_mode_enabled)
        except Exception:
            pass
 
    def choose_font(self):
        current = self.custom_font or self.font()
        font, ok = QFontDialog.getFont(current, self, "Choose Application Font")
        if ok:
            self.custom_font = font
            # Persist font
            self.db.set_setting('app_font', font.toString())
            self.apply_appearance()
 
    def choose_text_color(self):
        current = self.custom_text_color or QColor('#FFFFFF' if self.dark_mode_enabled else '#000000')
        color = QColorDialog.getColor(current, self, "Choose Text Color")
        if color.isValid():
            self.custom_text_color = color
            # Persist color
            self.db.set_setting('app_text_color', color.name())
            self.apply_appearance()
 
    def choose_background_color(self):
        current = self.custom_bg_color or QColor('#121212' if self.dark_mode_enabled else '#FFFFFF')
        color = QColorDialog.getColor(current, self, "Choose Background Color")
        if color.isValid():
            self.custom_bg_color = color
            # Persist color
            self.db.set_setting('app_bg_color', color.name())
            self.apply_appearance()
 
    def apply_appearance(self):
        app = QApplication.instance()
        # Font
        if self.custom_font:
            app.setFont(self.custom_font)
        # Palette base (dark or light)
        palette = QPalette()
        if self.dark_mode_enabled:
            palette.setColor(QPalette.Window, QColor(18, 18, 18))
            palette.setColor(QPalette.WindowText, QColor(220, 220, 220))
            palette.setColor(QPalette.Base, QColor(30, 30, 30))
            palette.setColor(QPalette.AlternateBase, QColor(45, 45, 45))
            palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 220))
            palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))
            palette.setColor(QPalette.Text, QColor(220, 220, 220))
            palette.setColor(QPalette.Button, QColor(45, 45, 45))
            palette.setColor(QPalette.ButtonText, QColor(220, 220, 220))
            palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
            palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
            palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
        else:
            palette = app.style().standardPalette()
 
        # Apply custom colors if set
        if self.custom_bg_color:
            palette.setColor(QPalette.Window, self.custom_bg_color)
            palette.setColor(QPalette.Base, self.custom_bg_color.darker(110) if self.dark_mode_enabled else self.custom_bg_color)
        if self.custom_text_color:
            palette.setColor(QPalette.WindowText, self.custom_text_color)
            palette.setColor(QPalette.Text, self.custom_text_color)
            palette.setColor(QPalette.ButtonText, self.custom_text_color)
 
        app.setPalette(palette)


def main():
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Start the application
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
