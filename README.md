# Proyecto Caso Testigo - Gestión de Tareas

Este proyecto implementa una aplicación de gestión de tareas (To-Do List) con un backend RESTful API desarrollado en Python con Flask y un frontend construido con React y TypeScript. Incluye una suite de pruebas completa (unitarias, de integración con Testcontainers y E2E con Playwright) y está diseñado siguiendo principios SOLID y patrones de diseño.

video: https://youtu.be/YCPlqSB7Bx0

## Arquitectura del Proyecto

El proyecto está dividido en dos componentes principales:

-   **`backend/`**: Contiene la API RESTful en Flask que gestiona las tareas.
-   **`frontend/`**: Contiene la aplicación web de React que consume la API del backend.

## Tecnologías Utilizadas

### Backend

-   **Python**: Lenguaje de programación.
-   **Flask**: Microframework web para la API.
-   **Flask-CORS**: Para habilitar CORS.
-   **Gunicorn**: Servidor WSGI para producción (usado en Docker).
-   **python-dotenv**: Para gestionar variables de entorno.
-   **Docker**: Contenedorización del backend.
-   **pytest**: Framework de testing.
-   **requests**: Para realizar peticiones HTTP en los tests de integración.
-   **testcontainers-python**: Para gestionar contenedores Docker en tests de integración.

### Frontend

-   **React**: Librería para construir la interfaz de usuario.
-   **TypeScript**: Lenguaje de programación para tipado estático.
-   **Vite**: Herramienta de construcción rápida para proyectos frontend.
-   **Axios**: Cliente HTTP para interactuar con la API.

### Pruebas

-   **Pytest**: Para pruebas unitarias y de integración del backend.
-   **Testcontainers**: Para entornos de prueba aislados en integración.
-   **Playwright**: Para pruebas End-to-End (E2E) del frontend y la integración completa.

## Configuración y Ejecución del Proyecto

Asegúrate de tener **Docker** y **Node.js (con npm)** instalados en tu sistema. Para Python, se recomienda usar un entorno virtual.

### 1. Configuración del Backend

1.  **Navega al directorio `backend`**:
    ```bash
    cd backend
    ```
2.  **Crea y activa un entorno virtual (recomendado)**:
    ```bash
    python -m venv venv
    .\venv\Scripts\activate # En Windows
    # source venv/bin/activate # En Linux/macOS
    ```
3.  **Instala las dependencias de Python**:
    ```bash
    pip install -r requirements.txt
    ```
4.  **Ejecuta la aplicación Flask (desarrollo)**:
    ```bash
    flask run
    # O si tienes un archivo .env configurado con FLASK_APP=app.py
    # flask --app app run --debug --host 0.0.0.0 --port 5000
    ```
    La API estará disponible en `http://localhost:5000`.

### 2. Configuración y Ejecución del Frontend

1.  **Navega al directorio `frontend`**:
    ```bash
    cd frontend
    ```
2.  **Instala las dependencias de Node.js**:
    ```bash
    npm install
    ```
3.  **Ejecuta la aplicación React (desarrollo)**:
    ```bash
    npm run dev
    ```
    La aplicación frontend estará disponible en `http://localhost:5173`.

## Ejecución de Pruebas

### Pruebas Unitarias (Backend)

*Se asume que las pruebas unitarias ya están implementadas en `backend/tests/test_api.py` y `backend/tests/__init__.py`.*

1.  **Asegúrate de que tu entorno virtual esté activado en el directorio `backend`**.
2.  **Ejecuta Pytest**:
    ```bash
    # Desde el directorio raíz del proyecto:
    .\backend\venv\Scripts\python.exe -m pytest -v backend/tests/test_api.py
    ```

### Pruebas de Integración (Backend con Testcontainers)

1.  **Asegúrate de que tu entorno virtual esté activado en el directorio `backend`**.
2.  **Asegúrate de que Docker esté corriendo en tu sistema.**
3.  **Ejecuta Pytest**:
    ```bash
    # Desde el directorio raíz del proyecto:
    .\backend\venv\Scripts\python.exe -m pytest -v backend/tests/test_integration.py
    ```
    Estas pruebas construirán y ejecutarán el backend dentro de un contenedor Docker.

### Pruebas End-to-End (Frontend + Backend con Playwright)

1.  **Asegúrate de que Docker esté corriendo en tu sistema.**
2.  **Asegúrate de haber instalado las dependencias de Playwright (se hizo durante la inicialización).**
3.  **Ejecuta Playwright**:
    ```bash
    # Desde el directorio raíz del proyecto:
    npx playwright test
    ```
    Playwright se encargará de levantar tanto el backend (en Docker) como el frontend (usando `npm run dev`) automáticamente antes de ejecutar las pruebas del navegador.

## Documentación de la API

Los endpoints disponibles en el backend son:

-   `GET /`: Mensaje de bienvenida.
-   `GET /health`: Estado de salud de la API.
-   `GET /api/tasks`: Obtiene todas las tareas.
-   `GET /api/tasks/<int:task_id>`: Obtiene una tarea por su ID.
-   `POST /api/tasks`: Crea una nueva tarea. Requiere `{ "title": "...", "completed": false/true }`.
-   `PUT /api/tasks/<int:task_id>`: Actualiza una tarea existente. Requiere `{ "title": "...", "completed": false/true }` (campos opcionales).
-   `DELETE /api/tasks/<int:task_id>`: Elimina una tarea por su ID.

## Principios SOLID y Patrones de Diseño Aplicados (Backend)

-   **Single Responsibility Principle (SRP)**:
    -   La lógica de gestión de tareas se ha movido del `app.py` (capa de la API) a `backend/services/task_service.py` (capa de lógica de negocio).
    -   El modelo `Task` (`backend/models/task_model.py`) tiene la única responsabilidad de definir la estructura y validación de una tarea.
-   **Open/Closed Principle (OCP)**:
    -   La clase `Task` es fácilmente extensible (abierta a extensión) con nuevos atributos o comportamientos sin modificar su código existente.
    -   El `task_service` se podría extender para usar diferentes almacenamientos (ej. base de datos) sin alterar la interfaz pública de `task_service` (a través de inyección de dependencias si se refina más).
-   **Liskov Substitution Principle (LSP)**: (Menos evidente en esta pequeña aplicación, pero la interfaz de `Task` se mantiene consistente).
-   **Interface Segregation Principle (ISP)**: (No aplicable directamente en Flask sin interfaces explícitas).
-   **Dependency Inversion Principle (DIP)**: Se observa una inversión parcial de dependencia donde `app.py` depende de las abstracciones de `task_service` (funciones), no de detalles de implementación de almacenamiento.

**Patrones de Diseño:**

-   **Service Layer**: `task_service.py` actúa como una capa de servicio que abstrae la lógica de negocio del controlador de la API.
-   **Domain Model**: La clase `Task` en `task_model.py` representa un modelo de dominio rico con su propia validación y comportamiento.

## Próximos Pasos (No implementado en esta entrega)

-   Implementación de una base de datos persistente (ej. PostgreSQL) en lugar del almacenamiento en memoria.
-   Autenticación y autorización para la API.
-   Mejoras en la interfaz de usuario del frontend (ej. edición de tareas, filtros).
