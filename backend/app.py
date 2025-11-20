from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from dotenv import load_dotenv

# Carga las variables de entorno desde el archivo .env
load_dotenv()

app = Flask(__name__)
CORS(app) # Habilita CORS para permitir solicitudes desde el frontend

# --- Almacenamiento en memoria para las tareas ---
tasks = []
task_id_counter = 1
# ------------------------------------------------

@app.route('/')
def home():
    return jsonify(message="¡Bienvenido a la API de Gestión de Tareas!")

@app.route('/health')
def health_check():
    return jsonify(status="UP", version=os.environ.get("APP_VERSION", "1.0.0"))

# --- Endpoints de la API para Tareas ---

# OBTENER todas las tareas
@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    return jsonify(tasks)

# OBTENER una tarea específica por ID
@app.route('/api/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    task = next((t for t in tasks if t['id'] == task_id), None)
    if task:
        return jsonify(task)
    return jsonify(error="Tarea no encontrada"), 404

# CREAR una nueva tarea
@app.route('/api/tasks', methods=['POST'])
def create_task():
    global task_id_counter
    data = request.json
    
    if not data or 'title' not in data:
        return jsonify(error="El campo 'title' es requerido"), 400
        
    new_task = {
        'id': task_id_counter,
        'title': data['title'],
        'completed': data.get('completed', False)
    }
    
    tasks.append(new_task)
    task_id_counter += 1
    
    return jsonify(new_task), 201

# ACTUALIZAR una tarea existente (PUT)
@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    task = next((t for t in tasks if t['id'] == task_id), None)
    if not task:
        return jsonify(error="Tarea no encontrada"), 404
        
    data = request.json
    task['title'] = data.get('title', task['title'])
    task['completed'] = data.get('completed', task['completed'])
    
    return jsonify(task)

# ELIMINAR una tarea
@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    global tasks
    task = next((t for t in tasks if t['id'] == task_id), None)
    if not task:
        return jsonify(error="Tarea no encontrada"), 404
        
    tasks = [t for t in tasks if t['id'] != task_id]
    
    return jsonify(message="Tarea eliminada exitosamente"), 200

# -----------------------------------------

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)