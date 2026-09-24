import { test, expect } from '@playwright/test';

/**
 * End-to-End Test Suite against docker-compose stack (App + PostgreSQL)
 *
 * Scenarios tested:
 * 1. Log in as a user.
 * 2. Create a task.
 * 3. Move it across different columns (Ideas -> To Do -> In Progress -> Done).
 * 4. Delete a task.
 * 5. Log out, log back in, and ensure persistent database state didn't reset or change.
 */
test.describe('Kanban Board Full Lifecycle E2E', () => {
  const timestamp = Date.now().toString().slice(-6);
  const userEmail = `e2e_tester_${timestamp}@example.com`;
  const userPassword = `Pass#${timestamp}!2026`;

  const primaryTaskTitle = `Feature Task ${timestamp}`;
  const taskToDeleteTitle = `Temporary Task ${timestamp}`;

  test.beforeEach(async ({ page }) => {
    // Navigate to base URL and ensure clean unauthenticated session state
    await page.goto('/');
    await page.evaluate(() => localStorage.clear());
    await page.reload();
  });

  test('User can login, create tasks, move across columns, delete a task, and preserve state after logout/login', async ({ page }) => {
    // -------------------------------------------------------------------------
    // 1. Log in as a user (Register fresh user account)
    // -------------------------------------------------------------------------
    await expect(page.getByText('Korda')).toBeVisible();

    // Switch to register mode
    const createAccountButton = page.getByRole('button', { name: 'Create an account' });
    if (await createAccountButton.isVisible()) {
      await createAccountButton.click();
      await expect(page.getByRole('heading', { name: 'Start with a blank board.' })).toBeVisible();
    }

    await page.locator('input[type="email"]').fill(userEmail);
    await page.locator('input[type="password"]').fill(userPassword);
    await page.getByRole('button', { name: /Create account|Sign in/i }).click();

    // Verify successful login into board
    await expect(page.getByRole('heading', { name: 'Today, Focus' })).toBeVisible({ timeout: 15000 });
    await expect(page.getByText(`Signed in as ${userEmail}`)).toBeVisible();

    // Locate column sections
    const ideasColumn = page.locator('section').filter({ has: page.getByRole('heading', { name: 'Ideas' }) });
    const todoColumn = page.locator('section').filter({ has: page.getByRole('heading', { name: 'To Do' }) });
    const progressColumn = page.locator('section').filter({ has: page.getByRole('heading', { name: 'In Progress' }) });
    const doneColumn = page.locator('section').filter({ has: page.getByRole('heading', { name: 'Done' }) });

    // -------------------------------------------------------------------------
    // 2. Create tasks
    // -------------------------------------------------------------------------
    // 2a. Create the primary task in 'Ideas'
    await ideasColumn.getByRole('button', { name: /Add task/i }).first().click();
    await expect(page.getByRole('heading', { name: 'Add task' })).toBeVisible();

    await page.getByPlaceholder('Name the next thing').fill(primaryTaskTitle);
    await page.getByPlaceholder('Optional notes').fill('Comprehensive end-to-end test verification task.');
    await page.getByRole('button', { name: 'high', exact: true }).click();
    await page.getByRole('button', { name: 'Save changes' }).click();

    // Verify task appears in 'Ideas' column
    const primaryTaskCard = ideasColumn.locator('article').filter({ hasText: primaryTaskTitle });
    await expect(primaryTaskCard).toBeVisible({ timeout: 10000 });

    // 2b. Create a secondary task to be deleted in step 4
    await ideasColumn.getByRole('button', { name: /Add task/i }).first().click();
    await expect(page.getByRole('heading', { name: 'Add task' })).toBeVisible();
    await page.getByPlaceholder('Name the next thing').fill(taskToDeleteTitle);
    await page.getByRole('button', { name: 'Save changes' }).click();

    const taskToDeleteCard = ideasColumn.locator('article').filter({ hasText: taskToDeleteTitle });
    await expect(taskToDeleteCard).toBeVisible({ timeout: 10000 });

    // -------------------------------------------------------------------------
    // 3. Move it across the different columns (Ideas -> To Do -> In Progress -> Done)
    // -------------------------------------------------------------------------
    // 3a. Move from Ideas to To Do
    await primaryTaskCard.dragTo(todoColumn);
    const taskInTodo = todoColumn.locator('article').filter({ hasText: primaryTaskTitle });
    await expect(taskInTodo).toBeVisible({ timeout: 10000 });
    await expect(ideasColumn.locator('article').filter({ hasText: primaryTaskTitle })).not.toBeVisible();

    // 3b. Move from To Do to In Progress
    await taskInTodo.dragTo(progressColumn);
    const taskInProgress = progressColumn.locator('article').filter({ hasText: primaryTaskTitle });
    await expect(taskInProgress).toBeVisible({ timeout: 10000 });
    await expect(todoColumn.locator('article').filter({ hasText: primaryTaskTitle })).not.toBeVisible();

    // 3c. Move from In Progress to Done
    await taskInProgress.dragTo(doneColumn);
    const taskInDone = doneColumn.locator('article').filter({ hasText: primaryTaskTitle });
    await expect(taskInDone).toBeVisible({ timeout: 10000 });
    await expect(progressColumn.locator('article').filter({ hasText: primaryTaskTitle })).not.toBeVisible();

    // Verify done status indicator appears
    await expect(taskInDone.getByText(/Done/i)).toBeVisible();

    // -------------------------------------------------------------------------
    // 4. Delete a task
    // -------------------------------------------------------------------------
    // Click the temporary task in 'Ideas' column to open the edit dialog
    await taskToDeleteCard.click();
    await expect(page.getByRole('heading', { name: 'Edit task' })).toBeVisible();

    // Handle the confirmation dialog automatically
    page.once('dialog', async (dialog) => {
      expect(dialog.message()).toContain(`Delete “${taskToDeleteTitle}”?`);
      await dialog.accept();
    });

    await page.getByRole('button', { name: /Delete/i }).click();

    // Verify task is removed from the board
    await expect(page.locator('article').filter({ hasText: taskToDeleteTitle })).not.toBeVisible({ timeout: 10000 });

    // -------------------------------------------------------------------------
    // 5. Log out and login back and ensure state didn't reset or change
    // -------------------------------------------------------------------------
    // 5a. Sign out
    await page.getByRole('button', { name: /Sign out/i }).click();
    await expect(page.getByRole('heading', { name: 'Back to focus.' })).toBeVisible({ timeout: 10000 });

    // 5b. Sign back in with the same credentials
    await page.locator('input[type="email"]').fill(userEmail);
    await page.locator('input[type="password"]').fill(userPassword);
    await page.getByRole('button', { name: 'Sign in' }).click();

    // Verify board loads for the authenticated user
    await expect(page.getByRole('heading', { name: 'Today, Focus' })).toBeVisible({ timeout: 15000 });
    await expect(page.getByText(`Signed in as ${userEmail}`)).toBeVisible();

    // 5c. Ensure deleted task is still gone (not reset)
    await expect(page.locator('article').filter({ hasText: taskToDeleteTitle })).not.toBeVisible();

    // 5d. Ensure the moved task is still in 'Done' column (persisted in PostgreSQL)
    const persistedDoneTask = doneColumn.locator('article').filter({ hasText: primaryTaskTitle });
    await expect(persistedDoneTask).toBeVisible({ timeout: 10000 });
    await expect(persistedDoneTask.getByText(/Done/i)).toBeVisible();
    await expect(ideasColumn.locator('article').filter({ hasText: primaryTaskTitle })).not.toBeVisible();
    await expect(todoColumn.locator('article').filter({ hasText: primaryTaskTitle })).not.toBeVisible();
    await expect(progressColumn.locator('article').filter({ hasText: primaryTaskTitle })).not.toBeVisible();
  });
});
