import { useState, useEffect, FormEvent } from 'react';
import axios from 'axios';
import './App.css';

// Define la URL base de la API. 
// Asegúrate de que el backend esté corriendo en este puerto.
const API_BASE_URL = 'http://localhost:5000/api';

interface Task {
  id: number;
  title: string;
  completed: boolean;
}

function App() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [newTaskTitle, setNewTaskTitle] = useState('');
  const [error, setError] = useState<string | null>(null);

  // --- Efecto para cargar las tareas al iniciar ---
  useEffect(() => {
    const fetchTasks = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/tasks`);
        setTasks(response.data);
      } catch (err) {
        setError('No se pudieron cargar las tareas. Asegúrate de que el backend esté funcionando.');
        console.error(err);
      }
    };
    fetchTasks();
  }, []);

  // --- Manejador para crear una nueva tarea ---
  const handleCreateTask = async (e: FormEvent) => {
    e.preventDefault();
    if (!newTaskTitle.trim()) {
      alert('El título de la tarea no puede estar vacío.');
      return;
    }
    try {
      const response = await axios.post(`${API_BASE_URL}/tasks`, { title: newTaskTitle });
      setTasks([...tasks, response.data]);
      setNewTaskTitle(''); // Limpiar el input
    } catch (err) {
      setError('Error al crear la tarea.');
      console.error(err);
    }
  };

  // --- Manejador para actualizar el estado de una tarea ---
  const handleToggleCompleted = async (task: Task) => {
    try {
      const updatedTask = { ...task, completed: !task.completed };
      await axios.put(`${API_BASE_URL}/tasks/${task.id}`, updatedTask);
      setTasks(tasks.map(t => (t.id === task.id ? updatedTask : t)));
    } catch (err)
    {
      setError('Error al actualizar la tarea.');
      console.error(err);
    }
  };

  // --- Manejador para eliminar una tarea ---
  const handleDeleteTask = async (taskId: number) => {
    try {
      await axios.delete(`${API_BASE_URL}/tasks/${taskId}`);
      setTasks(tasks.filter(t => t.id !== taskId));
    } catch (err) {
      setError('Error al eliminar la tarea.');
      console.error(err);
    }
  };

  return (
    <div className="app-container">
      <h1>Lista de Tareas</h1>
      
      {error && <p style={{ color: 'red' }}>{error}</p>}

      <form className="task-input-form" onSubmit={handleCreateTask}>
        <input
          type="text"
          className="task-input"
          value={newTaskTitle}
          onChange={(e) => setNewTaskTitle(e.target.value)}
          placeholder="Añadir una nueva tarea..."
        />
        <button type="submit" className="add-btn">Añadir</button>
      </form>

      <ul className="task-list">
        {tasks.map(task => (
          <li key={task.id} className={`task-item ${task.completed ? 'completed' : ''}`}>
            <input
              type="checkbox"
              checked={task.completed}
              onChange={() => handleToggleCompleted(task)}
            />
            <span className="task-title">{task.title}</span>
            <button onClick={() => handleDeleteTask(task.id)} className="delete-btn">
              Eliminar
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default App;