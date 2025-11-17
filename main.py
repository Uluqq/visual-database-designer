# main.py

import sys
from PySide6.QtWidgets import QApplication, QDialog
# --- VVV --- ДОБАВЛЯЕМ НОВЫЕ ИМПОРТЫ --- VVV ---
from PySide6.QtCore import QTranslator, QLibraryInfo
# --- ^^^ --- КОНЕЦ ИЗМЕНЕНИЙ --- ^^^ ---
from views.main_window import MainWindow
from views.auth_dialog import AuthDialog
from views.project_selection_dialog import ProjectSelectionDialog
from models.base import init_db
from models.user import User
from models.project import Project
import resources_rc


class ApplicationController:
    """
    Класс для управления жизненным циклом окон приложения.
    """
    def __init__(self):
        self.auth_dialog = None
        self.project_dialog = None
        self.main_window = None
        self.current_user = None

    def run(self):
        """Запускает основной цикл приложения."""
        self.show_auth_dialog()
        return app.exec()

    def show_auth_dialog(self):
        """Показывает диалог аутентификации."""
        self.auth_dialog = AuthDialog()
        if self.auth_dialog.exec() == QDialog.Accepted:
            self.current_user = self.auth_dialog.current_user
            self.show_project_dialog()
        else:
            sys.exit(0)

    def show_project_dialog(self):
        """Показывает диалог выбора проекта."""
        self.project_dialog = ProjectSelectionDialog(user=self.current_user)
        if self.project_dialog.exec() == QDialog.Accepted:
            selected_project = self.project_dialog.selected_project
            self.show_main_window(selected_project)
        else:
            sys.exit(0)

    def show_main_window(self, project: Project):
        """Показывает главное окно с диаграммой."""
        self.main_window = MainWindow(user=self.current_user, project=project)
        self.main_window.project_selection_requested.connect(self.handle_exit_to_project_selection)
        self.main_window.show()

    def handle_exit_to_project_selection(self):
        """Обрабатывает выход из главного окна к выбору проекта."""
        if self.main_window:
            self.main_window.close()
        self.show_project_dialog()


if __name__ == "__main__":
    print("Инициализация базы данных...")
    init_db()
    print("База данных готова.")

    app = QApplication(sys.argv)

    # --- VVV --- НОВЫЙ КОД ДЛЯ ЛОКАЛИЗАЦИИ --- VVV ---
    # Загружаем стандартные переводы Qt для диалогов (QColorDialog, QMessageBox и др.)
    translator = QTranslator()
    # Находим путь к встроенным в PySide6 файлам перевода
    translations_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    if translator.load("qtbase_ru", translations_path):
        app.installTranslator(translator)
        print("Русский перевод для стандартных диалогов Qt успешно загружен.")
    else:
        print("ПРЕДУПРЕЖДЕНИЕ: Файл перевода qtbase_ru.qm не найден. Диалоги могут быть на английском.")
    # --- ^^^ --- КОНЕЦ НОВОГО КОДА --- ^^^ ---

    controller = ApplicationController()
    sys.exit(controller.run())