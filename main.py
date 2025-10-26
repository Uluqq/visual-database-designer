# main.py

from PySide6.QtWidgets import QApplication, QDialog
from views.main_window import MainWindow
from views.auth_dialog import AuthDialog
import sys

# Переменная для хранения текущего пользователя
current_user = None


def main():
    app = QApplication(sys.argv)

    # 1. Создаем и показываем диалог аутентификации
    auth_dialog = AuthDialog()

    # Функция, которая будет вызвана при успешной аутентификации
    def on_authenticated(user):
        global current_user
        current_user = user

    auth_dialog.authenticated.connect(on_authenticated)

    # 2. Запускаем диалог. Если он завершился успешно, показывем главное окно.
    if auth_dialog.exec() == QDialog.Accepted and current_user:
        window = MainWindow(user=current_user)  # Передаем пользователя в главное окно
        window.show()
        sys.exit(app.exec())
    else:
        # Если пользователь закрыл окно входа, просто выходим
        sys.exit(0)


if __name__ == "__main__":
    main()