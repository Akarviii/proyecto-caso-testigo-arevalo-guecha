import pytest
import app  # Importamos el módulo 'app' directamente
from app import app as flask_app

# 'fixture' es un concepto de pytest.
# Esta fixture ahora reinicia el estado directamente en el módulo 'app'
# antes de cada prueba, asegurando que no haya contaminación de estado.
@pytest.fixture
def client():
    # Reiniciar el estado directamente en el módulo 'app'
    app.tasks.clear()
    app.task_id_counter = 1
    with flask_app.test_client() as client:
        yield client

def test_health_check(client):
    """
    GIVEN un cliente de prueba de Flask
    WHEN se hace una petición GET a '/health'
    THEN se debe obtener una respuesta con código 200 y un JSON que contenga 'status': 'UP'
    """
    response = client.get('/health')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['status'] == "UP"
    assert "version" in json_data


def test_get_all_tasks_empty(client):
    """
    GIVEN un cliente de prueba de Flask
    WHEN se hace una petición GET a '/api/tasks' y no hay tareas
    THEN la respuesta debe ser 200 y una lista vacía
    """
    response = client.get('/api/tasks')
    assert response.status_code == 200
    assert response.get_json() == []

def test_create_task(client):
    """
    GIVEN un cliente de prueba de Flask
    WHEN se hace una petición POST a '/api/tasks' con datos de tarea
    THEN la respuesta debe ser 201 y la tarea creada con un ID
    """
    response = client.post('/api/tasks', json={'title': 'Nueva Tarea'})
    assert response.status_code == 201
    json_data = response.get_json()
    assert json_data['title'] == 'Nueva Tarea'
    assert json_data['id'] == 1
    assert json_data['completed'] is False

def test_get_all_tasks_with_data(client):
    """
    GIVEN un cliente de prueba de Flask con tareas
    WHEN se hace una petición GET a '/api/tasks'
    THEN la respuesta debe ser 200 y una lista con las tareas
    """
    client.post('/api/tasks', json={'title': 'Tarea 1'})
    client.post('/api/tasks', json={'title': 'Tarea 2'})
    response = client.get('/api/tasks')
    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data) == 2
    assert json_data[0]['title'] == 'Tarea 1'
    assert json_data[1]['title'] == 'Tarea 2'

def test_get_single_task(client):
    """
    GIVEN un cliente de prueba de Flask con una tarea
    WHEN se hace una petición GET a '/api/tasks/<id>' para una tarea existente
    THEN la respuesta debe ser 200 y la tarea específica
    """
    client.post('/api/tasks', json={'title': 'Tarea Única'})
    response = client.get('/api/tasks/1')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['title'] == 'Tarea Única'
    assert json_data['id'] == 1

def test_get_nonexistent_task(client):
    """
    GIVEN un cliente de prueba de Flask
    WHEN se hace una petición GET a '/api/tasks/<id>' para una tarea no existente
    THEN la respuesta debe ser 404
    """
    response = client.get('/api/tasks/999')
    assert response.status_code == 404
    assert "Tarea no encontrada" in response.get_json()['error']

def test_update_task(client):
    """
    GIVEN un cliente de prueba de Flask con una tarea
    WHEN se hace una petición PUT a '/api/tasks/<id>' para actualizar
    THEN la respuesta debe ser 200 y la tarea actualizada
    """
    client.post('/api/tasks', json={'title': 'Tarea a Actualizar'})
    response = client.put('/api/tasks/1', json={'title': 'Tarea Actualizada', 'completed': True})
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['title'] == 'Tarea Actualizada'
    assert json_data['completed'] is True

def test_update_nonexistent_task(client):
    """
    GIVEN un cliente de prueba de Flask
    WHEN se hace una petición PUT a '/api/tasks/<id>' para una tarea no existente
    THEN la respuesta debe ser 404
    """
    response = client.put('/api/tasks/999', json={'title': 'No existe'})
    assert response.status_code == 404

def test_delete_task(client):
    """
    GIVEN un cliente de prueba de Flask con una tarea
    WHEN se hace una petición DELETE a '/api/tasks/<id>' para una tarea existente
    THEN la respuesta debe ser 200 y la tarea ya no debe existir
    """
    client.post('/api/tasks', json={'title': 'Tarea a Borrar'})
    response = client.delete('/api/tasks/1')
    assert response.status_code == 200
    assert "Tarea eliminada exitosamente" in response.get_json()['message']
    
    get_response = client.get('/api/tasks')
    assert get_response.status_code == 200
    assert len(get_response.get_json()) == 0

def test_delete_nonexistent_task(client):
    """
    GIVEN un cliente de prueba de Flask
    WHEN se hace una petición DELETE a '/api/tasks/<id>' para una tarea no existente
    THEN la respuesta debe ser 404
    """
    response = client.delete('/api/tasks/999')
    assert response.status_code == 404

def test_create_task_no_title(client):
    """
    GIVEN un cliente de prueba de Flask
    WHEN se hace una petición POST a '/api/tasks' sin el campo 'title'
    THEN la respuesta debe ser 400
    """
    response = client.post('/api/tasks', json={'description': 'Esto no es un título'})
    assert response.status_code == 400
    assert "El campo 'title' es requerido" in response.get_json()['error']

