# main.py

import sys
from PySide6.QtWidgets import QApplication, QDialog
from PySide6.QtCore import QTranslator, QLibraryInfo
from views.main_window import MainWindow
from views.auth_dialog import AuthDialog
from views.project_selection_dialog import ProjectSelectionDialog
from models.base import init_db
from models.user import User
from models.project import Project
import resources_rc

CYBERPUNK_STYLESHEET = """
/* --- ГЛОБАЛЬНЫЕ НАСТРОЙКИ ШРИФТА И ЦВЕТА ТЕКСТА --- */
QWidget {
    font-family: 'Segoe UI', 'Roboto', sans-serif;
    font-size: 14px;
    color: #d9e0ee;
    /* ВАЖНО: Не задаем здесь background-color, иначе он перекроет все! */
}

/* Фон задается только корневым элементам через ID в коде Python */
QFrame#RootFrame {
    background-color: #1e1e2e;
}

/* Лейблы должны быть прозрачными, чтобы видеть фон фрейма */
QLabel {
    background-color: transparent;
}

/* --- COMBOBOX --- */
QComboBox {
    background-color: rgba(30, 30, 46, 0.8);
    border: 1px solid rgba(137, 180, 250, 0.3);
    border-radius: 5px;
    padding: 5px 10px;
    padding-right: 30px; 
    color: #ffffff;
    min-height: 25px;
}

/* Компактный ComboBox внутри таблицы */
QTableWidget QComboBox {
    margin: 0px;
    padding: 0px 0px 0px 5px;
    min-height: 0px;
    border-radius: 0px;
    background-color: transparent; 
    border: none; 
}
QTableWidget QComboBox:hover {
    background-color: rgba(137, 180, 250, 0.1);
}
QTableWidget QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: 20px;
    border: none;
}
QTableWidget QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #89b4fa;
}

/* --- ПОЛЯ ВВОДА --- */
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox {
    background-color: rgba(30, 30, 46, 0.8);
    border: 1px solid rgba(137, 180, 250, 0.3);
    border-radius: 5px;
    padding: 5px 10px;
    color: #ffffff;
    selection-background-color: #f5c2e7;
    selection-color: #1e1e2e;
    min-height: 30px;
}
QLineEdit:focus, QSpinBox:focus { border: 1px solid #89b4fa; }

/* --- КНОПКИ --- */
QPushButton {
    background-color: rgba(137, 180, 250, 0.1);
    border: 1px solid rgba(137, 180, 250, 0.5);
    border-radius: 6px;
    padding: 0px 15px;
    color: #89b4fa;
    font-weight: bold;
    min-height: 35px;
}
QPushButton:hover { background-color: rgba(137, 180, 250, 0.2); border: 1px solid #89b4fa; color: #ffffff; }
QPushButton:pressed { background-color: rgba(137, 180, 250, 0.4); }

QPushButton[role="primary"] {
    background-color: rgba(245, 194, 231, 0.1); 
    border: 1px solid #f5c2e7;
    color: #f5c2e7;
}
QPushButton[role="primary"]:hover { background-color: rgba(245, 194, 231, 0.3); color: #ffffff; }

/* --- СПИСКИ И ТАБЛИЦЫ --- */
QListWidget, QTableWidget, QTreeWidget {
    background-color: rgba(24, 24, 37, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    outline: none;
}
QListWidget::item, QTableWidget::item {
    padding: 5px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}
QListWidget::item:selected, QTableWidget::item:selected {
    background-color: rgba(137, 180, 250, 0.3);
    border: 1px solid rgba(137, 180, 250, 0.5);
    border-radius: 4px;
    color: white;
}
QHeaderView::section {
    background-color: #11111b;
    color: #bac2de;
    padding: 6px;
    border: none;
    border-bottom: 2px solid #89b4fa;
    font-weight: bold;
}

/* --- ВКЛАДКИ --- */
QTabWidget::pane {
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 5px;
    background-color: rgba(30, 30, 46, 0.5);
}
QTabBar::tab {
    background: transparent;
    color: #a6adc8;
    padding: 10px 15px;
    border-bottom: 2px solid transparent;
}
QTabBar::tab:selected { color: #f5c2e7; border-bottom: 2px solid #f5c2e7; }
QTabBar::tab:hover { background-color: rgba(255, 255, 255, 0.05); }

/* --- МЕНЮ --- */
QMenuBar { background-color: #181825; border-bottom: 1px solid #313244; color: #cdd6f4; }
QMenuBar::item:selected { background-color: rgba(137, 180, 250, 0.2); }
QMenu { background-color: #1e1e2e; border: 1px solid #313244; color: #cdd6f4; }
QMenu::item { padding: 5px 20px; }
QMenu::item:selected { background-color: rgba(137, 180, 250, 0.2); }
"""


class ApplicationController:
    def __init__(self):
        self.auth_dialog = None
        self.project_dialog = None
        self.main_window = None
        self.current_user = None

    def run(self):
        self.show_auth_dialog()
        return app.exec()

    def show_auth_dialog(self):
        self.auth_dialog = AuthDialog()
        if self.auth_dialog.exec() == QDialog.Accepted:
            self.current_user = self.auth_dialog.current_user
            self.show_project_dialog()
        else:
            sys.exit(0)

    def show_project_dialog(self):
        self.project_dialog = ProjectSelectionDialog(user=self.current_user)
        if self.project_dialog.exec() == QDialog.Accepted:
            selected_project = self.project_dialog.selected_project
            self.show_main_window(selected_project)
        else:
            sys.exit(0)

    def show_main_window(self, project: Project):
        self.main_window = MainWindow(user=self.current_user, project=project)
        self.main_window.project_selection_requested.connect(self.handle_exit_to_project_selection)
        self.main_window.show()

    def handle_exit_to_project_selection(self):
        if self.main_window:
            self.main_window.close()
        self.show_project_dialog()


if __name__ == "__main__":
    init_db()
    app = QApplication(sys.argv)
    app.setStyleSheet(CYBERPUNK_STYLESHEET)

    translator = QTranslator()
    translations_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    if translator.load("qtbase_ru", translations_path):
        app.installTranslator(translator)

    controller = ApplicationController()
    sys.exit(controller.run())