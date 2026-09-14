export type TaskStatus = "ideas" | "todo" | "progress" | "done";
export type Priority = "high" | "medium" | "low";

export type User = {
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
  completedAt?: string | undefined;
};

const TOKEN_STORAGE_KEY = "kanban_auth_token";

const getBaseUrl = (): string => {
  if (typeof import.meta !== "undefined" && import.meta.env && import.meta.env["VITE_API_URL"]) {
    return (import.meta.env["VITE_API_URL"] as string).replace(/\/$/, "");
  }
  return "http://localhost:8000";
};

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_STORAGE_KEY);
}

function setToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_STORAGE_KEY, token);
}

function removeToken(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_STORAGE_KEY);
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const baseUrl = getBaseUrl();
  const url = `${baseUrl}${path.startsWith("/") ? path : `/${path}`}`;

  const token = getToken();
  const headers = new Headers(options.headers || {});
  headers.set("Accept", "application/json");

  if (!(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  let response: Response;
  try {
    response = await fetch(url, {
      ...options,
      headers,
    });
  } catch (err) {
    const msg =
      err instanceof Error && (err.message === "Failed to fetch" || err.message.includes("NetworkError"))
        ? `Cannot connect to backend at ${baseUrl}. Please ensure the backend is running on port 8000.`
        : err instanceof Error
        ? err.message
        : `Network error connecting to ${baseUrl}`;
    throw new Error(msg);
  }

  if (response.status === 204) {
    return {} as T;
  }

  let data: any;
  const contentType = response.headers.get("content-type");
  if (contentType && contentType.includes("application/json")) {
    data = await response.json();
  } else {
    data = await response.text();
  }

  if (!response.ok) {
    if (response.status === 401) {
      removeToken();
    }
    const message =
      (data && typeof data === "object" && (data.message || data.detail)) ||
      (typeof data === "string" && data) ||
      `Request failed with status ${response.status}`;
    throw new Error(String(message));
  }

  return data as T;
}

export const apiClient = {
  async getSession(): Promise<User | null> {
    const token = getToken();
    if (!token) return null;

    try {
      const data = await request<User | null>("/api/auth/session");
      if (!data) {
        removeToken();
        return null;
      }
      return data;
    } catch {
      removeToken();
      return null;
    }
  },

  async signIn(email: string, password: string): Promise<User> {
    const data = await request<{ id: string; email: string; token: string; user?: User }>(
      "/api/auth/login",
      {
        method: "POST",
        body: JSON.stringify({ email, password }),
      },
    );

    if (data.token) {
      setToken(data.token);
    }

    return {
      id: data.user?.id || data.id,
      email: data.user?.email || data.email,
    };
  },

  async register(email: string, password: string): Promise<User> {
    const data = await request<{ id: string; email: string; token: string; user?: User }>(
      "/api/auth/register",
      {
        method: "POST",
        body: JSON.stringify({ email, password }),
      },
    );

    if (data.token) {
      setToken(data.token);
    }

    return {
      id: data.user?.id || data.id,
      email: data.user?.email || data.email,
    };
  },

  async signOut(): Promise<void> {
    try {
      await request("/api/auth/logout", {
        method: "POST",
      });
    } catch {
      // Ignore network errors during sign out
    } finally {
      removeToken();
    }
  },

  async listTasks(): Promise<Task[]> {
    const token = getToken();
    if (!token) return [];
    try {
      return await request<Task[]>("/api/tasks");
    } catch (error) {
      console.warn("Could not fetch tasks:", error);
      return [];
    }
  },

  async createTask(input: Omit<Task, "id" | "position" | "completedAt">): Promise<Task> {
    return await request<Task>("/api/tasks", {
      method: "POST",
      body: JSON.stringify(input),
    });
  },

  async updateTask(id: string, changes: Partial<Omit<Task, "id">>): Promise<Task> {
    return await request<Task>(`/api/tasks/${id}`, {
      method: "PATCH",
      body: JSON.stringify(changes),
    });
  },

  async moveTask(id: string, status: TaskStatus, targetId?: string): Promise<Task[]> {
    return await request<Task[]>(`/api/tasks/${id}/move`, {
      method: "POST",
      body: JSON.stringify({ status, targetId }),
    });
  },

  async deleteTask(id: string): Promise<void> {
    await request(`/api/tasks/${id}`, {
      method: "DELETE",
    });
  },

  async clearCompleted(): Promise<void> {
    await request("/api/tasks/completed", {
      method: "DELETE",
    });
  },
};

// Aliases for compatibility
export const api = apiClient;
export type MockUser = User;
