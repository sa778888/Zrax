import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.Qsci import *
import sys
from pathlib import Path
from editor import Editor
from fuzzy_searcher import SearchItem, SearchWorker
from file_manager import FileManager
from typing import Optional, Callable

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__() # Corrected super() call

        self.side_bar_clr = "#282c34"
        self.init_ui()
        self.current_file: Optional[Path] = None
        self.current_side_bar: Optional[str] = None

    def init_ui(self):
        self.app_name = "PYQT EDITOR"
        self.setWindowTitle(self.app_name)
        self.resize(1300, 900)
        try:
            with open("./src/css/style.qss", "r") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print("Error: style.qss not found.") # Log to console
            # Optionally, set a default stylesheet here.
            self.setStyleSheet("background-color: #333;") #Example Default style

        self.window_font = QFont("Fire Code")
        self.window_font.setPointSize(12)
        self.setFont(self.window_font)

        self.set_up_menu()
        self.set_up_body()
        self.set_up_status_bar()
        self.show()

    def set_up_status_bar(self):
        stat = QStatusBar(self)
        stat.setStyleSheet("color: #D3D3D3;")
        stat.showMessage("Ready", 3000)
        self.setStatusBar(stat)

    def set_up_menu(self):
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("File")

        new_file = file_menu.addAction("New")
        new_file.setShortcut("Ctrl+N")
        new_file.triggered.connect(self.new_file)

        open_file = file_menu.addAction("Open File")
        open_file.setShortcut("Ctrl+O")
        open_file.triggered.connect(self.open_file)

        open_folder = file_menu.addAction("Open Folder")
        open_folder.setShortcut("Ctrl+K")
        open_folder.triggered.connect(self.open_folder)

        file_menu.addSeparator()

        save_file = file_menu.addAction("Save")
        save_file.setShortcut("Ctrl+S")
        save_file.triggered.connect(self.save_file)

        save_as = file_menu.addAction("Save As")
        save_as.setShortcut("Ctrl+Shift+S")
        save_as.triggered.connect(self.save_as)

        edit_menu = menu_bar.addMenu("Edit")
        copy_action = edit_menu.addAction("Copy")
        copy_action.setShortcut("Ctrl+C")
        copy_action.triggered.connect(self.copy)

    def get_editor(self, path: Optional[Path] = None, is_python_file=True) -> QsciScintilla:
        editor = Editor(self, path=path, is_python_file=is_python_file)
        return editor

    def is_binary(self, path: Path) -> bool:
        try:
            with open(path, 'rb') as f:
                return b'\0' in f.read(1024)
        except IOError: # Catch file not found errors
            return True

    def set_new_tab(self, path: Path, is_new_file=False):
        if not is_new_file and self.is_binary(path):
            self.statusBar().showMessage("Cannot Open Binary File", 2000)
            return

        if path.is_dir():
            return

        editor = self.get_editor(path, path.suffix in {".py", ".pyw"})

        if is_new_file:
            self.tab_view.addTab(editor, "untitled")
            self.setWindowTitle("untitled - " + self.app_name)
            self.statusBar().showMessage("Opened untitled")
            self.tab_view.setCurrentIndex(self.tab_view.count() - 1)
            self.current_file = None
            return

        for i in range(self.tab_view.count()):
            if self.tab_view.tabText(i) == path.name or self.tab_view.tabText(i) == "*"+path.name:
                self.tab_view.setCurrentIndex(i)
                self.current_file = path
                return

        try:
            editor.setText(path.read_text(encoding="utf-8"))
        except UnicodeDecodeError:
            QMessageBox.warning(self, "Error", f"Could not decode file {path.name} with UTF-8.  Try opening in a different encoding.")
            return
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error opening {path.name}: {e}")
            return

        self.tab_view.addTab(editor, path.name)
        self.setWindowTitle(f"{path.name} - {self.app_name}")
        self.current_file = path
        self.tab_view.setCurrentIndex(self.tab_view.count() - 1)
        self.statusBar().showMessage(f"Opened {path.name}", 2000)

    def set_cursor_pointer(self, e):
        self.setCursor(Qt.PointingHandCursor)

    def set_cursor_arrow(self, e):
        self.setCursor(Qt.ArrowCursor)

    def get_side_bar_label(self, path: str, name: str) -> QLabel:
        label = QLabel()
        label.setPixmap(QPixmap(path).scaled(QSize(30, 30)))
        label.setAlignment(Qt.AlignmentFlag.AlignTop)
        label.setFont(self.window_font)
        label.mousePressEvent = lambda e: self.show_hide_tab(e, name)

        label.enterEvent = self.set_cursor_pointer
        label.leaveEvent = self.set_cursor_arrow
        return label

    def get_frame(self) -> QFrame:
        frame = QFrame()
        frame.setFrameShape(QFrame.NoFrame)
        frame.setFrameShadow(QFrame.Plain)
        frame.setContentsMargins(0, 0, 0, 0)
        frame.setStyleSheet('''
            QFrame {
                background-color: #21252b;
                border-radius: 5px;
                border: none;
                padding: 5px;
                color: #D3D3D3;
            }
            QFrame:hover {
                color: white;
            }
        ''')
        return frame

    def set_up_body(self):
        body_frame = QFrame()
        body_frame.setFrameShape(QFrame.NoFrame)
        body_frame.setFrameShadow(QFrame.Plain)
        body_frame.setLineWidth(0)
        body_frame.setMidLineWidth(0)
        body_frame.setContentsMargins(0, 0, 0, 0)
        body_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        body_frame.setLayout(body)

        self.tab_view = QTabWidget()
        self.tab_view.setContentsMargins(0, 0, 0, 0)
        self.tab_view.setTabsClosable(True)
        self.tab_view.setMovable(True)
        self.tab_view.setDocumentMode(True)
        self.tab_view.tabCloseRequested.connect(self.close_tab)

        self.side_bar = QFrame()
        self.side_bar.setFrameShape(QFrame.StyledPanel)
        self.side_bar.setFrameShadow(QFrame.Plain)
        self.side_bar.setStyleSheet(f'''
            background-color: {self.side_bar_clr};
        ''')

        side_bar_layout = QVBoxLayout()
        side_bar_layout.setContentsMargins(5, 10, 5, 0)
        side_bar_layout.setSpacing(0)
        side_bar_layout.setAlignment(Qt.AlignTop | Qt.AlignCenter)

        folder_label = self.get_side_bar_label("./src/icons/folder-icon-blue.svg", "folder-icon")
        side_bar_layout.addWidget(folder_label)

        search_label = self.get_side_bar_label("./src/icons/search-icon", "search-icon")
        side_bar_layout.addWidget(search_label)

        self.side_bar.setLayout(side_bar_layout)

        self.hsplit = QSplitter(Qt.Horizontal)

        self.file_manager_frame = self.get_frame()
        self.file_manager_frame.setMaximumWidth(400)
        self.file_manager_frame.setMinimumWidth(200)

        self.file_manager_layout = QVBoxLayout()
        self.file_manager_layout.setContentsMargins(0, 0, 0, 0)
        self.file_manager_layout.setSpacing(0)

        self.file_manager = FileManager(
            tab_view=self.tab_view,
            set_new_tab=self.set_new_tab,
            main_window=self
        )

        self.file_manager_layout.addWidget(self.file_manager)
        self.file_manager_frame.setLayout(self.file_manager_layout)

        self.search_frame = self.get_frame()
        self.search_frame.setMaximumWidth(400)
        self.search_frame.setMinimumWidth(200)

        search_layout = QVBoxLayout()
        search_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        search_layout.setContentsMargins(0, 10, 0, 0)
        search_layout.setSpacing(0)

        search_input = QLineEdit()
        search_input.setPlaceholderText("Search")
        search_input.setFont(self.window_font)
        search_input.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.search_checkbox = QCheckBox("Search in modules")
        self.search_checkbox.setFont(self.window_font)
        self.search_checkbox.setStyleSheet("color: white; margin-bottom: 10px;")

        self.search_worker = SearchWorker()
        self.search_worker.finished.connect(self.search_finshed)

        search_input.textChanged.connect(
            lambda text: self.search_worker.update(
                text,
                self.file_manager.model.rootPath(), # Corrected
                self.search_checkbox.isChecked()
            )
        )

        self.search_list_view = QListWidget()
        self.search_list_view.setFont(QFont("FiraCode", 13))
        self.search_list_view.setStyleSheet("""
            QListWidget {
                background-color: #21252b;
                border-radius: 5px;
                border: 1px solid #D3D3D3;
                padding: 5px;
                color: #D3D3D3;
            }
        """)
        self.search_list_view.itemClicked.connect(self.search_list_view_clicked)

        search_layout.addWidget(self.search_checkbox)
        search_layout.addWidget(search_input)
        search_layout.addSpacerItem(QSpacerItem(5, 5, QSizePolicy.Minimum, QSizePolicy.Minimum))
        search_layout.addWidget(self.search_list_view)
        self.search_frame.setLayout(search_layout)

        self.hsplit.addWidget(self.file_manager_frame)
        self.hsplit.addWidget(self.tab_view)

        body.addWidget(self.side_bar)
        body.addWidget(self.hsplit)
        body_frame.setLayout(body)

        self.setCentralWidget(body_frame)

    def search_finshed(self, items):
        self.search_list_view.clear()
        for i in items:
            self.search_list_view.addItem(i)

    def search_list_view_clicked(self, item: SearchItem):
        self.set_new_tab(Path(item.full_path))
        editor: Editor = self.tab_view.currentWidget()
        editor.setCursorPosition(item.lineno, item.end)
        editor.setFocus()

    def show_dialog(self, title: str, msg: str) -> int:
        dialog = QMessageBox(self)
        dialog.setFont(self.font())
        dialog.font().setPointSize(14)
        dialog.setWindowTitle(title)
        dialog.setWindowIcon(QIcon(":/icons/close-icon.svg"))
        dialog.setText(msg)
        dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dialog.setDefaultButton(QMessageBox.No)
        dialog.setIcon(QMessageBox.Warning)
        return dialog.exec_()

    def close_tab(self, index: int):
        editor: Editor = self.tab_view.widget(index)  # changed from currentWidget
        if editor.current_file_changed:
            dialog = self.show_dialog(
                "Close", f"Do you want to save the changes made to {self.current_file.name}?"
            )
            if dialog == QMessageBox.Yes:
                self.save_file() # You need to save file before removing
        self.tab_view.removeTab(index) # This should always happen

    def show_hide_tab(self, e, type_: str):
        if type_ == "folder-icon":
            if not (self.file_manager_frame in self.hsplit.children()):
                self.hsplit.insertWidget(0, self.file_manager_frame) # insert instead of replace
            self.search_frame.hide()
            self.file_manager_frame.show()

        elif type_ == "search-icon":
            if not (self.search_frame in self.hsplit.children()):
                self.hsplit.insertWidget(0, self.search_frame) # insert instead of replace
            self.file_manager_frame.hide()
            self.search_frame.show()

        self.current_side_bar = type_

        frame = self.hsplit.widget(0) # changed from children()[0]
        if frame.isHidden():
            frame.show()
        else:
            frame.hide()

    def new_file(self):
        self.set_new_tab(Path("untitled"), is_new_file=True)

    def save_file(self):
        if self.current_file is None and self.tab_view.count() > 0:
            self.save_as()
            return # add return so the rest doesnt execute

        editor = self.tab_view.currentWidget()
        try:
            self.current_file.write_text(editor.text())
            self.statusBar().showMessage(f"Saved {self.current_file.name}", 2000)
            editor.current_file_changed = False
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save file: {e}")

    def save_as(self):
        editor = self.tab_view.currentWidget()
        if editor is None:
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Save As", os.getcwd()) # added _
        if not file_path: # same as file_path == ''
            self.statusBar().showMessage("Cancelled", 2000)
            return

        path = Path(file_path)
        try:
            path.write_text(editor.text())
            self.tab_view.setTabText(self.tab_view.currentIndex(), path.name)
            self.statusBar().showMessage(f"Saved {path.name}", 2000)
            self.current_file = path
            editor.current_file_changed = False
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save file: {e}")

    def open_file(self):
        ops = QFileDialog.Options()
        ops |= QFileDialog.DontUseNativeDialog

        file_path, _ = QFileDialog.getOpenFileName(self, # added _
            "Pick A File", "", "All Files (*);;Python Files (*.py)",
            options=ops)

        if not file_path: # same as file_path == ''
            self.statusBar().showMessage("Cancelled", 2000)
            return

        f = Path(file_path)
        self.set_new_tab(f)

    def open_folder(self):
        ops = QFileDialog.Options()
        ops |= QFileDialog.DontUseNativeDialog

        new_folder = QFileDialog.getExistingDirectory(self, "Pick A Folder", "", options=ops)

        if new_folder:
            self.file_manager.model.setRootPath(new_folder)
            self.file_manager.setRootIndex(self.file_manager.model.index(new_folder))
            self.statusBar().showMessage(f"Opened {new_folder}", 2000)

    def copy(self):
        editor = self.tab_view.currentWidget()
        if editor is not None:
            editor.copy()

if __name__ == '__main__':
    app = QApplication(sys.argv) # added sys.argv
    window = MainWindow()
    sys.exit(app.exec_())
