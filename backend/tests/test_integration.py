import pytest
import requests
import os
import docker  # Import the docker library
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs

# Construye la ruta absoluta al directorio 'backend' para asegurar que Docker la encuentre.
# __file__ es la ruta al archivo actual (backend/tests/test_integration.py)
# os.path.dirname(...) nos da el directorio que lo contiene.
# Usamos dirname dos veces para subir de 'tests' a 'backend'.
DOCKERFILE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@pytest.fixture(scope="module")
def app_container():
    """
    Esta fixture construye la imagen Docker explícitamente usando la librería `docker`,
    luego la inicia con testcontainers. Esto evita problemas de interpretación de rutas
    que ocurren en Windows.
    """
    # Usamos la librería 'docker' para construir la imagen explícitamente.
    client = docker.from_env()
    image_tag = "test-app-my-project:latest"  # Nombre de imagen válido y en minúsculas
    try:
        print(f"\nBuilding image '{image_tag}' from path '{DOCKERFILE_PATH}'...")
        client.images.build(path=DOCKERFILE_PATH, tag=image_tag, rm=True, forcerm=True)
        print("Image built successfully.")
    except docker.errors.BuildError as e:
        print("\n--- DOCKER BUILD FAILED ---")
        for line in e.build_log:
            if 'stream' in line:
                print(line['stream'].strip())
        print("---------------------------\n")
        pytest.fail(f"Docker image build failed: {e}")

    # Ahora, usamos testcontainers para correr el contenedor desde la imagen ya construida.
    with DockerContainer(image=image_tag).with_exposed_ports(5000) as container:
        # Espera a que el contenedor muestre un log que indique que la app está lista.
        # Gunicorn nos avisará cuando esté escuchando en el puerto.
        wait_for_logs(container, "Booting worker", timeout=60)
        
        # Obtiene el puerto mapeado dinámicamente y la IP del host.
        host = container.get_container_host_ip()
        port = container.get_exposed_port(5000)
        
        # Cede la URL base de la API a las pruebas.
        print(f"Container is ready at http://{host}:{port}")
        yield f"http://{host}:{port}"

def test_integration_health_check(app_container):
    """
    GIVEN el contenedor de la aplicación corriendo
    WHEN se hace una petición GET real a su endpoint '/health'
    THEN la respuesta debe ser 200 y el estado 'UP'
    """
    # app_container es la URL base, por ejemplo: http://localhost:54321
    response = requests.get(f"{app_container}/health")
    
    assert response.status_code == 200
    json_data = response.json()
    assert json_data['status'] == "UP"

# --- Pruebas para la API de Tareas ---

def test_scenario_create_get_update_delete(app_container):
    """
    Un test de escenario completo:
    1. Verifica que no hay tareas al inicio.
    2. Crea una tarea.
    3. La obtiene y verifica su contenido.
    4. La actualiza.
    5. Verifica que fue actualizada.
    6. La elimina.
    7. Verifica que ya no existe.
    """
    base_url = f"{app_container}/api/tasks"
    
    # 1. Limpiar y verificar que la lista de tareas está vacía
    # (Hacemos esto obteniendo todas las tareas y eliminándolas una por una)
    initial_tasks_resp = requests.get(base_url)
    assert initial_tasks_resp.status_code == 200
    for task in initial_tasks_resp.json():
        requests.delete(f"{base_url}/{task['id']}")
    
    final_tasks_resp = requests.get(base_url)
    assert final_tasks_resp.json() == []

    # 2. Crear una nueva tarea
    new_task_payload = {'title': 'Mi primera tarea de integración'}
    create_resp = requests.post(base_url, json=new_task_payload)
    assert create_resp.status_code == 201
    created_task = create_resp.json()
    assert 'id' in created_task
    assert created_task['title'] == new_task_payload['title']
    assert not created_task['completed']
    task_id = created_task['id']

    # 3. Obtener la tarea por su ID
    get_resp = requests.get(f"{base_url}/{task_id}")
    assert get_resp.status_code == 200
    assert get_resp.json() == created_task

    # 4. Actualizar la tarea
    update_payload = {'title': 'Tarea actualizada', 'completed': True}
    update_resp = requests.put(f"{base_url}/{task_id}", json=update_payload)
    assert update_resp.status_code == 200
    updated_task = update_resp.json()
    assert updated_task['title'] == update_payload['title']
    assert updated_task['completed'] == update_payload['completed']

    # 5. Verificar que fue actualizada
    get_updated_resp = requests.get(f"{base_url}/{task_id}")
    assert get_updated_resp.status_code == 200
    assert get_updated_resp.json() == updated_task

    # 6. Eliminar la tarea
    delete_resp = requests.delete(f"{base_url}/{task_id}")
    assert delete_resp.status_code == 200

    # 7. Verificar que ya no existe
    get_deleted_resp = requests.get(f"{base_url}/{task_id}")
    assert get_deleted_resp.status_code == 404

def test_create_task_bad_request(app_container):
    """
    GIVEN la API corriendo
    WHEN se intenta crear una tarea sin el campo 'title'
    THEN la API debe devolver un error 400 Bad Request.
    """
    base_url = f"{app_container}/api/tasks"
    bad_payload = {'description': 'Esto no es un título'}
    response = requests.post(base_url, json=bad_payload)
    assert response.status_code == 400
    assert 'error' in response.json()

def test_get_task_not_found(app_container):
    """
    GIVEN la API corriendo
    WHEN se busca una tarea con un ID que no existe
    THEN la API debe devolver un error 404 Not Found.
    """
    base_url = f"{app_container}/api/tasks"
    # Usamos un ID que es muy improbable que exista
    non_existent_id = 99999
    response = requests.get(f"{base_url}/{non_existent_id}")
    assert response.status_code == 404

def test_update_task_not_found(app_container):
    """
    GIVEN la API corriendo
    WHEN se intenta actualizar una tarea con un ID que no existe
    THEN la API debe devolver un error 404 Not Found.
    """
    base_url = f"{app_container}/api/tasks"
    non_existent_id = 99999
    update_payload = {'title': 'No existo'}
    response = requests.put(f"{base_url}/{non_existent_id}", json=update_payload)
    assert response.status_code == 404

def test_delete_task_not_found(app_container):
    """
    GIVEN la API corriendo
    WHEN se intenta eliminar una tarea con un ID que no existe
    THEN la API debe devolver un error 404 Not Found.
    """
    base_url = f"{app_container}/api/tasks"
    non_existent_id = 99999
    response = requests.delete(f"{base_url}/{non_existent_id}")
    assert response.status_code == 404

def test_task_ids_are_auto_incrementing(app_container):
    """
    GIVEN la API corriendo
    WHEN se crean dos tareas consecutivamente
    THEN el ID de la segunda tarea debe ser mayor que el de la primera.
    """
    base_url = f"{app_container}/api/tasks"
    
    # Crear la primera tarea
    task1_payload = {'title': 'Tarea A'}
    resp1 = requests.post(base_url, json=task1_payload)
    assert resp1.status_code == 201
    task1_id = resp1.json()['id']
    
    # Crear la segunda tarea
    task2_payload = {'title': 'Tarea B'}
    resp2 = requests.post(base_url, json=task2_payload)
    assert resp2.status_code == 201
    task2_id = resp2.json()['id']
    
    # Verificar que los IDs son diferentes y se incrementan
    assert task2_id > task1_id
    
    # Limpieza
    requests.delete(f"{base_url}/{task1_id}")
    requests.delete(f"{base_url}/{task2_id}")

def test_update_task_only_title(app_container):
    """
    GIVEN una tarea existente
    WHEN se actualiza solo su título
    THEN el título debe cambiar y el estado 'completed' debe permanecer igual.
    """
    base_url = f"{app_container}/api/tasks"
    
    # Crear tarea inicial
    task_payload = {'title': 'Título original', 'completed': False}
    resp = requests.post(base_url, json=task_payload)
    task_id = resp.json()['id']
    
    # Actualizar solo el título
    update_payload = {'title': 'Título nuevo'}
    update_resp = requests.put(f"{base_url}/{task_id}", json=update_payload)
    assert update_resp.status_code == 200
    updated_task = update_resp.json()
    
    # Verificar
    assert updated_task['title'] == 'Título nuevo'
    assert updated_task['completed'] is False
    
    # Limpieza
    requests.delete(f"{base_url}/{task_id}")

def test_update_task_only_completed(app_container):
    """
    GIVEN una tarea existente
    WHEN se actualiza solo su estado 'completed'
    THEN el estado debe cambiar y el título debe permanecer igual.
    """
    base_url = f"{app_container}/api/tasks"
    
    # Crear tarea inicial
    task_payload = {'title': 'Completar esta tarea'}
    resp = requests.post(base_url, json=task_payload)
    task_id = resp.json()['id']
    
    # Actualizar solo el estado
    update_payload = {'completed': True}
    update_resp = requests.put(f"{base_url}/{task_id}", json=update_payload)
    assert update_resp.status_code == 200
    updated_task = update_resp.json()
    
    # Verificar
    assert updated_task['title'] == 'Completar esta tarea'
    assert updated_task['completed'] is True
    
    # Limpieza
    requests.delete(f"{base_url}/{task_id}")

def test_create_task_with_empty_title(app_container):
    """
    GIVEN la API corriendo
    WHEN se intenta crear una tarea con un título vacío
    THEN la API debe devolver un error 400 Bad Request.
    """
    base_url = f"{app_container}/api/tasks"
    payload = {'title': ''}
    resp = requests.post(base_url, json=payload)
    assert resp.status_code == 400
    assert 'error' in resp.json() # Check for the error message

def test_create_and_get_multiple_tasks(app_container):
    """
    GIVEN la API corriendo
    WHEN se crean varias tareas
    THEN al obtener todas las tareas, la lista debe contenerlas.
    """
    base_url = f"{app_container}/api/tasks"
    
    # Limpiar estado previo
    initial_tasks_resp = requests.get(base_url)
    for task in initial_tasks_resp.json():
        requests.delete(f"{base_url}/{task['id']}")
        
    # Crear 3 tareas
    task1 = requests.post(base_url, json={'title': 'Task 1'}).json()
    task2 = requests.post(base_url, json={'title': 'Task 2'}).json()
    task3 = requests.post(base_url, json={'title': 'Task 3'}).json()
    
    # Obtener todas las tareas
    get_all_resp = requests.get(base_url)
    assert get_all_resp.status_code == 200
    tasks_list = get_all_resp.json()
    
    # Verificar que la lista contiene las 3 tareas
    assert len(tasks_list) == 3
    
    # Verificar que los IDs están en la lista
    response_ids = {task['id'] for task in tasks_list}
    expected_ids = {task1['id'], task2['id'], task3['id']}
    assert response_ids == expected_ids
    
    # Limpieza
    for task_id in expected_ids:
        requests.delete(f"{base_url}/{task_id}")

# --- Set 9: Pruebas de Casos Borde y Edge Cases ---

@pytest.mark.parametrize("long_title", [
    "a" * 1000,
    "largo" * 500,
])
def test_create_task_with_long_title(app_container, long_title):
    base_url = f"{app_container}/api/tasks"
    resp = requests.post(base_url, json={'title': long_title})
    assert resp.status_code == 201
    task = resp.json()
    assert task['title'] == long_title
    requests.delete(f"{base_url}/{task['id']}")

@pytest.mark.parametrize("special_title", [
    "Tarea con !@#$%^&*()",
    "你好,世界",
    "😊🎉👍",
])
def test_create_task_with_special_chars_title(app_container, special_title):
    base_url = f"{app_container}/api/tasks"
    resp = requests.post(base_url, json={'title': special_title})
    assert resp.status_code == 201
    task = resp.json()
    assert task['title'] == special_title
    requests.delete(f"{base_url}/{task['id']}")

def test_create_task_with_whitespace_title(app_container):
    base_url = f"{app_container}/api/tasks"
    payload = {'title': '   '}
    resp = requests.post(base_url, json=payload)
    assert resp.status_code == 400
    assert 'error' in resp.json() # Check for the error message

def test_update_task_with_long_title(app_container):
    base_url = f"{app_container}/api/tasks"
    task_resp = requests.post(base_url, json={'title': 'Original'})
    task_id = task_resp.json()['id']
    
    long_title = "b" * 1000
    update_payload = {'title': long_title}
    update_resp = requests.put(f"{base_url}/{task_id}", json=update_payload)
    assert update_resp.status_code == 200
    assert update_resp.json()['title'] == long_title
    
    requests.delete(f"{base_url}/{task_id}")

def test_update_task_does_not_change_id(app_container):
    base_url = f"{app_container}/api/tasks"
    task_resp = requests.post(base_url, json={'title': 'ID Inmutable'})
    original_task = task_resp.json()
    task_id = original_task['id']
    
    update_payload = {'title': 'ID Cambiado?', 'id': task_id + 100}
    update_resp = requests.put(f"{base_url}/{task_id}", json=update_payload)
    assert update_resp.status_code == 200
    updated_task = update_resp.json()
    
    assert updated_task['id'] == task_id
    assert updated_task['title'] == 'ID Cambiado?'
    
    requests.delete(f"{base_url}/{task_id}")

def test_create_task_with_extra_fields(app_container):
    base_url = f"{app_container}/api/tasks"
    payload = {'title': 'Extra, Extra', 'extra_field': 'ignórame'}
    resp = requests.post(base_url, json=payload)
    assert resp.status_code == 201
    task = resp.json()
    assert 'extra_field' not in task
    assert task['title'] == 'Extra, Extra'
    requests.delete(f"{base_url}/{task['id']}")

def test_update_task_with_extra_fields(app_container):
    base_url = f"{app_container}/api/tasks"
    task_resp = requests.post(base_url, json={'title': 'Original'})
    task_id = task_resp.json()['id']
    
    payload = {'title': 'Actualizado', 'another_field': 'también ignorado'}
    update_resp = requests.put(f"{base_url}/{task_id}", json=payload)
    assert update_resp.status_code == 200
    task = update_resp.json()
    assert 'another_field' not in task
    assert task['title'] == 'Actualizado'
    
    requests.delete(f"{base_url}/{task_id}")

def test_complex_delete_scenario(app_container):
    base_url = f"{app_container}/api/tasks"

    # Limpiar
    for task in requests.get(base_url).json():
        requests.delete(f"{base_url}/{task['id']}")

    # Crear 5 tareas
    ids = [requests.post(base_url, json={'title': f'T{i}'}).json()['id'] for i in range(5)]
    
    # Eliminar las del medio (índices 1, 2, 3)
    requests.delete(f"{base_url}/{ids[1]}")
    requests.delete(f"{base_url}/{ids[2]}")
    requests.delete(f"{base_url}/{ids[3]}")
    
    # Verificar que solo quedan la primera y la última
    remaining_tasks = requests.get(base_url).json()
    assert len(remaining_tasks) == 2
    
    remaining_ids = {task['id'] for task in remaining_tasks}
    assert remaining_ids == {ids[0], ids[4]}
    
    # Limpiar
    requests.delete(f"{base_url}/{ids[0]}")
    requests.delete(f"{base_url}/{ids[4]}")

def test_get_all_tasks_is_initially_empty(app_container):
    base_url = f"{app_container}/api/tasks"
    
    # Limpiar por si acaso
    for task in requests.get(base_url).json():
        requests.delete(f"{base_url}/{task['id']}")

    # Verificar que está vacío
    resp = requests.get(base_url)
    assert resp.status_code == 200
    assert resp.json() == []



