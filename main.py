# main.py

from PySide6.QtWidgets import QApplication, QDialog
from views.main_window import MainWindow
from views.auth_dialog import AuthDialog
from views.project_selection_dialog import ProjectSelectionDialog
import sys


def main():
    app = QApplication(sys.argv)

    current_user = None
    selected_project = None

    # --- Шаг 1: Аутентификация ---
    auth_dialog = AuthDialog()

    def on_authenticated(user):
        nonlocal current_user
        current_user = user

    auth_dialog.authenticated.connect(on_authenticated)

    if auth_dialog.exec() != QDialog.Accepted or not current_user:
        sys.exit(0)  # Выход, если пользователь закрыл окно входа

    # --- Шаг 2: Выбор проекта ---
    project_dialog = ProjectSelectionDialog(user=current_user)

    def on_project_selected(project):
        nonlocal selected_project
        selected_project = project

    project_dialog.project_selected.connect(on_project_selected)

    if project_dialog.exec() != QDialog.Accepted or not selected_project:
        sys.exit(0)  # Выход, если пользователь закрыл окно выбора проекта

    # --- Шаг 3: Запуск главного окна ---
    # Передаем и пользователя, и выбранный проект
    main_window = MainWindow(user=current_user, project=selected_project)
    main_window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()