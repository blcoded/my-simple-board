export type TaskStatus = "ideas" | "todo" | "progress" | "done";
export type Priority = "high" | "medium" | "low";

export type MockUser = {
  id: string;
  email: string;
};

export type Task = {
  id: string;
  title: string;
  description: string;
  dueDate: string;
  priority: Priority;
  status: TaskStatus;
  position: number;
  completedAt?: string;
};

type MockState = {
  user: MockUser | null;
  boards: Record<string, Task[]>;
};

const seedTasks: Task[] = [
  {
    id: "task-onboarding",
    title: "Sketch onboarding flow",
    description: "Map the first three screens before writing any code.",
    dueDate: "2026-03-03",
    priority: "high",
    status: "ideas",
    position: 0,
  },
  {
    id: "task-tokens",
    title: "Audit color tokens",
    description: "Consolidate the 40 shades into a single scale.",
    dueDate: "2026-03-15",
    priority: "medium",
    status: "ideas",
    position: 1,
  },
  {
    id: "task-drag-physics",
    title: "Read on drag physics",
    description: "Two articles on easing curves for cards.",
    dueDate: "",
    priority: "low",
    status: "ideas",
    position: 2,
  },
  {
    id: "task-auth",
    title: "Build auth scaffold",
    description: "Routes, mock backend calls, session state.",
    dueDate: "2026-03-12",
    priority: "high",
    status: "todo",
    position: 0,
  },
  {
    id: "task-dnd",
    title: "Wire drag-and-drop",
    description: "Reorder within a column plus cross-lane moves.",
    dueDate: "2026-03-14",
    priority: "medium",
    status: "todo",
    position: 1,
  },
  {
    id: "task-empty-states",
    title: "Trim copy in empty states",
    description: "Keep each under nine words.",
    dueDate: "",
    priority: "low",
    status: "todo",
    position: 2,
  },
  {
    id: "task-card",
    title: "Design the task card",
    description: "Finalize priority chips and due-date states.",
    dueDate: "2026-03-10",
    priority: "high",
    status: "progress",
    position: 0,
  },
  {
    id: "task-api",
    title: "Set up mock API",
    description: "Stubbed endpoints for tasks and auth.",
    dueDate: "2026-03-09",
    priority: "medium",
    status: "done",
    position: 0,
    completedAt: "2026-03-09",
  },
  {
    id: "task-type",
    title: "Pick type pairing",
    description: "Space Grotesk for display, Inter for body.",
    dueDate: "2026-03-08",
    priority: "low",
    status: "done",
    position: 1,
    completedAt: "2026-03-08",
  },
];

let state: MockState = {
  user: { id: "demo-user", email: "ada@example.com" },
  boards: { "demo-user": structuredClone(seedTasks) },
};

const delay = (value: number) => new Promise((resolve) => setTimeout(resolve, value));

function cloneTasks(tasks: Task[]) {
  return tasks.map((task) => ({ ...task }));
}

function currentTasks() {
  return state.user ? state.boards[state.user.id] ?? [] : [];
}

function normalizePositions(tasks: Task[]) {
  const statuses: TaskStatus[] = ["ideas", "todo", "progress", "done"];
  statuses.forEach((status) => {
    tasks
      .filter((task) => task.status === status)
      .sort((a, b) => a.position - b.position)
      .forEach((task, index) => {
        task.position = index;
      });
  });
}

export const mockApi = {
  async getSession() {
    await delay(180);
    return state.user;
  },

  async signIn(email: string, password: string) {
    await delay(420);
    if (!email.trim() || password.trim().length < 4) {
      throw new Error("Enter an email and a password with at least four characters.");
    }
    const normalizedEmail = email.trim().toLowerCase();
    state.user = { id: normalizedEmail, email: normalizedEmail };
    state.boards[normalizedEmail] ??= [];
    if (normalizedEmail === "ada@example.com" && state.boards[normalizedEmail].length === 0) {
      state.boards[normalizedEmail] = structuredClone(seedTasks);
    }
    return state.user;
  },

  async register(email: string, password: string) {
    await delay(520);
    if (!email.includes("@") || password.trim().length < 4) {
      throw new Error("Use a valid email and a password with at least four characters.");
    }
    const normalizedEmail = email.trim().toLowerCase();
    state.user = { id: normalizedEmail, email: normalizedEmail };
    state.boards[normalizedEmail] = [];
    return state.user;
  },

  async signOut() {
    await delay(160);
    state.user = null;
  },

  async listTasks() {
    await delay(240);
    return cloneTasks(currentTasks());
  },

  async createTask(input: Omit<Task, "id" | "position" | "completedAt">) {
    await delay(260);
    if (!state.user) throw new Error("Sign in to add a task.");
    const tasks = currentTasks();
    const position = tasks.filter((task) => task.status === input.status).length;
    const task: Task = {
      ...input,
      id: `task-${Date.now()}`,
      position,
      ...(input.status === "done" ? { completedAt: new Date().toISOString() } : {}),
    };
    state.boards[state.user.id] = [...tasks, task];
    return { ...task };
  },

  async updateTask(id: string, changes: Partial<Omit<Task, "id">>) {
    await delay(260);
    const tasks = currentTasks();
    const existing = tasks.find((task) => task.id === id);
    if (!existing) throw new Error("That task is no longer available.");
    state.boards[state.user?.id ?? ""] = tasks.map((task) =>
      task.id === id
        ? {
            ...task,
            ...changes,
            ...(changes.status === "done" && task.status !== "done"
              ? { completedAt: new Date().toISOString() }
              : {}),
            ...(changes.status && changes.status !== "done" ? { completedAt: undefined } : {}),
          }
        : task,
    );
    normalizePositions(currentTasks());
    const updated = currentTasks().find((task) => task.id === id);
    if (!updated) throw new Error("That task is no longer available.");
    return { ...updated };
  },

  async moveTask(id: string, status: TaskStatus, targetId?: string) {
    await delay(180);
    if (!state.user) throw new Error("Sign in to move a task.");
    const tasks = cloneTasks(currentTasks());
    const moving = tasks.find((task) => task.id === id);
    if (!moving) throw new Error("That task is no longer available.");
    const destination = tasks.filter((task) => task.status === status && task.id !== id);
    const oldIndex = destination.findIndex((task) => task.id === targetId);
    const insertAt = oldIndex >= 0 ? oldIndex : destination.length;
    moving.status = status;
    moving.completedAt = status === "done" ? new Date().toISOString() : undefined;
    destination.splice(insertAt, 0, moving);
    const remaining = tasks.filter((task) => task.id !== id && task.status !== status);
    state.boards[state.user.id] = [...remaining, ...destination];
    normalizePositions(currentTasks());
    return cloneTasks(currentTasks());
  },

  async deleteTask(id: string) {
    await delay(220);
    if (!state.user) throw new Error("Sign in to delete a task.");
    state.boards[state.user.id] = currentTasks().filter((task) => task.id !== id);
    normalizePositions(currentTasks());
  },

  async clearCompleted() {
    await delay(260);
    if (!state.user) throw new Error("Sign in to clear completed tasks.");
    state.boards[state.user.id] = currentTasks().filter((task) => task.status !== "done");
    normalizePositions(currentTasks());
  },
};