import logging
import datetime
import os
from typing import List, Dict
import webbrowser

import pytz
from PyQt5.QtCore import Qt, QTimer, QDate
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider,
    QPushButton, QGroupBox, QGridLayout, QScrollArea, QFrame,
    QLineEdit, QListWidget, QListWidgetItem, QDialog,
    QDialogButtonBox, QMessageBox, QComboBox, QCheckBox,
    QDateEdit, QTimeEdit, QMenu, QAction, QFormLayout
)

LOGGER = logging.getLogger(__name__)


class TimeZoneWidget(QFrame):
    def __init__(self, timezone_name: str, city_name: str, is_local: bool = False):
        super().__init__()
        self.timezone_name = timezone_name
        self.city_name = city_name
        self.is_local = is_local

        self.setFrameStyle(QFrame.Box)
        self._setup_ui()
        self.update_styles()
        # Note: Context menu is handled by parent WorldClockTab

    def update_styles(self, dark_mode: bool = False):
        self.setStyleSheet("""
            TimeZoneWidget {
                background-color: %s;
                border: 1px solid %s;
                border-radius: 8px;
                margin: 2px;
                padding: 8px;
            }
            TimeZoneWidget:hover {
                background-color: %s;
                border-color: #007bff;
            }
        """ % ("#1E1E1E" if dark_mode else "#f8f9fa",
                 "#444" if dark_mode else "#dee2e6",
                 "#2A2A2A" if dark_mode else "#e9ecef"))

        if hasattr(self, 'city_label'):
            self.city_label.setStyleSheet(f"color: {'#63b3ed' if self.is_local else '#007bff'}; font-weight: bold;")
        if hasattr(self, 'time_label'):
            self.time_label.setStyleSheet(f"color: {'#63b3ed' if self.is_local else '#007bff'};")
        if hasattr(self, 'date_label'):
            self.date_label.setStyleSheet("color: #AAAAAA;" if dark_mode else "color: #6c757d;")
        if hasattr(self, 'timezone_label'):
            self.timezone_label.setStyleSheet("color: #AAAAAA;" if dark_mode else "color: #6c757d;")
        if hasattr(self, 'dst_label'):
            # keep color set at update_time
            pass

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(2)  # Reduce spacing between labels
        layout.setContentsMargins(4, 4, 4, 4)  # Reduce margins

        city_text = self.city_name + (" (Local)" if self.is_local else "")
        self.city_label = QLabel(city_text)
        self.city_label.setFont(QFont("Arial", 10, QFont.Bold))  # Reduced from 12
        self.city_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.city_label)

        self.time_label = QLabel()
        self.time_label.setFont(QFont("Arial", 14, QFont.Bold))  # Reduced from 16
        self.time_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.time_label)

        self.date_label = QLabel()
        self.date_label.setFont(QFont("Arial", 8))  # Reduced from 10
        self.date_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.date_label)

        self.timezone_label = QLabel(self.timezone_name)
        self.timezone_label.setFont(QFont("Arial", 7))  # Reduced from 9
        self.timezone_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.timezone_label)

        self.dst_label = QLabel()
        self.dst_label.setFont(QFont("Arial", 7))  # Reduced from 8
        self.dst_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.dst_label)

    def update_time(self, base_time: datetime.datetime, local_tz: pytz.BaseTzInfo):
        try:
            tz = pytz.timezone(self.timezone_name)
            local_time = local_tz.localize(base_time.replace(tzinfo=None))
            target_time = local_time.astimezone(tz)
            is_dst = (target_time.dst() or datetime.timedelta(0)) > datetime.timedelta(0)

            self.time_label.setText(target_time.strftime("%H:%M:%S"))
            self.date_label.setText(target_time.strftime("%A, %B %d, %Y"))
            if is_dst:
                self.dst_label.setText("DST Active")
                self.dst_label.setStyleSheet("color: #48bb78; font-weight: bold;")
            else:
                self.dst_label.setText("Standard Time")
                self.dst_label.setStyleSheet("color: #6c757d;")
        except Exception as e:
            LOGGER.error(f"Error updating time for {self.timezone_name}: {e}")
            self.time_label.setText("--:--:--")
            self.date_label.setText("Error")

    def get_target_time(self) -> datetime.datetime:
        """Get the target city's time based on the parent's current time"""
        try:
            # Walk up parents to find the world clock tab with current_time/current_date/local_timezone
            parent = self.parent()
            while parent and not (hasattr(parent, 'current_time') and hasattr(parent, 'current_date') and hasattr(parent, 'local_timezone')):
                parent = parent.parent()

            if not parent:
                # Return current time if parent not found
                return datetime.datetime.now()

            # Get the parent's current time and date
            current_time = parent.current_time
            current_date = parent.current_date

            # Combine date and time
            py_date = current_date.toPyDate()
            target_dt = datetime.datetime.combine(py_date, datetime.time(current_time.hour, current_time.minute, 0, 0))

            # Convert to target timezone
            tz = pytz.timezone(self.timezone_name)
            local_tz = parent.local_timezone
            local_time = local_tz.localize(target_dt)
            target_time = local_time.astimezone(tz)

            return target_time

        except Exception as e:
            LOGGER.error(f"Error getting target time for {self.timezone_name}: {e}")
            return datetime.datetime.now()

    def _create_meeting(self, platform: str):
        try:
            # Walk up parents to find the world clock tab with current_time/current_date/local_timezone
            parent = self.parent()
            while parent and not (hasattr(parent, 'current_time') and hasattr(parent, 'current_date') and hasattr(parent, 'local_timezone')):
                parent = parent.parent()
            if not parent:
                QMessageBox.warning(self, "Error", "Could not access current time.")
                return
            current_time = parent.current_time
            current_date = parent.current_date
            # Combine date and time
            py_date = current_date.toPyDate()
            target_dt = datetime.datetime.combine(py_date, datetime.time(current_time.hour, current_time.minute, 0, 0))
            # Convert to target timezone to get intended meeting time
            tz = pytz.timezone(self.timezone_name)
            local_tz = parent.local_timezone
            local_time = local_tz.localize(target_dt)
            target_time = local_time.astimezone(tz)
            local_meeting_time = target_time.astimezone(local_tz)
            # Format
            readable_target_time = target_time.strftime("%Y-%m-%d %H:%M")
            readable_local_time = local_meeting_time.strftime("%Y-%m-%d %H:%M")
            # Ask for duration in 15-min steps up to 8 hours
            duration_minutes = self._confirm_and_get_duration(readable_target_time, readable_local_time, self.city_name)
            if duration_minutes is None:
                return
            start_time = local_meeting_time.strftime("%Y-%m-%dT%H:%M:00")
            end_time = (local_meeting_time + datetime.timedelta(minutes=duration_minutes)).strftime("%Y-%m-%dT%H:%M:00")
            subject = "NexthinkSupport"
            meeting_url = f"https://teams.microsoft.com/l/meeting/new?subject={subject}&startTime={start_time}&endTime={end_time}"
            webbrowser.open(meeting_url)
        except Exception as e:
            LOGGER.error(f"Error creating {platform} meeting: {e}")
            QMessageBox.critical(self, "Error", f"Could not create {platform} meeting: {e}")

    def _confirm_and_get_duration(self, readable_target_time: str, readable_local_time: str, city_name: str) -> int:
        """Show a confirmation dialog with duration selection. Returns minutes or None if cancelled."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Confirm Meeting")
        v = QVBoxLayout(dialog)
        msg = QLabel(
            f"Create Teams meeting for {city_name}?\n\n"
            f"Target Time: {readable_target_time} ({city_name})\n"
            f"Your Local Time: {readable_local_time}\n\n"
            f"Select duration:"
        )
        msg.setWordWrap(True)
        v.addWidget(msg)
        # Duration choices: 15 to 480 in steps of 15
        combo = QComboBox(dialog)
        durations = list(range(15, 8*60 + 1, 15))
        for d in durations:
            combo.addItem(f"{d} minutes" if d < 60 else (f"{d//60} hour" + ("" if d==60 else "s") + (f" {d%60} min" if d%60 else "")), d)
        # Default 30 min
        default_index = durations.index(30) if 30 in durations else 0
        combo.setCurrentIndex(default_index)
        v.addWidget(combo)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=dialog)
        v.addWidget(buttons)
        result = {'accepted': False}
        def accept():
            result['accepted'] = True
            dialog.accept()
        buttons.accepted.connect(accept)
        buttons.rejected.connect(dialog.reject)
        if dialog.exec_() == QDialog.Accepted and result['accepted']:
            return int(combo.currentData())
        return None


class CustomUrlManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("World Clock Integrations")
        self.setModal(True)
        self.resize(600, 500)
        self._setup_ui()
        self._load_parameters()
        self._load_urls()
        self.editing_mode = False  # Track if we're in edit mode
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Instructions
        info = QLabel("Manage custom meeting URLs for third-party integrations:")
        info.setWordWrap(True)
        info.setStyleSheet("color: #6c757d; margin-bottom: 10px;")
        layout.addWidget(info)
        
        # URL list
        list_group = QGroupBox("Configured URLs")
        list_layout = QVBoxLayout(list_group)
        
        self.url_list = QListWidget()
        self.url_list.setSelectionMode(QListWidget.SingleSelection)
        self.url_list.itemSelectionChanged.connect(self._on_selection_changed)
        list_layout.addWidget(self.url_list)
        
        # Buttons for list
        list_buttons = QHBoxLayout()
        self.add_btn = QPushButton("Add")
        self.add_btn.clicked.connect(self._add_new_url)
        self.edit_btn = QPushButton("Edit")
        self.edit_btn.clicked.connect(self._edit_url)
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self._delete_url)
        # Initially disable Edit and Delete buttons (no selection)
        self.edit_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        list_buttons.addWidget(self.add_btn)
        list_buttons.addWidget(self.edit_btn)
        list_buttons.addWidget(self.delete_btn)
        list_buttons.addStretch()
        list_layout.addLayout(list_buttons)
        
        layout.addWidget(list_group)
        
        # Add new URL section
        add_group = QGroupBox("Add New Integration")
        add_layout = QVBoxLayout(add_group)
        
        form_layout = QFormLayout()
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., Outlook Bookings, Teams Launcher, Zoom Meeting")
        form_layout.addRow("Name:", self.name_input)
        
        # Integration type selection
        self.integration_type_combo = QComboBox()
        self.integration_type_combo.addItem("Email Integration", "email")
        self.integration_type_combo.addItem("Application Launcher", "launcher")
        self.integration_type_combo.addItem("Web URL Launcher", "url")
        self.integration_type_combo.addItem("Batch File Launcher", "batch")
        self.integration_type_combo.currentTextChanged.connect(self._on_integration_type_changed)
        form_layout.addRow("Integration Type:", self.integration_type_combo)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://outlook.office.com/bookings/... or C:\\app.exe or https://teams.com/...")
        form_layout.addRow("URL/Application Path:", self.url_input)
        
        # Email app selection (only for email type)
        self.email_app_combo = QComboBox()
        self.email_app_combo.addItem("None (launch URL directly)", "")
        self.email_app_combo.addItem("Browse...", "browse")
        self.email_app_combo.addItem("Outlook", "outlook")
        self.email_app_combo.addItem("Thunderbird", "thunderbird")
        self.email_app_combo.addItem("Default Email Client", "default")
        form_layout.addRow("Email App:", self.email_app_combo)
        
        self.email_path_input = QLineEdit()
        self.email_path_input.setPlaceholderText("Path to email executable (e.g., C:\\Program Files\\Microsoft Office\\root\\Office16\\OUTLOOK.EXE)")
        self.email_path_input.setEnabled(False)
        form_layout.addRow("Email App Path:", self.email_path_input)
        
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.setEnabled(False)
        self.browse_btn.clicked.connect(self._browse_email_app)
        form_layout.addRow("", self.browse_btn)
        
        # Parameters section
        param_group = QGroupBox("Parameters")
        param_layout = QVBoxLayout(param_group)
        
        # Parameter help text
        param_help = QLabel("Available parameters (double click to put the parameter):")
        param_help.setStyleSheet("color: #6c757d; font-weight: bold;")
        param_layout.addWidget(param_help)
        
        # Parameter list
        self.param_list_widget = QListWidget()
        self.param_list_widget.setMaximumHeight(120)
        self.param_list_widget.itemDoubleClicked.connect(self._copy_parameter)
        param_layout.addWidget(self.param_list_widget)
        
        # Parameter input field
        param_input_layout = QHBoxLayout()
        self.param_input = QLineEdit()
        self.param_input.setPlaceholderText("Enter parameters or double-click items above to copy. Example: /meet %wc_city_name% -duration %wc_duration%")
        form_layout.addRow("Parameters:", self.param_input)
        
        # Add help button for parameters
        help_btn = QPushButton("?")
        help_btn.setFixedSize(24, 24)
        help_btn.setToolTip("Click for parameter guide")
        help_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border-radius: 12px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        help_btn.clicked.connect(self._show_parameter_guide)
        param_input_layout.addWidget(self.param_input)
        param_input_layout.addWidget(help_btn)
        form_layout.addRow("", param_input_layout)
        
        add_layout.addLayout(form_layout)
        add_layout.addWidget(param_group)
        
        self.add_btn = QPushButton("Add/Save Config")
        self.add_btn.clicked.connect(self._add_url)
        # Initially enabled since fields are clear for new entry
        self.add_btn.setEnabled(True)
        add_layout.addWidget(self.add_btn)
        
        layout.addWidget(add_group)
        
        # Dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.accept)
        layout.addWidget(buttons)
        
        # Enable/disable buttons based on selection
        self.url_list.itemSelectionChanged.connect(self._update_buttons)
        self.email_app_combo.currentTextChanged.connect(self._on_email_app_changed)
        self._update_buttons()
        
    def _show_parameter_guide(self):
        """Show a comprehensive guide for using parameters"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit
        from PyQt5.QtCore import Qt
        
        guide_dialog = QDialog(self)
        guide_dialog.setWindowTitle("Parameter Guide")
        guide_dialog.setModal(True)
        guide_dialog.resize(600, 500)
        
        layout = QVBoxLayout(guide_dialog)
        
        # Create text widget with guide
        guide_text = QTextEdit()
        guide_text.setReadOnly(True)
        guide_text.setHtml("""
        <h2>📝 Parameter Guide</h2>
        
        <h3>🔧 Available Parameters</h3>
        <table border="1" cellpadding="5" cellspacing="0" width="100%">
            <tr bgcolor="#f0f0f0">
                <th>Parameter</th>
                <th>Description</th>
                <th>Example Output</th>
            </tr>
            <tr>
                <td><code>%wc_city_name%</code></td>
                <td>City name</td>
                <td>Dubai, Tokyo, New York</td>
            </tr>
            <tr>
                <td><code>%wc_timezone%</code></td>
                <td>Timezone ID</td>
                <td>Asia/Dubai, Asia/Tokyo</td>
            </tr>
            <tr>
                <td><code>%wc_local_time%</code></td>
                <td>Your local time</td>
                <td>2026-02-03 14:30</td>
            </tr>
            <tr>
                <td><code>%wc_target_time%</code></td>
                <td>Target city time</td>
                <td>2026-02-03 18:30</td>
            </tr>
            <tr>
                <td><code>%wc_date%</code></td>
                <td>Current date</td>
                <td>2026-02-03</td>
            </tr>
            <tr>
                <td><code>%wc_time%</code></td>
                <td>Current time</td>
                <td>14:30</td>
            </tr>
            <tr>
                <td><code>%wc_year%</code></td>
                <td>Year</td>
                <td>2026</td>
            </tr>
            <tr>
                <td><code>%wc_month%</code></td>
                <td>Month (2-digit)</td>
                <td>02</td>
            </tr>
            <tr>
                <td><code>%wc_day%</code></td>
                <td>Day (2-digit)</td>
                <td>03</td>
            </tr>
            <tr>
                <td><code>%wc_hour%</code></td>
                <td>Hour (2-digit)</td>
                <td>14</td>
            </tr>
            <tr>
                <td><code>%wc_minute%</code></td>
                <td>Minute (2-digit)</td>
                <td>30</td>
            </tr>
        </table>
        
        <h3>🌐 Common Use Cases</h3>
        
        <h4>1. Google Search</h4>
        <table border="1" cellpadding="5" cellspacing="0" width="100%">
            <tr bgcolor="#f0f0f0">
                <th>Purpose</th>
                <th>URL</th>
                <th>Parameters</th>
                <th>Result</th>
            </tr>
            <tr>
                <td>Current time in city</td>
                <td>https://www.google.com/search?q=</td>
                <td>%wc_city_name%+time+now</td>
                <td>search?q=Dubai+time+now</td>
            </tr>
            <tr>
                <td>Weather in city</td>
                <td>https://www.google.com/search?q=</td>
                <td>weather+in+%wc_city_name%</td>
                <td>search?q=weather+in+Dubai</td>
            </tr>
        </table>
        
        <h4>2. Meeting Scheduler</h4>
        <table border="1" cellpadding="5" cellspacing="0" width="100%">
            <tr bgcolor="#f0f0f0">
                <th>Service</th>
                <th>URL</th>
                <th>Parameters</th>
            </tr>
            <tr>
                <td>Google Calendar</td>
                <td>https://calendar.google.com/calendar/render?action=TEMPLATE&</td>
                <td>text=Meeting+with+%wc_city_name%&dates=%wc_year%%wc_month%%wc_day%T%wc_hour%%wc_minute%00</td>
            </tr>
            <tr>
                <td>Outlook Calendar</td>
                <td>https://outlook.live.com/calendar/0/deeplink/compose?subject=Meeting+with+%wc_city_name%&startdt=%wc_year%-%wc_month%-%wc_day%T%wc_hour%:%wc_minute%&enddt=%wc_year%-%wc_month%-%wc_day%T%wc_hour%:%wc_minute%</td>
                <td></td>
            </tr>
        </table>
        
        <h4>3. Time Zone Tools</h4>
        <table border="1" cellpadding="5" cellspacing="0" width="100%">
            <tr bgcolor="#f0f0f0">
                <th>Service</th>
                <th>URL</th>
                <th>Parameters</th>
            </tr>
            <tr>
                <td>Time Converter</td>
                <td>https://www.timeanddate.com/worldclock/converter.html?</td>
                <td>iso=%wc_local_time%&p1=195&p2=%wc_timezone%</td>
            </tr>
        </table>
        
        <h3>💡 Tips & Tricks</h3>
        <ul>
            <li><b>Spaces in URLs:</b> Use <code>+</code> for spaces (e.g., <code>time+in+%wc_city_name%</code>)</li>
            <li><b>Don't start with /:</b> The system automatically removes leading slashes</li>
            <li><b>Test simple first:</b> Start with just <code>%wc_city_name%</code> to ensure it works</li>
            <li><b>Double-click to copy:</b> Double-click any parameter in the list above to copy it</li>
            <li><b>URL encoding:</b> The system automatically handles special characters</li>
        </ul>
        
        <h3>⚠️ Important Notes</h3>
        <ul>
            <li><b>%wc_target_time%</b> gives the time in the selected city's timezone</li>
            <li><b>%wc_local_time%</b> gives your local time</li>
            <li><b>Integration Type matters:</b> Use "Web URL Launcher" for web URLs</li>
            <li><b>Check service documentation:</b> Different services may require different URL formats</li>
        </ul>
        """)
        
        layout.addWidget(guide_text)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(guide_dialog.accept)
        layout.addWidget(close_btn)
        
        guide_dialog.exec_()
        
    def _update_buttons(self):
        """Enable/disable buttons based on selection"""
        has_selection = bool(self.url_list.currentItem())
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
        
    def _on_email_app_changed(self, text):
        """Handle email app selection change"""
        app_data = self.email_app_combo.currentData()
        if app_data == "browse":
            self.email_path_input.setEnabled(True)
            self.browse_btn.setEnabled(True)
        elif app_data in ["outlook", "thunderbird"]:
            self.email_path_input.setEnabled(False)
            self.browse_btn.setEnabled(False)
            # Auto-fill common paths
            if app_data == "outlook":
                self.email_path_input.setText("C:\\Program Files\\Microsoft Office\\root\\Office16\\OUTLOOK.EXE")
            elif app_data == "thunderbird":
                self.email_path_input.setText("C:\\Program Files\\Mozilla Thunderbird\\thunderbird.exe")
        else:
            self.email_path_input.setEnabled(False)
            self.browse_btn.setEnabled(False)
            self.email_path_input.clear()
            
    def _browse_email_app(self):
        """Browse for email application executable"""
        from PyQt5.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Email Application", "", "Executable Files (*.exe)"
        )
        if file_path:
            self.email_path_input.setText(file_path)
            
    def _on_integration_type_changed(self, text):
        """Handle integration type change"""
        integration_type = self.integration_type_combo.currentData()
        
        if integration_type == "email":
            # Show email-related fields
            self.email_app_combo.setEnabled(True)
            self.email_path_input.setEnabled(False)
            self.browse_btn.setEnabled(False)
            self.url_input.setPlaceholderText("https://outlook.office.com/bookings/...")
        elif integration_type == "launcher":
            # Show application launcher fields
            self.email_app_combo.setEnabled(False)
            self.email_path_input.setEnabled(False)
            self.browse_btn.setEnabled(False)
            self.url_input.setPlaceholderText("C:\\Program Files\\Teams\\Teams.exe")
        elif integration_type == "url":
            # Show URL launcher fields
            self.email_app_combo.setEnabled(False)
            self.email_path_input.setEnabled(False)
            self.browse_btn.setEnabled(False)
            self.url_input.setPlaceholderText("https://teams.microsoft.com/...")
        elif integration_type == "batch":
            # Show batch file fields
            self.email_app_combo.setEnabled(False)
            self.email_path_input.setEnabled(False)
            self.browse_btn.setEnabled(True)
            self.url_input.setPlaceholderText("C:\\Scripts\\launch_meeting.bat")
            
    def _load_parameters(self):
        """Load World Clock parameters"""
        try:
            parent = self.parent()
            if parent and hasattr(parent, 'db') and parent.db:
                parameters = parent.db.get_wc_parameters()
                self.param_list_widget.clear()
                
                # Group parameters by category
                categories = {}
                for param in parameters:
                    category = param['param_category']
                    if category not in categories:
                        categories[category] = []
                    categories[category].append(param)
                
                # Add parameters by category
                for category, params in categories.items():
                    # Add category header
                    header_item = QListWidgetItem(f"--- {category.title()} ---")
                    header_item.setData(Qt.UserRole, None)
                    header_item.setForeground(Qt.gray)
                    self.param_list_widget.addItem(header_item)
                    
                    # Add parameters
                    for param in params:
                        display_text = f"{param['param_name']} - {param['param_description']}"
                        item = QListWidgetItem(display_text)
                        item.setData(Qt.UserRole, param['param_name'])
                        item.setToolTip(f"Sample: {param['param_sample']}")
                        self.param_list_widget.addItem(item)
                        
        except Exception as e:
            LOGGER.error(f"Error loading parameters: {e}")
            
    def _copy_parameter(self, item):
        """Copy parameter to clipboard and insert into parameter input"""
        param_name = item.data(Qt.UserRole)
        if param_name:
            # Insert parameter at cursor position in parameter input
            cursor_pos = self.param_input.cursorPosition()
            current_text = self.param_input.text()
            new_text = current_text[:cursor_pos] + param_name + current_text[cursor_pos:]
            self.param_input.setText(new_text)
            # Move cursor after inserted parameter
            self.param_input.setCursorPosition(cursor_pos + len(param_name))
        
    def _load_urls(self):
        """Load existing URLs from database"""
        try:
            parent = self.parent()
            if parent and hasattr(parent, 'db') and parent.db:
                urls = parent.db.get_custom_urls()
                self.url_list.clear()
                for name, data in urls.items():
                    url = data.get('url', '')
                    integration_type = data.get('integration_type', 'email')
                    app_path = data.get('app_path', '')
                    parameters = data.get('parameters', '')
                    
                    # Debug logging
                    LOGGER.info(f"Loaded integration: name={name}, type={integration_type}")
                    
                    # Create display text based on integration type
                    if integration_type == "email":
                        display_text = f"{name} - {url}"
                        if app_path:
                            display_text += f" [Email: {os.path.basename(app_path)}]"
                    elif integration_type == "launcher":
                        display_text = f"{name} - {os.path.basename(url)}"
                        if parameters:
                            display_text += f" [Params: {parameters[:30]}...]"
                    elif integration_type == "url":
                        display_text = f"{name} - {url}"
                        if parameters:
                            display_text += f" [Params: {parameters[:30]}...]"
                    elif integration_type == "batch":
                        display_text = f"{name} - {os.path.basename(url)}"
                        if parameters:
                            display_text += f" [Params: {parameters[:30]}...]"
                    else:
                        display_text = f"{name} - {url}"
                    
                    item = QListWidgetItem(display_text)
                    item.setData(Qt.UserRole, {
                        "name": name, 
                        "url": url, 
                        "integration_type": integration_type,
                        "app_path": app_path,
                        "parameters": parameters
                    })
                    self.url_list.addItem(item)
        except Exception as e:
            LOGGER.error(f"Error loading custom URLs: {e}")
    
    def _on_selection_changed(self):
        """Handle selection change - populate fields as read-only"""
        current_item = self.url_list.currentItem()
        
        # Disable Edit button if no item is selected
        if not current_item:
            self.edit_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            # Clear fields when no selection
            self._clear_fields()
            # Enable Add/Save Config button for new entry
            self.add_btn.setEnabled(True)
            return
        
        if self.editing_mode:
            return
            
        # Enable Edit and Delete buttons when item is selected
        self.edit_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)
            
        data = current_item.data(Qt.UserRole)
        
        # Debug logging
        LOGGER.info(f"Selected item data: {data}")
        
        # Populate fields as read-only
        self.name_input.setText(data["name"])
        self.name_input.setReadOnly(True)
        self.url_input.setText(data["url"])
        self.url_input.setReadOnly(True)
        
        # Handle integration type - fix: set by data value, not text
        integration_type = data.get("integration_type", "email")
        LOGGER.info(f"Setting integration type combo to: {integration_type}")
        
        # Find the index of the integration type in the combo box
        for i in range(self.integration_type_combo.count()):
            if self.integration_type_combo.itemData(i) == integration_type:
                self.integration_type_combo.setCurrentIndex(i)
                LOGGER.info(f"Found integration type at index {i}")
                break
        else:
            LOGGER.warning(f"Integration type '{integration_type}' not found in combo box")
        
        # Handle app path and parameters
        app_path = data.get("app_path", "")
        parameters = data.get("parameters", "")
        
        self.email_path_input.setText(app_path)
        self.email_path_input.setReadOnly(True)
        self.param_input.setText(parameters)
        self.param_input.setReadOnly(True)
        
        # Update field visibility based on integration type
        self._on_integration_type_changed(integration_type)
        
        # Disable all controls in read-only mode
        self.email_app_combo.setEnabled(False)
        self.browse_btn.setEnabled(False)
        self.integration_type_combo.setEnabled(False)
        
        # Disable Add/Save Config button in read-only mode
        self.add_btn.setEnabled(False)
        
        # Set email app combo based on path (for display only)
        if integration_type == "email":
            if not app_path:
                self.email_app_combo.setCurrentIndex(0)
            elif "outlook.exe" in app_path.lower():
                self.email_app_combo.setCurrentText("Outlook")
            elif "thunderbird.exe" in app_path.lower():
                self.email_app_combo.setCurrentText("Thunderbird")
            else:
                self.email_app_combo.setCurrentText("Browse...")
            
    def _edit_url(self):
        """Enable editing for selected URL"""
        current_item = self.url_list.currentItem()
        if not current_item:
            return
            
        # Enable editing mode
        self.editing_mode = True
        
        # Make fields editable
        self.name_input.setReadOnly(False)
        self.url_input.setReadOnly(False)
        self.email_path_input.setReadOnly(False)
        self.param_input.setReadOnly(False)
        self.email_app_combo.setEnabled(True)
        self.browse_btn.setEnabled(True)
        self.integration_type_combo.setEnabled(True)
        
        # Enable Add/Save Config button in edit mode
        self.add_btn.setEnabled(True)
        
        # Disable Edit and Delete buttons during edit mode
        self.edit_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        
        # Store current data for potential update
        self.current_edit_data = current_item.data(Qt.UserRole)
    
    def _clear_fields(self):
        """Clear all input fields"""
        self.name_input.clear()
        self.url_input.clear()
        self.email_path_input.clear()
        self.param_input.clear()
        self.email_app_combo.setCurrentIndex(0)
        # Don't reset integration type - keep the user's selection
        # self.integration_type_combo.setCurrentIndex(0)
        
        # Make fields editable again for new entries
        self.name_input.setReadOnly(False)
        self.url_input.setReadOnly(False)
        self.email_path_input.setReadOnly(False)
        self.param_input.setReadOnly(False)
        self.email_app_combo.setEnabled(True)
        self.browse_btn.setEnabled(True)
        self.integration_type_combo.setEnabled(True)
    
    def _add_new_url(self):
        """Clear fields and prepare for adding new URL"""
        # Clear any editing mode
        self.editing_mode = False
        self.edit_btn.setText("Edit")
        self.edit_btn.clicked.disconnect()
        self.edit_btn.clicked.connect(self._edit_url)
        
        # Clear selection in list
        self.url_list.clearSelection()
        
        # Clear all fields
        self._clear_fields()
        
        # Ensure fields are editable for new entry
        self.name_input.setReadOnly(False)
        self.url_input.setReadOnly(False)
        self.email_path_input.setReadOnly(False)
        self.email_app_combo.setEnabled(True)
        self.browse_btn.setEnabled(True)
        
        # Enable Add/Save Config button for new entry
        self.add_btn.setEnabled(True)
        
        # Set focus to name input for convenience
        self.name_input.setFocus()
            
    def _add_url(self):
        """Add a new URL integration or save edited one"""
        name = self.name_input.text().strip()
        url = self.url_input.text().strip()
        integration_type = self.integration_type_combo.currentData()
        app_path = self.email_path_input.text().strip()
        parameters = self.param_input.text().strip()
        
        # Debug logging
        LOGGER.info(f"Saving integration: name={name}, type={integration_type}, url={url}")
        
        if not name or not url:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Input Error", "Please enter both name and URL/application path.")
            return
            
        try:
            parent = self.parent()
            if parent and hasattr(parent, 'db') and parent.db:
                # Check if we're in edit mode
                if self.editing_mode and hasattr(self, 'current_edit_data'):
                    # Save edited entry
                    old_name = self.current_edit_data["name"]
                    
                    # Delete old entry if name changed
                    if old_name != name:
                        parent.db.delete_custom_url(old_name)
                    
                    # Save updated entry
                    parent.db.save_custom_url(name, url, integration_type, app_path, parameters)
                    LOGGER.info(f"Updated integration with type: {integration_type}")
                    
                    # Reset editing mode
                    self.editing_mode = False
                    
                    # Re-enable Edit and Delete buttons after saving
                    self.edit_btn.setEnabled(True)
                    self.delete_btn.setEnabled(True)
                    
                    from PyQt5.QtWidgets import QMessageBox
                    QMessageBox.information(self, "Success", f"Integration '{name}' updated successfully!")
                else:
                    # Add new entry
                    parent.db.save_custom_url(name, url, integration_type, app_path, parameters)
                    LOGGER.info(f"Saved new integration with type: {integration_type}")
                
                # Clear fields and reload
                self._clear_fields()
                self._load_urls()
                
        except Exception as e:
            LOGGER.error(f"Error saving integration: {e}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", f"Could not save integration:\n{str(e)}")
            
    def _delete_url(self):
        """Delete selected URL"""
        current_item = self.url_list.currentItem()
        if not current_item:
            return
            
        data = current_item.data(Qt.UserRole)
        from PyQt5.QtWidgets import QMessageBox
        reply = QMessageBox.question(self, "Confirm Delete", 
                                    f"Delete URL '{data['name']}'?", 
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self._delete_selected_url()
            
    def _delete_selected_url(self):
        """Delete the currently selected URL"""
        current_item = self.url_list.currentItem()
        if not current_item:
            return
            
        data = current_item.data(Qt.UserRole)
        try:
            parent = self.parent()
            if parent and hasattr(parent, 'db') and parent.db:
                parent.db.delete_custom_url(data["name"])
                self._load_urls()
        except Exception as e:
            LOGGER.error(f"Error deleting custom URL: {e}")


class CityManagerDialog(QDialog):
    def __init__(self, current_cities: List[Dict], parent=None):
        super().__init__(parent)
        self.current_cities = current_cities
        self.setWindowTitle("Manage Cities")
        self.setModal(True)
        self.resize(500, 600)
        self._setup_ui()
        self._load_available_cities()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        available_group = QGroupBox("Available Cities")
        available_layout = QVBoxLayout(available_group)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search cities...")
        self.search_box.textChanged.connect(self._filter_cities)
        available_layout.addWidget(self.search_box)

        self.available_list = QListWidget()
        self.available_list.setSelectionMode(QListWidget.MultiSelection)
        available_layout.addWidget(self.available_list)
        self.available_list.itemDoubleClicked.connect(self._add_city_on_double_click)

        add_btn = QPushButton("Add Selected Cities")
        add_btn.clicked.connect(self._add_selected_cities)
        available_layout.addWidget(add_btn)
        layout.addWidget(available_group)

        current_group = QGroupBox("Current Cities")
        current_layout = QVBoxLayout(current_group)
        self.current_list = QListWidget()
        current_layout.addWidget(self.current_list)
        remove_btn = QPushButton("Remove Selected Cities")
        remove_btn.clicked.connect(self._remove_selected_cities)
        current_layout.addWidget(remove_btn)
        layout.addWidget(current_group)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._load_current_cities()

    def _load_available_cities(self):
        all_cities = [
            ("UTC", "UTC"),
            ("America/New_York", "New York"),
            ("America/Los_Angeles", "San Francisco"),
            ("America/Chicago", "Houston"),
            ("America/Chicago", "Chicago"),
            ("America/Denver", "Denver"),
            ("America/Toronto", "Toronto"),
            ("America/Vancouver", "Vancouver"),
            ("America/Mexico_City", "Mexico City"),
            ("America/Sao_Paulo", "São Paulo"),
            ("America/Buenos_Aires", "Buenos Aires"),
            ("Europe/London", "London"),
            ("Europe/Paris", "Paris"),
            ("Europe/Madrid", "Madrid"),
            ("Europe/Berlin", "Berlin"),
            ("Europe/Rome", "Rome"),
            ("Europe/Amsterdam", "Amsterdam"),
            ("Europe/Zurich", "Zurich"),
            ("Europe/Stockholm", "Stockholm"),
            ("Europe/Moscow", "Moscow"),
            ("Asia/Dubai", "Dubai"),
            ("Asia/Riyadh", "Riyadh"),
            ("Asia/Kuwait", "Kuwait"),
            ("Asia/Qatar", "Doha"),
            ("Asia/Singapore", "Singapore"),
            ("Asia/Hong_Kong", "Hong Kong"),
            ("Asia/Tokyo", "Tokyo"),
            ("Asia/Shanghai", "Shanghai"),
            ("Asia/Beijing", "Beijing"),
            ("Asia/Seoul", "Seoul"),
            ("Asia/Bangkok", "Bangkok"),
            ("Asia/Jakarta", "Jakarta"),
            ("Asia/Manila", "Manila"),
            ("Asia/Kolkata", "Mumbai"),
            ("Asia/Delhi", "Delhi"),
            ("Asia/Karachi", "Karachi"),
            ("Australia/Sydney", "Sydney"),
            ("Australia/Melbourne", "Melbourne"),
            ("Australia/Perth", "Perth"),
            ("Australia/Brisbane", "Brisbane"),
            ("Pacific/Auckland", "Auckland"),
            ("Pacific/Fiji", "Fiji"),
            ("Africa/Cairo", "Cairo"),
            ("Africa/Johannesburg", "Johannesburg"),
            ("Africa/Lagos", "Lagos"),
            ("Africa/Casablanca", "Casablanca"),
        ]
        self.all_cities = all_cities
        self._update_available_list()

    def _load_current_cities(self):
        self.current_list.clear()
        for city_data in self.current_cities:
            item = QListWidgetItem(f"{city_data['city']} ({city_data['timezone']})")
            item.setData(Qt.UserRole, city_data)
            self.current_list.addItem(item)

    def _filter_cities(self):
        self._update_available_list()

    def _update_available_list(self):
        self.available_list.clear()
        search_text = self.search_box.text().lower()
        current_tz_names = {city['timezone'] for city in self.current_cities}
        for tz_name, city_name in self.all_cities:
            if tz_name in current_tz_names:
                continue
            if search_text and search_text not in city_name.lower():
                continue
            item = QListWidgetItem(f"{city_name} ({tz_name})")
            item.setData(Qt.UserRole, {'timezone': tz_name, 'city': city_name})
            self.available_list.addItem(item)

    def _add_city_on_double_click(self, item):
        city_data = item.data(Qt.UserRole)
        if city_data and city_data not in self.current_cities:
            self.current_cities.append(city_data)
            self._load_current_cities()
            self._update_available_list()

    def _add_selected_cities(self):
        selected_items = self.available_list.selectedItems()
        for item in selected_items:
            city_data = item.data(Qt.UserRole)
            self.current_cities.append(city_data)
        self._load_current_cities()
        self._update_available_list()

    def _remove_selected_cities(self):
        selected_items = self.current_list.selectedItems()
        for item in selected_items:
            city_data = item.data(Qt.UserRole)
            if city_data in self.current_cities:
                self.current_cities.remove(city_data)
        self._load_current_cities()
        self._update_available_list()

class WorldClockTab(QWidget):
    def __init__(self, db=None, dark_mode: bool = False):
        super().__init__()
        self.db = db
        self.timezone_widgets: List[TimeZoneWidget] = []
        self.pinned_widgets: List[TimeZoneWidget] = []  # Pinned cities (max 3)
        self.current_time = datetime.datetime.now()
        self.current_date = QDate.currentDate()
        self.local_timezone = pytz.timezone('UTC')
        self.dark_mode = dark_mode
        self._updating_slider = False  # Prevent recursive calls during slider updates

        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_all_times)
        self.update_timer.start(1000)

        self._detect_local_timezone()
        self._setup_ui()
        self._load_saved_cities()
        self.reset_to_current_time()

    def update_theme(self, dark_mode: bool):
        self.dark_mode = dark_mode
        for w in self.timezone_widgets:
            w.update_styles(dark_mode)
        # Style the refresh button per theme
        if hasattr(self, 'current_time_btn'):
            self.current_time_btn.setStyleSheet(
                "background-color: #2A2A2A; color: #ffffff; border: 1px solid #444; border-radius: 6px; padding: 8px 12px;" if dark_mode else
                "background-color: #e9f2ff; color: #0b5ed7; border: 1px solid #b6d4fe; border-radius: 6px; padding: 8px 12px;"
            )
        # Update instruction text color per theme
        if hasattr(self, 'instruction_note'):
            self.instruction_note.setStyleSheet(
                "color: #ffffff; font-style: italic; margin-bottom: 6px;" if dark_mode else
                "color: #0b5ed7; font-style: italic; margin-bottom: 6px;"
            )

    def _detect_local_timezone(self):
        try:
            import time
            local_offset = time.timezone if time.daylight == 0 else time.altzone
            local_offset_hours = -local_offset / 3600
            for tz_name in pytz.all_timezones:
                tz = pytz.timezone(tz_name)
                now = datetime.datetime.now()
                offset = tz.utcoffset(now).total_seconds() / 3600
                if offset == local_offset_hours:
                    self.local_timezone = tz
                    break
            else:
                self.local_timezone = pytz.utc
        except Exception as e:
            LOGGER.warning(f"Could not detect local timezone: {e}")
            self.local_timezone = pytz.utc

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        title_label = QLabel("World Clock")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setStyleSheet("color: #63b3ed; margin-bottom: 10px;" if self.dark_mode else "color: #007bff; margin-bottom: 10px;")
        main_layout.addWidget(title_label)

        # Use double ampersand to render '&' literally (avoid mnemonic underscore)
        time_group = QGroupBox("Time && Date Selection")
        time_layout = QVBoxLayout(time_group)

        # Instruction note
        self.instruction_note = QLabel("To create a Teams meet or launch custom booking URL, please select the date and time of the preferred city and right-click to schedule.")
        self.instruction_note.setWordWrap(True)
        self.instruction_note.setStyleSheet("color: #ffffff; font-style: italic; margin-bottom: 6px;" if self.dark_mode else "color: #0b5ed7; font-style: italic; margin-bottom: 6px;")
        self.instruction_note.setAlignment(Qt.AlignCenter)
        time_layout.addWidget(self.instruction_note)

        # Centered date/time controls row
        datetime_row = QHBoxLayout()
        datetime_row.setSpacing(8)
        # left spacer
        datetime_row.addStretch()
        date_label = QLabel("Date:")
        date_label.setFont(QFont("Arial", 10, QFont.Bold))
        datetime_row.addWidget(date_label)

        self.date_edit = QDateEdit()
        self.date_edit.setFont(QFont("Arial", 10))
        self.date_edit.setDate(self.current_date)
        self.date_edit.setCalendarPopup(True)
        self.date_edit.dateChanged.connect(self.on_date_changed)
        datetime_row.addWidget(self.date_edit)

        datetime_row.addSpacing(20)

        time_label = QLabel("Time:")
        time_label.setFont(QFont("Arial", 10, QFont.Bold))
        datetime_row.addWidget(time_label)

        from PyQt5.QtCore import QTime
        self.time_edit = QTimeEdit()
        self.time_edit.setFont(QFont("Arial", 10))
        self.time_edit.setTime(QTime(self.current_time.hour, self.current_time.minute))
        self.time_edit.timeChanged.connect(self.on_time_changed)
        # Hour decrement/increment buttons to the left of time edit
        self.btn_hour_dec = QPushButton("▼")
        self.btn_hour_dec.setFixedWidth(24)
        self.btn_hour_dec.setToolTip("Hour -1")
        self.btn_hour_dec.clicked.connect(lambda: self.adjust_time(hours=-1))
        self.btn_hour_inc = QPushButton("▲")
        self.btn_hour_inc.setFixedWidth(24)
        self.btn_hour_inc.setToolTip("Hour +1")
        self.btn_hour_inc.clicked.connect(lambda: self.adjust_time(hours=+1))
        datetime_row.addWidget(self.btn_hour_dec)
        datetime_row.addWidget(self.btn_hour_inc)

        datetime_row.addWidget(self.time_edit)

        # Minute decrement/increment buttons to the right of time edit
        self.btn_min_dec = QPushButton("▼")
        self.btn_min_dec.setFixedWidth(24)
        self.btn_min_dec.setToolTip("Minute -15")
        self.btn_min_dec.clicked.connect(lambda: self.adjust_time(minutes=-15))
        self.btn_min_inc = QPushButton("▲")
        self.btn_min_inc.setFixedWidth(24)
        self.btn_min_inc.setToolTip("Minute +15")
        self.btn_min_inc.clicked.connect(lambda: self.adjust_time(minutes=+15))
        datetime_row.addWidget(self.btn_min_dec)
        datetime_row.addWidget(self.btn_min_inc)

        # right spacer
        datetime_row.addStretch()

        self.current_time_btn = QPushButton("Click here to refresh the Current time")
        self.current_time_btn.setFont(QFont("Arial", 11, QFont.Bold))
        self.current_time_btn.clicked.connect(self.reset_to_current_time)
        datetime_row.addWidget(self.current_time_btn)

        time_layout.addLayout(datetime_row)

        slider_layout = QHBoxLayout()
        slider_label = QLabel("Quick Time Selection:")
        slider_layout.addWidget(slider_label)

        self.time_slider = QSlider(Qt.Horizontal)
        self.time_slider.setMinimum(0)
        self.time_slider.setMaximum(24 * 60 - 1)
        self.time_slider.setTickPosition(QSlider.TicksBelow)
        # 15-minute granularity for a single step
        self.time_slider.setTickInterval(15)
        self.time_slider.setSingleStep(15)
        self.time_slider.setPageStep(60)
        self.time_slider.valueChanged.connect(self.on_slider_changed)
        slider_layout.addWidget(self.time_slider)

        self.local_time_label = QLabel("Local Time: --:--")
        # Initial emphasis; will also be updated by update_theme
        self.local_time_label.setFont(QFont("Arial", 12, QFont.Bold))
        slider_layout.addWidget(self.local_time_label)

        time_layout.addLayout(slider_layout)
        main_layout.addWidget(time_group)

        self.cities_btn = QPushButton("Manage Cities")
        self.cities_btn.setFont(QFont("Arial", 10))
        self.cities_btn.clicked.connect(self.manage_cities)
        main_layout.addWidget(self.cities_btn)

        # Pinned Cities Section
        pinned_group = QGroupBox("📍 Pinned Cities (Double-click to pin, max 3)")
        pinned_layout = QVBoxLayout(pinned_group)
        
        # Pinned cities container (horizontal layout)
        self.pinned_container = QWidget()
        self.pinned_layout = QHBoxLayout(self.pinned_container)
        self.pinned_layout.setSpacing(10)
        pinned_layout.addWidget(self.pinned_container)
        
        # Instructions for pinned section
        self.pinned_info = QLabel("Double-click any city below to pin it here")
        self.pinned_info.setStyleSheet("color: #6c757d; font-style: italic; font-size: 9px; margin: 5px 0;")
        self.pinned_info.setAlignment(Qt.AlignCenter)
        pinned_layout.addWidget(self.pinned_info)
        
        main_layout.addWidget(pinned_group)

        # Main Cities Section
        main_group = QGroupBox("🌍 World Cities (Right-click for meetings)")
        main_layout.addWidget(main_group)

        # Single row scrollable area for main cities
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setMaximumHeight(150)  # Limit height for single row
        
        self.timezone_container = QWidget()
        self.timezone_layout = QHBoxLayout(self.timezone_container)  # Changed to QHBoxLayout
        self.timezone_layout.setSpacing(10)
        self.timezone_layout.addStretch()  # Add stretch to push cities to the left
        scroll_area.setWidget(self.timezone_container)
        main_layout.addWidget(scroll_area)

    def _load_saved_cities(self):
        # Use existing world_clocks table if available via self.db
        default_cities = [
            {"timezone": "America/New_York", "city": "New York"},
            {"timezone": "Europe/London", "city": "London"},
            {"timezone": "Europe/Paris", "city": "Paris"},
            {"timezone": "Asia/Dubai", "city": "Dubai"},
            {"timezone": "Asia/Singapore", "city": "Singapore"},
            {"timezone": "Asia/Tokyo", "city": "Tokyo"},
            {"timezone": "Australia/Sydney", "city": "Sydney"},
        ]
        cities = default_cities
        if self.db:
            try:
                entries = self.db.get_world_clocks()
                if entries:
                    cities = [{"timezone": e['timezone'], "city": e['city']} for e in entries]
            except Exception as e:
                LOGGER.warning(f"Could not load cities from DB: {e}")
        self._create_timezone_widgets(cities)

    def _create_timezone_widgets(self, cities: List[Dict]):
        """Create timezone widgets safely"""
        try:
            # Clean up existing widgets safely
            if hasattr(self, 'timezone_widgets'):
                for w in self.timezone_widgets:
                    if w:
                        w.setParent(None)
                        w.deleteLater()
                self.timezone_widgets.clear()
            
            # Sort east→west by current UTC offset (descending) for the selected date/time
            try:
                cities_sorted = sorted(cities, key=lambda c: self._tz_offset_minutes(c['timezone']), reverse=True)
            except Exception:
                cities_sorted = cities

            local_tz_name = self.local_timezone.zone
            
            # Create timezone widgets for each city
            for i, city_data in enumerate(cities_sorted):
                self._add_timezone_widget(city_data['city'], city_data['timezone'])
        except Exception as e:
            LOGGER.error(f"Error creating timezone widgets: {e}")
            
    def _add_timezone_widget(self, city_name: str, timezone_name: str, use_dst: int = 1, is_pinned: bool = False):
        """Add a timezone widget to the display"""
        widget = TimeZoneWidget(timezone_name, city_name, is_local=False)
        widget.update_time(self.current_time, self.local_timezone)
        widget.update_styles(self.dark_mode)
        widget.setContextMenuPolicy(Qt.CustomContextMenu)
        widget.customContextMenuRequested.connect(self._show_context_menu)
        
        # Add double-click handler for pinning
        widget.mouseDoubleClickEvent = lambda e: self._on_widget_double_clicked(widget, e)
        
        # Different styling for pinned vs regular widgets
        if is_pinned:
            # Make pinned widgets larger and add close button
            widget.setFixedSize(200, 120)
            widget.setStyleSheet("TimeZoneWidget { border: 2px solid #007bff; border-radius: 10px; background: #f8f9fa; }")
            
            # Add close button to pinned widget
            close_btn = QPushButton("×", widget)
            close_btn.setFixedSize(20, 20)
            close_btn.move(widget.width() - 25, 5)
            close_btn.setStyleSheet("QPushButton { background: #dc3545; color: white; border: none; border-radius: 10px; font-weight: bold; }")
            close_btn.clicked.connect(lambda: self._unpin_city(widget))
            
            # Add to pinned layout
            self.pinned_layout.insertWidget(self.pinned_layout.count() - 1, widget)  # Insert before stretch
            self.pinned_widgets.append(widget)
        else:
            # Regular widget size
            widget.setFixedSize(150, 100)
            
            # Add to main layout (insert before stretch)
            self.timezone_layout.insertWidget(self.timezone_layout.count() - 1, widget)
            self.timezone_widgets.append(widget)

    def _on_widget_double_clicked(self, widget, event):
        """Handle double-click to pin a city"""
        # Only allow pinning from regular widgets, not already pinned ones
        if widget in self.timezone_widgets and len(self.pinned_widgets) < 3:
            self._pin_city(widget)
        elif len(self.pinned_widgets) >= 3:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(self, "Maximum Pinned Cities", "You can only pin up to 3 cities. Remove a pinned city first.")

    def _pin_city(self, widget):
        """Pin a city to the pinned section"""
        try:
            # Remove from main layout
            self.timezone_layout.removeWidget(widget)
            self.timezone_widgets.remove(widget)
            
            # Remove the widget from old parent
            widget.setParent(None)
            
            # Create new pinned widget with same data
            self._add_timezone_widget(widget.city_name, widget.timezone_name, is_pinned=True)
            
            # Sort pinned widgets east to west
            self._sort_pinned_cities()
            
            # Update pinned info
            if len(self.pinned_widgets) >= 3:
                self.pinned_info.setText("Maximum pinned cities reached")
            else:
                self.pinned_info.setText(f"Pinned {len(self.pinned_widgets)}/3 cities")
                
            # Update times
            self.update_all_times()
            
        except Exception as e:
            LOGGER.error(f"Error pinning city: {e}")
            
    def _sort_pinned_cities(self):
        """Sort pinned cities east to west"""
        if len(self.pinned_widgets) <= 1:
            return
            
        try:
            # Get current pinned cities data
            pinned_cities = []
            for widget in self.pinned_widgets:
                pinned_cities.append({
                    'city': widget.city_name,
                    'timezone': widget.timezone_name,
                    'widget': widget
                })
            
            # Sort east to west (reverse=True for east to west)
            pinned_cities.sort(key=lambda c: self._tz_offset_minutes(c['timezone']), reverse=True)
            
            # Clear and re-add widgets in sorted order
            for widget in self.pinned_widgets:
                self.pinned_layout.removeWidget(widget)
            
            self.pinned_widgets.clear()
            
            for city_data in pinned_cities:
                widget = city_data['widget']
                self.pinned_layout.insertWidget(self.pinned_layout.count() - 1, widget)  # Insert before stretch
                self.pinned_widgets.append(widget)
                
        except Exception as e:
            LOGGER.error(f"Error sorting pinned cities: {e}")

    def _unpin_city(self, widget):
        """Unpin a city from the pinned section"""
        try:
            # Remove from pinned layout
            self.pinned_layout.removeWidget(widget)
            self.pinned_widgets.remove(widget)
            
            # Remove the widget from old parent
            widget.setParent(None)
            
            # Add back to main layout
            self._add_timezone_widget(widget.city_name, widget.timezone_name, is_pinned=False)
            
            # Update pinned info
            if len(self.pinned_widgets) == 0:
                self.pinned_info.setText("Double-click any city below to pin it here")
            else:
                self.pinned_info.setText(f"Pinned {len(self.pinned_widgets)}/3 cities")
                
            # Update times
            self.update_all_times()
            
        except Exception as e:
            LOGGER.error(f"Error unpinning city: {e}")

    def update_all_times(self):
        """Update times for both pinned and regular widgets"""
        # Update pinned widgets
        for widget in self.pinned_widgets:
            widget.update_time(self.current_time, self.local_timezone)
        
        # Update regular widgets
        for widget in self.timezone_widgets:
            widget.update_time(self.current_time, self.local_timezone)

    def on_date_changed(self, date):
        self.current_date = date
        self._resort_current_cities()
        self.update_all_times()

    def on_time_changed(self, time):
        minutes_since_midnight = time.hour() * 60 + time.minute()
        self.time_slider.setValue(minutes_since_midnight)
        python_date = self.current_date.toPyDate()
        self.current_time = datetime.datetime.combine(python_date, datetime.time(time.hour(), time.minute(), 0))
        self.local_time_label.setText(f"Local Time: {time.toString('HH:mm')}")
        self._resort_current_cities()
        self.update_all_times()

    def on_slider_changed(self, value):
        # Prevent recursive calls during slider updates
        if self._updating_slider:
            return
            
        self._updating_slider = True
        
        try:
            # Snap dragged value to nearest 15-minute step
            snapped = int(round(value / 15.0) * 15)
            # Clamp to [0, 24*60-1] to avoid 24:00
            max_minute = 24 * 60 - 1
            if snapped < 0:
                snapped = 0
            elif snapped > max_minute:
                snapped = max_minute
            if snapped != value:
                self.time_slider.blockSignals(True)
                self.time_slider.setValue(snapped)
                self.time_slider.blockSignals(False)
                value = snapped
            hours = value // 60
            minutes = value % 60
            python_date = self.current_date.toPyDate()
            slider_time = datetime.datetime.combine(python_date, datetime.time(hours, minutes, 0))
            self.local_time_label.setText(f"Local Time: {slider_time.strftime('%H:%M')}")
            self.current_time = slider_time
            from PyQt5.QtCore import QTime
            self.time_edit.blockSignals(True)
            self.time_edit.setTime(QTime(hours, minutes))
            self.time_edit.blockSignals(False)
            self._resort_current_cities()
            self.update_all_times()
        except Exception as e:
            LOGGER.error(f"Error in slider change: {e}")
        finally:
            self._updating_slider = False

    def reset_to_current_time(self):
        now = datetime.datetime.now()
        minutes_since_midnight = now.hour * 60 + now.minute
        self.time_slider.setValue(minutes_since_midnight)
        self.current_time = now
        self.current_date = QDate.currentDate()
        from PyQt5.QtCore import QTime
        self.date_edit.setDate(self.current_date)
        self.time_edit.setTime(QTime(now.hour, now.minute))
        self.local_time_label.setText(f"Local Time: {now.strftime('%H:%M')}")
        self.update_all_times()

    def _tz_offset_minutes(self, tz_name: str) -> int:
        """Get UTC offset in minutes for a timezone at the current selected date/time."""
        tz = pytz.timezone(tz_name)
        py_date = self.current_date.toPyDate()
        base_naive = datetime.datetime.combine(py_date, datetime.time(self.current_time.hour, self.current_time.minute, 0))
        base_local = self.local_timezone.localize(base_naive)
        tgt = base_local.astimezone(tz)
        off = tgt.utcoffset() or datetime.timedelta(0)
        return int(off.total_seconds() // 60)

    def _resort_current_cities(self):
        """Resort tiles by current UTC offset without changing the set of cities."""
        # Prevent crashes during rapid updates
        if not hasattr(self, 'timezone_widgets') or len(self.timezone_widgets) == 0:
            return
            
        try:
            cities = [{
                'timezone': w.timezone_name,
                'city': w.city_name
            } for w in self.timezone_widgets]
            if cities:
                self._create_timezone_widgets(cities)
        except Exception as e:
            LOGGER.error(f"Error in resort cities: {e}")

    def manage_cities(self):
        current_cities = [{
            'timezone': w.timezone_name,
            'city': w.city_name
        } for w in self.timezone_widgets]

        dialog = CityManagerDialog(current_cities, self)
        if dialog.exec_() == QDialog.Accepted:
            self.save_cities(dialog.current_cities)
            self._create_timezone_widgets(dialog.current_cities)
            self.update_all_times()

    def _show_context_menu(self, position):
        """Show context menu with meeting options"""
        # Get the widget that was right-clicked
        widget = self.sender()
        if not widget:
            # Try to get the widget at the position
            widget = self.childAt(position)
        
        # If still no widget, try to find the TimeZoneWidget that contains this position
        if not isinstance(widget, TimeZoneWidget):
            for tz_widget in self.timezone_widgets:
                if tz_widget.geometry().contains(position):
                    widget = tz_widget
                    break
                    
        if not isinstance(widget, TimeZoneWidget):
            return
            
        menu = QMenu(self)
        
        # Teams Meeting submenu
        teams_menu = menu.addMenu("Teams Meeting")
        
        # Teams Web Meeting
        teams_web_action = QAction("Create Teams Meeting (TeamsApp)", self)
        teams_web_action.triggered.connect(lambda: self._create_teams_meeting(widget))
        teams_menu.addAction(teams_web_action)
        
        # Teams Outlook Plugin - Manual approach
        teams_outlook_manual_action = QAction("Create Teams Meeting (Outlook Plugin - Manual)", self)
        teams_outlook_manual_action.triggered.connect(lambda: self._create_teams_outlook_meeting_manual(widget))
        teams_menu.addAction(teams_outlook_manual_action)
        
        # Custom URL options
        custom_urls = self.db.get_custom_urls()
        if custom_urls:
            menu.addSeparator()
            for url_name, url_data in custom_urls.items():
                url = url_data['url']
                integration_type = url_data.get('integration_type', 'email')
                app_path = url_data.get('app_path', '')
                parameters = url_data.get('parameters', '')
                
                if integration_type == "email":
                    if app_path and app_path.lower() != "default":
                        # Check if email app exists before adding menu item
                        if os.path.exists(app_path):
                            # Email invite option
                            action_text = f"Email Invite via {url_name}"
                            action = QAction(action_text, self)
                            action.triggered.connect(lambda checked, u=url, name=url_name, path=app_path: self._create_email_invite(widget, u, name, path))
                            menu.addAction(action)
                        else:
                            # Email app not found - show with warning
                            action_text = f"Email Invite via {url_name} (App Not Found)"
                            action = QAction(action_text, self)
                            action.setEnabled(False)  # Disable the action
                            menu.addAction(action)
                    elif app_path and app_path.lower() == "default":
                        # Default email client option
                        action_text = f"Email Invite via {url_name}"
                        action = QAction(action_text, self)
                        action.triggered.connect(lambda checked, u=url, name=url_name, path=app_path: self._create_email_invite(widget, u, name, path))
                        menu.addAction(action)
                    else:
                        # Direct URL launch option
                        action_text = f"Open {url_name}"
                        action = QAction(action_text, self)
                        action.triggered.connect(lambda checked, u=url, name=url_name: self._launch_custom_url(widget, u, name))
                        menu.addAction(action)
                elif integration_type in ["launcher", "url", "batch"]:
                    # Application/URL/Batch launcher
                    if integration_type == "launcher":
                        action_text = f"Launch {url_name}"
                    elif integration_type == "url":
                        action_text = f"Open {url_name}"
                    elif integration_type == "batch":
                        action_text = f"Run {url_name}"
                    
                    action = QAction(action_text, self)
                    action.triggered.connect(lambda checked, u=url, name=url_name, integration_type=integration_type, parameters=parameters: self._launch_integration(widget, u, name, integration_type, parameters))
                    menu.addAction(action)
        
        menu.exec(widget.mapToGlobal(position))
        
    def _create_teams_meeting(self, widget: TimeZoneWidget):
        """Create Teams meeting using the specified widget"""
        try:
            # Walk up parents to find the world clock tab with current_time/current_date/local_timezone
            parent = self
            while not (hasattr(parent, 'current_time') and hasattr(parent, 'current_date') and hasattr(parent, 'local_timezone')):
                parent = parent.parent()
            
            if not parent:
                QMessageBox.warning(self, "Error", "Could not access current time.")
                return
                
            current_time = parent.current_time
            current_date = parent.current_date
            # Combine date and time
            py_date = current_date.toPyDate()
            target_dt = datetime.datetime.combine(py_date, datetime.time(current_time.hour, current_time.minute, 0, 0))
            # Convert to target timezone to get intended meeting time
            tz = pytz.timezone(widget.timezone_name)
            local_tz = parent.local_timezone
            local_time = local_tz.localize(target_dt)
            target_time = local_time.astimezone(tz)
            local_meeting_time = target_time.astimezone(local_tz)
            # Format
            readable_target_time = target_time.strftime("%Y-%m-%d %H:%M")
            readable_local_time = local_meeting_time.strftime("%Y-%m-%d %H:%M")
            # Ask for duration in 15-min steps up to 8 hours
            duration_minutes = self._confirm_and_get_duration(readable_target_time, readable_local_time, widget.city_name)
            if duration_minutes is None:
                return
            start_time = local_meeting_time.strftime("%Y-%m-%dT%H:%M:00")
            end_time = (local_meeting_time + datetime.timedelta(minutes=duration_minutes)).strftime("%Y-%m-%dT%H:%M:00")
            subject = "NexthinkSupport"
            meeting_url = f"https://teams.microsoft.com/l/meeting/new?subject={subject}&startTime={start_time}&endTime={end_time}"
            webbrowser.open(meeting_url)
        except Exception as e:
            LOGGER.error(f"Error creating Teams meeting: {e}")
            QMessageBox.critical(self, "Error", f"Could not create Teams meeting: {e}")
        
    def _create_meeting(self, platform: str):
        """Create meeting using the specified platform"""
        try:
            # This method should be called from a TimeZoneWidget context
            # We need to get the widget that triggered this
            # For now, let's use the first timezone widget as a fallback
            if self.timezone_widgets:
                widget = self.timezone_widgets[0]
            else:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Error", "No timezone widgets available for meeting creation.")
                return
                
            # Walk up parents to find the world clock tab with current_time/current_date/local_timezone
            parent = self
            while not (hasattr(parent, 'current_time') and hasattr(parent, 'current_date') and hasattr(parent, 'local_timezone')):
                parent = parent.parent()
            
            if not parent:
                QMessageBox.warning(self, "Error", "Could not access current time.")
                return
                
            current_time = parent.current_time
            current_date = parent.current_date
            # Combine date and time
            py_date = current_date.toPyDate()
            target_dt = datetime.datetime.combine(py_date, datetime.time(current_time.hour, current_time.minute, 0, 0))
            # Convert to target timezone to get intended meeting time
            tz = pytz.timezone(widget.timezone_name)
            local_tz = parent.local_timezone
            local_time = local_tz.localize(target_dt)
            target_time = local_time.astimezone(tz)
            local_meeting_time = target_time.astimezone(local_tz)
            # Format
            readable_target_time = target_time.strftime("%Y-%m-%d %H:%M")
            readable_local_time = local_meeting_time.strftime("%Y-%m-%d %H:%M")
            # Ask for duration in 15-min steps up to 8 hours
            duration_minutes = self._confirm_and_get_duration(readable_target_time, readable_local_time, widget.city_name)
            if duration_minutes is None:
                return
            start_time = local_meeting_time.strftime("%Y-%m-%dT%H:%M:00")
            end_time = (local_meeting_time + datetime.timedelta(minutes=duration_minutes)).strftime("%Y-%m-%dT%H:%M:00")
            subject = "NexthinkSupport"
            meeting_url = f"https://teams.microsoft.com/l/meeting/new?subject={subject}&startTime={start_time}&endTime={end_time}"
            import webbrowser
            webbrowser.open(meeting_url)
        except Exception as e:
            LOGGER.error(f"Error creating {platform} meeting: {e}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"Could not create {platform} meeting: {e}")

    def on_date_changed(self, date):
        self.current_date = date
        self._resort_current_cities()
        self.update_all_times()

    def on_time_changed(self, time):
        minutes_since_midnight = time.hour() * 60 + time.minute()
        self.time_slider.setValue(minutes_since_midnight)
        python_date = self.current_date.toPyDate()
        self.current_time = datetime.datetime.combine(python_date, datetime.time(time.hour(), time.minute(), 0))
        self.local_time_label.setText(f"Local Time: {time.toString('HH:mm')}")
        self._resort_current_cities()
        self.update_all_times()

    def on_slider_changed(self, value):
        # Prevent recursive calls during slider updates
        if self._updating_slider:
            return
            
        self._updating_slider = True
        
        try:
            # Snap dragged value to nearest 15-minute step
            snapped = int(round(value / 15.0) * 15)
            # Clamp to [0, 24*60-1] to avoid 24:00
            max_minute = 24 * 60 - 1
            if snapped < 0:
                snapped = 0
            elif snapped > max_minute:
                snapped = max_minute
            if snapped != value:
                self.time_slider.blockSignals(True)
                self.time_slider.setValue(snapped)
                self.time_slider.blockSignals(False)
                value = snapped
            hours = value // 60
            minutes = value % 60
            python_date = self.current_date.toPyDate()
            slider_time = datetime.datetime.combine(python_date, datetime.time(hours, minutes, 0))
            self.local_time_label.setText(f"Local Time: {slider_time.strftime('%H:%M')}")
            self.current_time = slider_time
            from PyQt5.QtCore import QTime
            self.time_edit.blockSignals(True)
            self.time_edit.setTime(QTime(hours, minutes))
            self.time_edit.blockSignals(False)
            self._resort_current_cities()
            self.update_all_times()
        except Exception as e:
            LOGGER.error(f"Error in slider change: {e}")
        finally:
            self._updating_slider = False

    def reset_to_current_time(self):
        now = datetime.datetime.now()
        minutes_since_midnight = now.hour * 60 + now.minute
        self.time_slider.setValue(minutes_since_midnight)
        self.current_time = now
        self.current_date = QDate.currentDate()
        from PyQt5.QtCore import QTime
        self.date_edit.setDate(self.current_date)
        self.time_edit.setTime(QTime(now.hour, now.minute))
        self.local_time_label.setText(f"Local Time: {now.strftime('%H:%M')}")
        self.update_all_times()

    def adjust_time(self, hours: int = 0, minutes: int = 0):
        """Increment/decrement time by given hours/minutes."""
        dt = self.current_time
        dt = dt + datetime.timedelta(hours=hours, minutes=minutes)
        # Keep date consistent with date_edit selection
        py_date = self.current_date.toPyDate()
        dt = datetime.datetime.combine(py_date, dt.time())
        self.current_time = dt
        from PyQt5.QtCore import QTime
        self.time_edit.blockSignals(True)
        self.time_edit.setTime(QTime(self.current_time.hour, self.current_time.minute))
        self.time_edit.blockSignals(False)
        self.on_time_changed(self.time_edit.time())

    def _tz_offset_minutes(self, tz_name: str) -> int:
        """UTC offset (in minutes) for the given timezone at the currently selected date/time."""
        tz = pytz.timezone(tz_name)
        py_date = self.current_date.toPyDate()
        base_naive = datetime.datetime.combine(py_date, datetime.time(self.current_time.hour, self.current_time.minute, 0))
        base_local = self.local_timezone.localize(base_naive)
        tgt = base_local.astimezone(tz)
        off = tgt.utcoffset() or datetime.timedelta(0)
        return int(off.total_seconds() // 60)

    def _resort_current_cities(self):
        """Resort tiles by current UTC offset without changing the set of cities."""
        # Prevent crashes during rapid updates
        if not hasattr(self, 'timezone_widgets') or len(self.timezone_widgets) == 0:
            return
            
        try:
            cities = [{
                'timezone': w.timezone_name,
                'city': w.city_name
            } for w in self.timezone_widgets]
            if cities:
                self._create_timezone_widgets(cities)
        except Exception as e:
            LOGGER.error(f"Error in resort cities: {e}")

    def manage_cities(self):
        current_cities = [{
            'timezone': w.timezone_name,
            'city': w.city_name
        } for w in self.timezone_widgets]

        dialog = CityManagerDialog(current_cities, self)
        if dialog.exec_() == QDialog.Accepted:
            self.save_cities(dialog.current_cities)
            self._create_timezone_widgets(dialog.current_cities)
            self.update_all_times()

    def _show_context_menu(self, position):
        """Show context menu with meeting options"""
        # Get the widget that was right-clicked
        widget = self.sender()
        if not widget:
            # Try to get the widget at the position
            widget = self.childAt(position)
        
        # If still no widget, try to find the TimeZoneWidget that contains this position
        if not isinstance(widget, TimeZoneWidget):
            for tz_widget in self.timezone_widgets:
                if tz_widget.geometry().contains(position):
                    widget = tz_widget
                    break
                    
        if not isinstance(widget, TimeZoneWidget):
            return
            
        menu = QMenu(self)
        
        # Teams Meeting submenu
        teams_menu = menu.addMenu("Teams Meeting")
        
        # Teams Web Meeting
        teams_web_action = QAction("Create Teams Meeting (TeamsApp)", self)
        teams_web_action.triggered.connect(lambda: self._create_teams_meeting(widget))
        teams_menu.addAction(teams_web_action)
        
        # Teams Outlook Plugin - Manual approach
        teams_outlook_manual_action = QAction("Create Teams Meeting (Outlook Plugin - Manual)", self)
        teams_outlook_manual_action.triggered.connect(lambda: self._create_teams_outlook_meeting_manual(widget))
        teams_menu.addAction(teams_outlook_manual_action)
        
        # Custom URL options
        custom_urls = self.db.get_custom_urls()
        if custom_urls:
            menu.addSeparator()
            for url_name, url_data in custom_urls.items():
                url = url_data['url']
                integration_type = url_data.get('integration_type', 'email')
                app_path = url_data.get('app_path', '')
                parameters = url_data.get('parameters', '')
                
                if integration_type == "email":
                    if app_path and app_path.lower() != "default":
                        # Check if email app exists before adding menu item
                        if os.path.exists(app_path):
                            # Email invite option
                            action_text = f"Email Invite via {url_name}"
                            action = QAction(action_text, self)
                            action.triggered.connect(lambda checked, u=url, name=url_name, path=app_path: self._create_email_invite(widget, u, name, path))
                            menu.addAction(action)
                        else:
                            # Email app not found - show with warning
                            action_text = f"Email Invite via {url_name} (App Not Found)"
                            action = QAction(action_text, self)
                            action.setEnabled(False)  # Disable the action
                            menu.addAction(action)
                    elif app_path and app_path.lower() == "default":
                        # Default email client option
                        action_text = f"Email Invite via {url_name}"
                        action = QAction(action_text, self)
                        action.triggered.connect(lambda checked, u=url, name=url_name, path=app_path: self._create_email_invite(widget, u, name, path))
                        menu.addAction(action)
                    else:
                        # Direct URL launch option
                        action_text = f"Open {url_name}"
                        action = QAction(action_text, self)
                        action.triggered.connect(lambda checked, u=url, name=url_name: self._launch_custom_url(widget, u, name))
                        menu.addAction(action)
                elif integration_type in ["launcher", "url", "batch"]:
                    # Application/URL/Batch launcher
                    if integration_type == "launcher":
                        action_text = f"Launch {url_name}"
                    elif integration_type == "url":
                        action_text = f"Open {url_name}"
                    elif integration_type == "batch":
                        action_text = f"Run {url_name}"
                    
                    action = QAction(action_text, self)
                    action.triggered.connect(lambda checked, u=url, name=url_name, integration_type=integration_type, parameters=parameters: self._launch_integration(widget, u, name, integration_type, parameters))
                    menu.addAction(action)
        
        menu.exec(widget.mapToGlobal(position))
        
    def _create_teams_meeting(self, widget: TimeZoneWidget):
        """Create Teams meeting using the specified widget"""
        try:
            # Walk up parents to find the world clock tab with current_time/current_date/local_timezone
            parent = self
            while not (hasattr(parent, 'current_time') and hasattr(parent, 'current_date') and hasattr(parent, 'local_timezone')):
                parent = parent.parent()
            
            if not parent:
                QMessageBox.warning(self, "Error", "Could not access current time.")
                return
                
            current_time = parent.current_time
            current_date = parent.current_date
            # Combine date and time
            py_date = current_date.toPyDate()
            target_dt = datetime.datetime.combine(py_date, datetime.time(current_time.hour, current_time.minute, 0, 0))
            # Convert to target timezone to get intended meeting time
            tz = pytz.timezone(widget.timezone_name)
            local_tz = parent.local_timezone
            local_time = local_tz.localize(target_dt)
            target_time = local_time.astimezone(tz)
            local_meeting_time = target_time.astimezone(local_tz)
            # Format
            readable_target_time = target_time.strftime("%Y-%m-%d %H:%M")
            readable_local_time = local_meeting_time.strftime("%Y-%m-%d %H:%M")
            # Ask for duration in 15-min steps up to 8 hours
            duration_minutes = self._confirm_and_get_duration(readable_target_time, readable_local_time, widget.city_name)
            if duration_minutes is None:
                return
            start_time = local_meeting_time.strftime("%Y-%m-%dT%H:%M:00")
            end_time = (local_meeting_time + datetime.timedelta(minutes=duration_minutes)).strftime("%Y-%m-%dT%H:%M:00")
            subject = "NexthinkSupport"
            meeting_url = f"https://teams.microsoft.com/l/meeting/new?subject={subject}&startTime={start_time}&endTime={end_time}"
            webbrowser.open(meeting_url)
        except Exception as e:
            LOGGER.error(f"Error creating Teams meeting: {e}")
            QMessageBox.critical(self, "Error", f"Could not create Teams meeting: {e}")

    def _confirm_and_get_duration(self, readable_target_time: str, readable_local_time: str, city_name: str) -> int:
        """Show a confirmation dialog with duration selection. Returns minutes or None if cancelled."""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Confirm Meeting")
        dialog.setModal(True)
        layout = QVBoxLayout(dialog)
        
        # Show time information
        info = QLabel(f"Meeting for {city_name}")
        info.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(info)
        
        time_info = QLabel(f"Target time: {readable_target_time}")
        layout.addWidget(time_info)
        
        local_time_info = QLabel(f"Local time: {readable_local_time}")
        layout.addWidget(local_time_info)
        
        # Duration selection
        duration_label = QLabel("Duration:")
        layout.addWidget(duration_label)
        
        duration_combo = QComboBox()
        for minutes in range(15, 8*60+1, 15):  # 15 min to 8 hours in 15-min steps
            hours = minutes // 60
            mins = minutes % 60
            if hours > 0:
                text = f"{hours}h" + (f" {mins}m" if mins > 0 else "")
            else:
                text = f"{mins}m"
            duration_combo.addItem(text, minutes)
        duration_combo.setCurrentIndex(3)  # Default to 1 hour
        layout.addWidget(duration_combo)
        
        # Buttons
        button_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        ok_btn = QPushButton("Create Meeting")
        ok_btn.setDefault(True)
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(ok_btn)
        layout.addLayout(button_layout)
        
        cancel_btn.clicked.connect(dialog.reject)
        ok_btn.clicked.connect(dialog.accept)
        
        if dialog.exec_() == QDialog.Accepted:
            return duration_combo.currentData()
        return None
        
    def _launch_integration(self, widget: TimeZoneWidget, url: str, name: str, integration_type: str, parameters: str):
        """Launch integration with parameter substitution"""
        try:
            import subprocess
            import webbrowser
            from urllib.parse import quote
            
            # Get available parameters for substitution
            param_mapping = {
                '%wc_city_name%': widget.city_name,
                '%wc_timezone%': widget.timezone_name,
                '%wc_local_time%': self.current_time.strftime('%Y-%m-%d %H:%M'),
                '%wc_target_time%': widget.get_target_time().strftime('%Y-%m-%d %H:%M'),
                '%wc_date%': self.current_time.strftime('%Y-%m-%d'),
                '%wc_time%': self.current_time.strftime('%H:%M'),
                '%wc_year%': str(self.current_time.year),
                '%wc_month%': str(self.current_time.month).zfill(2),
                '%wc_day%': str(self.current_time.day).zfill(2),
                '%wc_hour%': str(self.current_time.hour).zfill(2),
                '%wc_minute%': str(self.current_time.minute).zfill(2),
            }
            
            # Substitute parameters in URL
            final_url = url
            for param, value in param_mapping.items():
                final_url = final_url.replace(param, str(value))
            
            # Substitute parameters in parameters string
            final_params = parameters
            for param, value in param_mapping.items():
                final_params = final_params.replace(param, str(value))
            
            # Remove leading slash if present (common when users want to append to URL path)
            if final_params.startswith('/'):
                final_params = final_params[1:]
            
            if integration_type == "launcher":
                # Launch application with parameters
                if final_params:
                    subprocess.run([final_url, final_params], check=False)
                else:
                    subprocess.run([final_url], check=False)
                LOGGER.info(f"Launched application: {final_url} with params: {final_params}")
                
            elif integration_type == "url":
                # Open URL in browser
                if final_params:
                    # Check if URL already ends with = (like Google search)
                    if final_url.endswith('='):
                        # Directly append parameters without separator
                        final_url = f"{final_url}{final_params}"
                    else:
                        # Use proper separator for other URLs
                        separator = "&" if "?" in final_url else "?"
                        # URL encode the parameters
                        encoded_params = quote(final_params, safe='+')
                        final_url = f"{final_url}{separator}{encoded_params}"
                webbrowser.open(final_url)
                LOGGER.info(f"Opened URL: {final_url}")
                LOGGER.info(f"Original URL: {url}")
                LOGGER.info(f"Parameters: {parameters}")
                LOGGER.info(f"Final params after substitution: {final_params}")
                
            elif integration_type == "batch":
                # Run batch file with parameters
                if final_params:
                    subprocess.run([final_url, final_params], shell=True, check=False)
                else:
                    subprocess.run([final_url], shell=True, check=False)
                LOGGER.info(f"Ran batch file: {final_url} with params: {final_params}")
                
        except Exception as e:
            LOGGER.error(f"Error launching integration: {e}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Launch Error", f"Could not launch integration:\n{str(e)}")
            
    def _launch_custom_url(self, widget: TimeZoneWidget, url: str, service_name: str):
        """Launch custom URL with meeting details"""
        try:
            import webbrowser
            from urllib.parse import quote, urlparse
            
            # Get meeting details from widget and parent
            meeting_time = self.current_time
            city_name = widget.city_name
            
            # Format the time for URL
            formatted_time = meeting_time.strftime("%Y-%m-%d %H:%M")
            
            # For email integrations without app path, just open the URL directly
            # No need to add extra parameters - let the user handle them in the URL configuration
            final_url = url
            
            # Launch the URL
            webbrowser.open(final_url)
            LOGGER.info(f"Launched custom URL: {final_url}")
            
        except Exception as e:
            LOGGER.error(f"Error launching custom URL: {e}")
            # Show error message to user
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "URL Launch Error", f"Could not launch the custom URL:\n{str(e)}")
            
    def _create_email_invite(self, widget: TimeZoneWidget, url: str, email_app_path: str, service_name: str):
        """Create email invite with URL using specified email app"""
        try:
            import subprocess
            from urllib.parse import quote
            from PyQt5.QtWidgets import QMessageBox
            
            # Walk up parents to find the world clock tab with current_time/current_date/local_timezone
            parent = self
            while not (hasattr(parent, 'current_time') and hasattr(parent, 'current_date') and hasattr(parent, 'local_timezone')):
                parent = parent.parent()
            
            if not parent:
                QMessageBox.warning(self, "Error", "Could not access current time.")
                return
                
            current_time = parent.current_time
            current_date = parent.current_date
            city_name = widget.city_name
            
            # Combine date and time
            py_date = current_date.toPyDate()
            target_dt = datetime.datetime.combine(py_date, datetime.time(current_time.hour, current_time.minute, 0, 0))
            
            # Convert to target timezone to get intended meeting time
            tz = pytz.timezone(widget.timezone_name)
            local_tz = parent.local_timezone
            local_time = local_tz.localize(target_dt)
            target_time = local_time.astimezone(tz)
            
            # Format times for display
            readable_target_time = target_time.strftime("%Y-%m-%d %H:%M")
            readable_local_time = local_time.strftime("%Y-%m-%d %H:%M")
            
            # Show confirmation dialog
            reply = QMessageBox.question(self, "Create Email Invite", 
                f"Ready to create email invite:\n\n"
                f"City: {city_name}\n"
                f"Target Time: {readable_target_time} ({city_name} timezone)\n"
                f"Your Local Time: {readable_local_time}\n\n"
                f"The email will contain only the meeting URL.")
            
            if reply == QMessageBox.Yes:
                # Create email body only - no subject
                body = quote(f"Meeting URL: {url}")
                
                # Create mailto URL with only body
                mailto_url = f"mailto:?body={body}"
                
                # Validate email app path before launching
                if email_app_path.lower() == "default":
                    # Use default email client
                    import webbrowser
                    webbrowser.open(mailto_url)
                    LOGGER.info(f"Created email invite via default email client for {service_name}")
                    
                    # Show success message
                    QMessageBox.information(self, "Email Created", 
                        f"Email invite created!\n\n"
                        f"The email has been opened in your default email client.\n\n"
                        f"It contains only the meeting URL for {city_name}.")
                else:
                    # Check if email app exists with better error handling
                    try:
                        # Normalize the path and check existence
                        normalized_path = os.path.normpath(email_app_path)
                        path_exists = os.path.exists(normalized_path)
                        outlook_found = False  # Initialize outlook_found
                        
                        LOGGER.info(f"Checking email app path: {normalized_path}")
                        LOGGER.info(f"Path exists: {path_exists}")
                        
                        if not path_exists:
                            # Try common Outlook paths as fallback
                            common_outlook_paths = [
                                r"C:\Program Files\Microsoft Office\root\Office16\OUTLOOK.EXE",
                                r"C:\Program Files (x86)\Microsoft Office\root\Office16\OUTLOOK.EXE",
                                r"C:\Program Files\Microsoft Office\Office16\OUTLOOK.EXE",
                                r"C:\Program Files (x86)\Microsoft Office\Office16\OUTLOOK.EXE"
                            ]
                            
                            for path in common_outlook_paths:
                                if os.path.exists(path):
                                    LOGGER.info(f"Found Outlook at common path: {path}")
                                    normalized_path = path
                                    path_exists = True
                                    outlook_found = True
                                    break
                        
                        if not outlook_found:
                            from PyQt5.QtWidgets import QMessageBox
                            QMessageBox.warning(self, "Email App Not Found", 
                                f"The email application could not be found:\n{email_app_path}\n\n"
                                f"Please check the email app path in the Custom URL Manager.\n"
                                f"Using default email client instead.")
                            # Fallback to default email client
                            import webbrowser
                            webbrowser.open(mailto_url)
                            LOGGER.info(f"Fallback to default email client for {service_name}")
                            return
                        
                        # Launch email app
                        if "outlook.exe" in normalized_path.lower():
                            # Outlook special handling
                            subprocess.run([normalized_path, "/c", "ipm.note", "/m", mailto_url], check=False)
                            LOGGER.info(f"Launched email invite via Outlook for {service_name}")
                            
                            # Show success message
                            QMessageBox.information(self, "Email Created", 
                                f"Email invite created!\n\n"
                                f"Outlook has been opened with a new email.\n\n"
                                f"It contains only the meeting URL for {city_name}.")
                        else:
                            # Generic email app
                            subprocess.run([normalized_path, mailto_url], check=False)
                            LOGGER.info(f"Launched email invite via {service_name}")
                            
                            # Show success message
                            QMessageBox.information(self, "Email Created", 
                                f"Email invite created!\n\n"
                                f"The email application has been opened.\n\n"
                                f"It contains only the meeting URL for {city_name}.")
                    
                    except Exception as path_error:
                        LOGGER.error(f"Error validating email app path: {path_error}")
                        # Fallback to default email client
                        import webbrowser
                        webbrowser.open(mailto_url)
                        LOGGER.info(f"Fallback to default email client for {service_name} due to path error")
            
        except Exception as e:
            LOGGER.error(f"Error creating email invite: {e}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Email Error", 
                f"Could not create email invite:\n{str(e)}\n\n"
                f"Please check the email app configuration in the Custom URL Manager.")
            
    def _create_outlook_meeting(self, widget: TimeZoneWidget):
        """Create Outlook meeting directly"""
        try:
            import subprocess
            from PyQt5.QtWidgets import QMessageBox
            
            # Walk up parents to find the world clock tab with current_time/current_date/local_timezone
            parent = self
            while not (hasattr(parent, 'current_time') and hasattr(parent, 'current_date') and hasattr(parent, 'local_timezone')):
                parent = parent.parent()
            
            if not parent:
                QMessageBox.warning(self, "Error", "Could not access current time.")
                return
                
            # Get meeting details
            meeting_time = parent.current_time
            city_name = widget.city_name
            formatted_time = meeting_time.strftime("%Y-%m-%d %H:%M")
            
            # Create meeting details
            subject = f"Meeting - {city_name}"
            body = f"Meeting scheduled for {city_name}\nTime: {formatted_time} ({city_name} timezone)"
            
            # Try to find Outlook
            outlook_paths = [
                r"C:\Program Files\Microsoft Office\root\Office16\OUTLOOK.EXE",
                r"C:\Program Files (x86)\Microsoft Office\root\Office16\OUTLOOK.EXE",
                r"C:\Program Files\Microsoft Office\Office16\OUTLOOK.EXE",
                r"C:\Program Files (x86)\Microsoft Office\Office16\OUTLOOK.EXE"
            ]
            
            outlook_path = None
            for path in outlook_paths:
                if os.path.exists(path):
                    outlook_path = path
                    break
            
            if outlook_path:
                # Create appointment with meeting details
                subprocess.run([outlook_path, "/c", "ipm.appointment", "/subject", subject, "/body", body], check=False)
                LOGGER.info(f"Created Outlook meeting for {city_name}")
            else:
                QMessageBox.warning(self, "Outlook Not Found", "Microsoft Outlook could not be found. Please install Outlook or check the installation path.")
                
        except Exception as e:
            LOGGER.error(f"Error creating Outlook meeting: {e}")
            QMessageBox.warning(self, "Outlook Error", f"Could not create Outlook meeting:\n{str(e)}")
            
    def _create_teams_outlook_meeting_manual(self, widget: TimeZoneWidget):
        """Create Teams meeting using Outlook plugin with manual time setting"""
        try:
            import subprocess
            from PyQt5.QtWidgets import QMessageBox
            from PyQt5.QtCore import QTime
            
            # Walk up parents to find the world clock tab with current_time/current_date/local_timezone
            parent = self
            while not (hasattr(parent, 'current_time') and hasattr(parent, 'current_date') and hasattr(parent, 'local_timezone')):
                parent = parent.parent()
            
            if not parent:
                QMessageBox.warning(self, "Error", "Could not access current time.")
                return
                
            current_time = parent.current_time
            current_date = parent.current_date
            
            # Combine date and time
            py_date = current_date.toPyDate()
            target_dt = datetime.datetime.combine(py_date, datetime.time(current_time.hour, current_time.minute, 0, 0))
            
            # Convert to target timezone to get intended meeting time
            tz = pytz.timezone(widget.timezone_name)
            local_tz = parent.local_timezone
            local_time = local_tz.localize(target_dt)
            target_time = local_time.astimezone(tz)
            
            # Format times for display
            readable_target_time = target_time.strftime("%Y-%m-%d %H:%M")
            readable_local_time = local_time.strftime("%Y-%m-%d %H:%M")
            city_name = widget.city_name
            
            # Ask for duration
            duration_minutes = self._confirm_and_get_duration(readable_target_time, readable_local_time, city_name)
            if duration_minutes is None:
                return
                
            # Calculate end time in target timezone
            target_end_time = target_time + datetime.timedelta(minutes=duration_minutes)
            formatted_target_end_time = target_end_time.strftime("%Y-%m-%d %H:%M")
            
            # Create meeting details
            subject = f"Teams Meeting - {city_name}"
            body = f"Teams meeting scheduled for {city_name}\nStart: {readable_target_time} ({city_name} timezone)\nEnd: {formatted_target_end_time} ({city_name} timezone)\nYour Local Time: {readable_local_time}\n\nAfter setting the time, click the 'Teams Meeting' button in Outlook to convert this to a Teams meeting."
            
            # Try to find Outlook
            outlook_paths = [
                r"C:\Program Files\Microsoft Office\root\Office16\OUTLOOK.EXE",
                r"C:\Program Files (x86)\Microsoft Office\root\Office16\OUTLOOK.EXE",
                r"C:\Program Files\Microsoft Office\Office16\OUTLOOK.EXE",
                r"C:\Program Files (x86)\Microsoft Office\Office16\OUTLOOK.EXE"
            ]
            
            outlook_path = None
            for path in outlook_paths:
                if os.path.exists(path):
                    outlook_path = path
                    break
            
            if outlook_path:
                # Show final confirmation before launching Outlook
                reply = QMessageBox.question(self, "Launch Outlook", 
                    f"Ready to create Teams meeting:\n\n"
                    f"City: {city_name}\n"
                    f"Target Time: {readable_target_time} ({city_name} timezone)\n"
                    f"Your Local Time: {readable_local_time}\n"
                    f"Duration: {duration_minutes} minutes\n\n"
                    f"After setting the time, click the 'Teams Meeting' button in Outlook to convert this to a Teams meeting.")
                
                if reply == QMessageBox.Yes:
                    # Create appointment with minimal parameters to avoid command line issues
                    try:
                        # Use a very simple subject without special characters
                        simple_subject = f"Teams Meeting - {city_name}".replace(" ", "_")
                        
                        # Try the most basic Outlook command first
                        LOGGER.info(f"Attempting to launch Outlook with: {outlook_path}")
                        LOGGER.info(f"Subject: {simple_subject}")
                        
                        subprocess.run([outlook_path, "/c", "ipm.appointment"], check=False)
                        LOGGER.info("Outlook launched successfully with basic appointment")
                        
                        # Show instruction message
                        from PyQt5.QtWidgets import QMessageBox
                        QMessageBox.information(self, "Teams Meeting Instructions", 
                            f"Outlook appointment created!\n\n"
                            f"Please set the following details:\n"
                            f"Subject: Teams Meeting - {city_name}\n"
                            f"Time: {readable_target_time} ({city_name} timezone)\n"
                            f"Duration: {duration_minutes} minutes\n\n"
                            f"Next steps:\n"
                            f"1. In Outlook, click the 'Teams Meeting' button\n"
                            f"2. Set the correct time for {city_name}\n"
                            f"3. Send the meeting invitation")
                            
                    except Exception as cmd_error:
                        LOGGER.error(f"Command line error: {cmd_error}")
                        # Fallback: try launching Outlook without any parameters
                        try:
                            subprocess.run([outlook_path], check=False)
                            QMessageBox.information(self, "Outlook Launched", 
                                f"Outlook has been opened.\n\n"
                                f"Please create a new appointment manually with:\n"
                                f"Subject: Teams Meeting - {city_name}\n"
                                f"Time: {readable_target_time} ({city_name} timezone)")
                        except Exception as fallback_error:
                            LOGGER.error(f"Fallback also failed: {fallback_error}")
                            QMessageBox.warning(self, "Launch Failed", 
                                f"Could not launch Outlook.\n"
                                f"Please check Outlook installation and try again.")
            else:
                QMessageBox.warning(self, "Outlook Not Found", "Microsoft Outlook could not be found. Please install Outlook or check the installation path.")
                
        except Exception as e:
            LOGGER.error(f"Error creating Teams Outlook meeting (manual): {e}")
            QMessageBox.warning(self, "Teams Outlook Error", f"Could not create Teams meeting:\n{str(e)}")
