# Visual Database Designer

*A desktop application for visually designing, modeling, and managing database schemas, built with Python and the Qt framework.*

![Screenshot of the application's main window] <!-- TODO: Add a screenshot here later -->

## About The Project

This project is a comprehensive tool that allows users to create, visualize, and interact with database structures in an intuitive graphical interface. Instead of writing complex SQL scripts from scratch, users can drag, drop, and connect tables to design their database schema.

The application is designed to be a powerful aid for students, developers, and database administrators who need to prototype, document, or manage relational database structures.

### Key Features

*   **Visual Schema Design:** Create and manage tables, columns, and relationships using an interactive drag-and-drop canvas.
*   **Multi-Diagram Support:** Organize large schemas by creating multiple, focused diagrams for different parts of your database within a single project.
*   **MySQL Reverse Engineering:** Connect to an existing MySQL database to automatically import and visualize its schema.
*   **SQL Code Generation:** Automatically generate SQL DDL scripts from your visual design to create the database.
*   **Self-Contained & Portable:** The application uses an embedded Firebird database for its own data, requiring no external database server for the user.

### Built With

*   **Python 3**
*   **Qt Framework** (via PyQt6)
*   **Firebird Embedded** (for internal application data)
*   **PyInstaller** (for packaging)

---

## Getting Started

### Prerequisites

*   Python 3.8+

### Installation & Running

1.  Clone the repository:
    ```sh
    git clone https://github.com/Uluqq/visual-database-designer.git
    ```
2.  Navigate to the project directory:
    ```sh
    cd visual-database-designer
    ```
3.  Install the required packages:
    ```sh
    pip install -r requirements.txt
    ```
4.  Run the application:
    ```sh
    python main.py
    ```

---

## License

Distributed under the MIT License. See `LICENSE` file for more information.

## Contact
I'm open to any help and advice.
email - papkovice@gmail.com

Project Link: [https://github.com/Uluqq/visual-database-designer](https://github.com/Uluqq/visual-database-designer)
