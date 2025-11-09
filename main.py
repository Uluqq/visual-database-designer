# main.py

import sys
from PySide6.QtWidgets import QApplication, QDialog
from views.main_window import MainWindow
from views.auth_dialog import AuthDialog
from views.project_selection_dialog import ProjectSelectionDialog
from models.base import init_db
from models.user import User
from models.project import Project
import resources_rc  # Убедитесь, что этот импорт присутствует


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
            # Пользователь закрыл окно входа, завершаем приложение
            sys.exit(0)

    def show_project_dialog(self):
        """Показывает диалог выбора проекта."""
        self.project_dialog = ProjectSelectionDialog(user=self.current_user)
        if self.project_dialog.exec() == QDialog.Accepted:
            selected_project = self.project_dialog.selected_project
            self.show_main_window(selected_project)
        else:
            # Пользователь закрыл окно выбора проекта, завершаем приложение
            sys.exit(0)

    def show_main_window(self, project: Project):
        """Показывает главное окно с диаграммой."""
        self.main_window = MainWindow(user=self.current_user, project=project)
        # Подключаем сигнал выхода из MainWindow к слоту, который покажет окно выбора проекта
        self.main_window.project_selection_requested.connect(self.handle_exit_to_project_selection)
        self.main_window.show()

    def handle_exit_to_project_selection(self):
        """Обрабатывает выход из главного окна к выбору проекта."""
        if self.main_window:
            self.main_window.close()
        # Запускаем цикл выбора проекта заново
        self.show_project_dialog()


if __name__ == "__main__":
    print("Инициализация базы данных...")
    init_db()
    print("База данных готова.")

    app = QApplication(sys.argv)
    controller = ApplicationController()
    sys.exit(controller.run())