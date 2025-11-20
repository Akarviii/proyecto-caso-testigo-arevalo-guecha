import { test, expect } from '@playwright/test';

test.describe('To-Do List E2E Tests - Simplified', () => {

  const tasksApiUrl = 'http://localhost:5000/api/tasks';

  test.beforeEach(async ({ page }) => {
    // Navigate to the app and ensure input is visible
    await page.goto('/');
    await expect(page.getByPlaceholder('Añadir una nueva tarea...')).toBeVisible({ timeout: 10000 });

    // --- CLEANUP: Ensure a clean state for each test by deleting all existing tasks ---
    // Wait for initial tasks to load if any, before attempting to delete them
    await page.waitForLoadState('networkidle'); 
    await page.waitForTimeout(500); // Give the UI a moment to render after networkidle

    // Use page.evaluate to make direct API calls from the browser context
    // This is a more robust way to clear backend state for E2E tests without relying on UI interactions
    await page.evaluate(async (apiUrl) => {
        try {
            const response = await fetch(apiUrl);
            if (!response.ok) {
                throw new Error(`Failed to fetch tasks: ${response.statusText}`);
            }
            const tasks = await response.json();
            for (const task of tasks) {
                const deleteResponse = await fetch(`${apiUrl}/${task.id}`, { method: 'DELETE' });
                if (!deleteResponse.ok) {
                    console.error(`Failed to delete task ${task.id}: ${deleteResponse.statusText}`);
                }
            }
        } catch (error) {
            console.error('Error during cleanup:', error);
        }
    }, tasksApiUrl);

    // Verify UI is empty after cleanup
    const taskList = page.locator('.task-list');
    await expect(taskList).toBeEmpty({ timeout: 5000 }); // Added timeout for clarity
  });

  test('should add a new task', async ({ page }) => {
    const taskTitle = `New Task ${Date.now()}`;
    const taskInput = page.getByPlaceholder('Añadir una nueva tarea...');
    const addButton = page.getByRole('button', { name: 'Añadir' });

    await taskInput.fill(taskTitle);
    const postPromise = page.waitForResponse(res => res.url().startsWith(tasksApiUrl) && res.request().method() === 'POST');
    await addButton.click();
    const postResponse = await postPromise;
    expect(postResponse.status()).toBe(201);

    const listItem = page.locator('.task-item', { hasText: taskTitle });
    await expect(listItem).toBeVisible();
  });

  test('should mark a task as completed', async ({ page }) => {
    const taskTitle = `Complete Task ${Date.now()}`;
    const taskInput = page.getByPlaceholder('Añadir una nueva tarea...');
    const addButton = page.getByRole('button', { name: 'Añadir' });

    // Create task first
    const postPromise = page.waitForResponse(res => res.url().startsWith(tasksApiUrl) && res.request().method() === 'POST');
    await taskInput.fill(taskTitle);
    await addButton.click();
    await postPromise;

    const listItem = page.locator('.task-item', { hasText: taskTitle });
    await expect(listItem).toBeVisible();

    const checkbox = listItem.getByRole('checkbox');
    // Mark as completed
    const putPromise = page.waitForResponse(res => res.url().includes(tasksApiUrl) && res.request().method() === 'PUT');
    await expect(checkbox).toBeEnabled(); // Ensure checkbox is enabled before clicking
    await checkbox.click(); // Use click() instead of check() for more direct interaction
    await putPromise;

    // Add a small timeout to allow the browser to render the class change
    await page.waitForTimeout(100); 

    await expect(listItem).toHaveClass(/completed/);
  });

  test('should delete a task', async ({ page }) => {
    const taskTitle = `Delete Task ${Date.now()}`;
    const taskInput = page.getByPlaceholder('Añadir una nueva tarea...');
    const addButton = page.getByRole('button', { name: 'Añadir' });

    // Create task first
    const postPromise = page.waitForResponse(res => res.url().startsWith(tasksApiUrl) && res.request().method() === 'POST');
    await taskInput.fill(taskTitle);
    await addButton.click();
    await postPromise;

    const listItem = page.locator('.task-item', { hasText: taskTitle });
    await expect(listItem).toBeVisible();

    const deleteButton = listItem.getByRole('button', { name: 'Eliminar' });

    // Delete the task
    const deletePromise = page.waitForResponse(res => res.url().includes(tasksApiUrl) && res.request().method() === 'DELETE');
    await deleteButton.click();
    await deletePromise;

    // Verify it's gone
    await expect(listItem).not.toBeVisible();
  });

  test('should not allow creating a task with an empty title', async ({ page }) => {
    const addButton = page.getByRole('button', { name: 'Añadir' });
    
    let alertMessage = '';
    page.on('dialog', async dialog => {
      alertMessage = dialog.message();
      await dialog.dismiss();
    });
    
    await addButton.click();
    
    expect(alertMessage).toContain('El título de la tarea no puede estar vacío.');
  });

  test('should unmark a completed task', async ({ page }) => {
    const taskTitle = `Unmark Task ${Date.now()}`;
    const taskInput = page.getByPlaceholder('Añadir una nueva tarea...');
    const addButton = page.getByRole('button', { name: 'Añadir' });

    // Create task
    await taskInput.fill(taskTitle);
    await addButton.click();
    const listItem = page.locator('.task-item', { hasText: taskTitle });
    await expect(listItem).toBeVisible();

    const checkbox = listItem.getByRole('checkbox');
    // Mark as completed
    await checkbox.click(); // This will trigger a PUT
    await expect(listItem).toHaveClass(/completed/);

    // Unmark the task
    const putPromise = page.waitForResponse(res => res.url().includes(tasksApiUrl) && res.request().method() === 'PUT');
    await checkbox.click(); // This will trigger another PUT
    await putPromise;

    await page.waitForTimeout(100); 
    await expect(listItem).not.toHaveClass(/completed/);

    // Cleanup
    await listItem.getByRole('button', { name: 'Eliminar' }).click();
  });

  test('should display a very long task title correctly', async ({ page }) => {
    const longTitle = 'A'.repeat(200); // A very long title
    const taskInput = page.getByPlaceholder('Añadir una nueva tarea...');
    const addButton = page.getByRole('button', { name: 'Añadir' });

    await taskInput.fill(longTitle);
    await addButton.click();

    const listItem = page.locator('.task-item', { hasText: longTitle });
    await expect(listItem).toBeVisible();
    await expect(listItem.locator('.task-title')).toHaveText(longTitle);

    // Cleanup
    await listItem.getByRole('button', { name: 'Eliminar' }).click();
  });

  test('should display special characters in task title correctly', async ({ page }) => {
    const specialTitle = 'Mi Tarea con Ñáçüé!@#$%^&*()_+';
    const taskInput = page.getByPlaceholder('Añadir una nueva tarea...');
    const addButton = page.getByRole('button', { name: 'Añadir' });

    await taskInput.fill(specialTitle);
    await addButton.click();

    const listItem = page.locator('.task-item', { hasText: specialTitle });
    await expect(listItem).toBeVisible();
    await expect(listItem.locator('.task-title')).toHaveText(specialTitle);

    // Cleanup
    await listItem.getByRole('button', { name: 'Eliminar' }).click();
  });






});