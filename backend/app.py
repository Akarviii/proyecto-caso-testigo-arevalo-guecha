from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from dotenv import load_dotenv
from services import task_service # Import the task service
from models.task_model import Task # Import the Task class for type hinting and .to_dict()

# Carga las variables de entorno desde el archivo .env
load_dotenv()

app = Flask(__name__)
CORS(app) # Habilita CORS para permitir solicitudes desde el frontend

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
    # Convert Task objects to dictionaries for jsonify
    return jsonify([task.to_dict() for task in task_service.get_all_tasks()])

# OBTENER una tarea específica por ID
@app.route('/api/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    task = task_service.get_task_by_id(task_id)
    if task:
        return jsonify(task.to_dict()) # Convert Task object to dictionary
    return jsonify(error="Tarea no encontrada"), 404

# CREAR una nueva tarea
@app.route('/api/tasks', methods=['POST'])
def create_task():
    data = request.json
    
    if not data or 'title' not in data:
        return jsonify(error="El campo 'title' es requerido"), 400
        
    try:
        new_task = task_service.create_task(data['title'], data.get('completed', False))
        return jsonify(new_task.to_dict()), 201 # Convert Task object to dictionary
    except ValueError as e: # Catch validation errors from Task model
        return jsonify(error=str(e)), 400

# ACTUALIZAR una tarea existente (PUT)
@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    data = request.json
    
    # Optional: Basic validation for title/completed if provided
    if 'title' in data and not isinstance(data['title'], str):
        return jsonify(error="El campo 'title' debe ser una cadena de texto"), 400
    if 'completed' in data and 'completed' in data and not isinstance(data['completed'], bool):
        return jsonify(error="El campo 'completed' debe ser un booleano"), 400

    updated_task = task_service.update_task(
        task_id,
        title=data.get('title'),
        completed=data.get('completed')
    )
    if updated_task:
        return jsonify(updated_task.to_dict()) # Convert Task object to dictionary
    return jsonify(error="Tarea no encontrada"), 404

# ELIMINAR una tarea
@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    if task_service.delete_task(task_id):
        return jsonify(message="Tarea eliminada exitosamente"), 200
    return jsonify(error="Tarea no encontrada"), 404

# -----------------------------------------

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)