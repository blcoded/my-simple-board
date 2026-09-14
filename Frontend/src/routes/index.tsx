import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import {
  CalendarDays,
  Check,
  ChevronDown,
  GripVertical,
  LogOut,
  Plus,
  Search,
  Trash2,
  X,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { apiClient, type Priority, type Task, type TaskStatus } from "@/lib/api-client";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Korda — Personal Kanban" },
      { name: "description", content: "A focused personal Kanban board for organizing tasks from idea to done." },
      { property: "og:title", content: "Korda — Personal Kanban" },
      { property: "og:description", content: "A focused personal Kanban board for organizing tasks from idea to done." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: KordaApp,
});

const columns: { id: TaskStatus; label: string }[] = [
  { id: "ideas", label: "Ideas" },
  { id: "todo", label: "To Do" },
  { id: "progress", label: "In Progress" },
  { id: "done", label: "Done" },
];

const priorities: Priority[] = ["high", "medium", "low"];

function KordaApp() {
  const [user, setUser] = useState<{ id: string; email: string } | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [search, setSearch] = useState("");
  const [priorityFilter, setPriorityFilter] = useState<Priority | "all">("all");
  const [dueFilter, setDueFilter] = useState<DueFilter>("all");
  const [taskDialog, setTaskDialog] = useState<{ mode: "create" | "edit"; status: TaskStatus; task?: Task } | null>(null);
  const [draggedTask, setDraggedTask] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    async function init() {
      try {
        const session = await apiClient.getSession();
        if (!active) return;
        setUser(session);
        if (session) {
          const nextTasks = await apiClient.listTasks();
          if (!active) return;
          setTasks(nextTasks);
        } else {
          setTasks([]);
        }
      } catch (error) {
        console.error("Failed to initialize board:", error);
        if (active) {
          setUser(null);
          setTasks([]);
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    init();
    return () => {
      active = false;
    };
  }, []);

  const visibleTasks = useMemo(() => {
    const query = search.trim().toLowerCase();
    return tasks.filter((task) => {
      const matchesSearch = !query || `${task.title} ${task.description}`.toLowerCase().includes(query);
      const matchesPriority = priorityFilter === "all" || task.priority === priorityFilter;
      const matchesDue = dueFilter === "all" || getDueState(task.dueDate) === dueFilter;
      return matchesSearch && matchesPriority && matchesDue;
    });
  }, [dueFilter, priorityFilter, search, tasks]);

  async function refreshTasks() {
    try {
      setTasks(await apiClient.listTasks());
    } catch (error) {
      console.error("Failed to refresh tasks:", error);
    }
  }

  async function handleMove(id: string, status: TaskStatus, targetId?: string) {
    setDraggedTask(null);
    try {
      await apiClient.moveTask(id, status, targetId);
      await refreshTasks();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Could not move that task.");
    }
  }

  async function handleSignOut() {
    await apiClient.signOut();
    setUser(null);
    setTasks([]);
    toast.success("You’re signed out.");
  }

  if (loading) return <LoadingScreen />;
  if (!user) {
    return (
      <AuthScreen
        mode={authMode}
        onModeChange={setAuthMode}
        onSignedIn={async (signedInUser) => {
          setUser(signedInUser);
          try {
            const nextTasks = await apiClient.listTasks();
            setTasks(nextTasks);
          } catch (err) {
            console.error("Failed to load tasks after sign in:", err);
          }
        }}
      />
    );
  }

  const openTasks = tasks.filter((task) => task.status !== "done").length;
  const doneTasks = tasks.filter((task) => task.status === "done").length;

  return (
    <main className="min-h-screen bg-background text-foreground">
      <div className="mx-auto max-w-[1440px] px-5 py-6 sm:px-8 lg:px-10 lg:py-8">
        <header className="flex flex-wrap items-center justify-between gap-4 border-b-2 border-foreground pb-5">
          <div className="flex items-center gap-3">
            <div className="grid size-9 place-items-center rounded-md bg-primary font-display text-lg font-bold text-primary-foreground">K</div>
            <span className="font-display text-sm font-semibold uppercase tracking-[0.2em]">Korda</span>
          </div>
          <div className="flex items-center gap-3 sm:gap-4">
            <span className="hidden text-sm text-muted-foreground sm:inline">Signed in as {user.email}</span>
            <div className="grid size-8 place-items-center rounded-full bg-foreground text-xs font-semibold text-background">{initials(user.email)}</div>
            <Button variant="ghost" size="sm" className="gap-1.5 px-1.5 text-muted-foreground hover:text-foreground" onClick={handleSignOut}>
              <LogOut /> <span className="hidden sm:inline">Sign out</span>
            </Button>
          </div>
        </header>

        <section className="mt-9 flex flex-col gap-7 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.25em] text-muted-foreground">Personal board</p>
            <h1 className="mt-2 max-w-3xl font-display text-5xl font-bold leading-[0.9] tracking-tight text-foreground sm:text-7xl lg:text-[5.5rem]">Today, Focus</h1>
            <p className="mt-4 max-w-md text-sm leading-relaxed text-muted-foreground">Drag tasks between lanes. Priority marks importance, position marks your order.</p>
          </div>
          <div className="flex flex-col gap-3 lg:items-end">
            <label className="flex w-full items-center gap-2 rounded-full border border-input bg-card px-4 py-2.5 shadow-sm lg:w-80">
              <Search className="size-4 text-muted-foreground" />
              <span className="sr-only">Search tasks</span>
              <Input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search tasks, notes…" className="h-auto border-0 bg-transparent p-0 text-sm shadow-none focus-visible:ring-0" />
              {search && <Button variant="ghost" size="icon" className="size-6 shrink-0" onClick={() => setSearch("")} aria-label="Clear search"><X /></Button>}
            </label>
            <div className="flex flex-wrap gap-2">
              <FilterSelect value={priorityFilter} onChange={setPriorityFilter} options={["all", ...priorities]} label="Priority" />
              <FilterSelect value={dueFilter} onChange={setDueFilter} options={["all", "overdue", "today", "upcoming", "none"]} label="Due" />
              {(priorityFilter !== "all" || dueFilter !== "all" || search) && <Button variant="ghost" size="sm" className="rounded-full text-muted-foreground" onClick={() => { setPriorityFilter("all"); setDueFilter("all"); setSearch(""); }}>Reset</Button>}
            </div>
          </div>
        </section>

        <section className="mt-8 flex gap-5 overflow-x-auto pb-3 scrollbar-thin xl:grid xl:grid-cols-4 xl:overflow-visible">
          {columns.map((column) => {
            const columnTasks = visibleTasks.filter((task) => task.status === column.id).sort((a, b) => a.position - b.position);
            const totalColumnTasks = tasks.filter((task) => task.status === column.id).length;
            return (
              <BoardColumn
                key={column.id}
                column={column}
                tasks={columnTasks}
                totalCount={totalColumnTasks}
                draggedTask={draggedTask}
                onDragStart={setDraggedTask}
                onDrop={(targetId) => draggedTask && handleMove(draggedTask, column.id, targetId)}
                onOpenTask={(task) => setTaskDialog({ mode: "edit", status: task.status, task })}
                onAdd={() => setTaskDialog({ mode: "create", status: column.id })}
                onClear={async () => {
                  if (!window.confirm("Clear every completed task from the board?")) return;
                  try {
                    await apiClient.clearCompleted();
                    await refreshTasks();
                    toast.success("Completed tasks cleared.");
                  } catch (error) {
                    toast.error(error instanceof Error ? error.message : "Could not clear completed tasks.");
                  }
                }}
              />
            );
          })}
        </section>

        <footer className="mt-8 flex flex-wrap items-center justify-between gap-3 text-xs text-muted-foreground">
          <span>Mock backend · {tasks.length} tasks on this board</span>
          <span>{openTasks} open · {doneTasks} done</span>
        </footer>
      </div>

      <TaskDialog
        state={taskDialog}
        onOpenChange={(open) => !open && setTaskDialog(null)}
        onSaved={async () => { await refreshTasks(); setTaskDialog(null); }}
      />
    </main>
  );
}

function BoardColumn({ column, tasks, totalCount, draggedTask, onDragStart, onDrop, onOpenTask, onAdd, onClear }: {
  column: { id: TaskStatus; label: string };
  tasks: Task[];
  totalCount: number;
  draggedTask: string | null;
  onDragStart: (id: string) => void;
  onDrop: (targetId?: string) => void;
  onOpenTask: (task: Task) => void;
  onAdd: () => void;
  onClear: () => void;
}) {
  return (
    <section className={`flex min-h-[420px] w-[305px] shrink-0 flex-col rounded-xl border border-border bg-card p-3 shadow-sm transition ${draggedTask ? "ring-2 ring-primary/40" : ""}`} onDragOver={(event) => event.preventDefault()} onDrop={() => onDrop()}>
      <div className="flex items-center justify-between px-1 pb-3">
        <div className="flex items-center gap-2">
          <span className={`size-2 rounded-full ${column.id === "done" ? "bg-chart-2" : column.id === "todo" ? "bg-primary" : column.id === "progress" ? "bg-chart-3" : "bg-muted-foreground"}`} />
          <h2 className="font-display font-semibold">{column.label}</h2>
          <span className="rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">{totalCount}</span>
        </div>
        {column.id === "done" && totalCount > 0 ? (
          <Button variant="ghost" size="sm" className="h-7 px-2 text-xs text-muted-foreground hover:text-destructive" onClick={onClear}>Clear</Button>
        ) : (
          <Button variant="ghost" size="icon" className="size-7 text-muted-foreground hover:text-primary" onClick={onAdd} aria-label={`Add task to ${column.label}`}><Plus /></Button>
        )}
      </div>
      <div className="flex flex-1 flex-col gap-3">
        {tasks.map((task) => <TaskCard key={task.id} task={task} isDragging={draggedTask === task.id} onDragStart={onDragStart} onDrop={onDrop} onOpen={onOpenTask} />)}
        {tasks.length === 0 && <div className="flex flex-1 items-center justify-center py-10 text-center text-sm text-muted-foreground">{totalCount === 0 ? "No tasks yet" : "No matching tasks"}</div>}
      </div>
      <Button variant="ghost" className="mt-3 w-full rounded-lg border border-dashed border-border py-2.5 text-sm font-semibold text-muted-foreground hover:border-primary hover:text-primary" onClick={onAdd}><Plus /> Add task</Button>
    </section>
  );
}

function TaskCard({ task, isDragging, onDragStart, onDrop, onOpen }: { task: Task; isDragging: boolean; onDragStart: (id: string) => void; onDrop: (targetId?: string) => void; onOpen: (task: Task) => void }) {
  const dueState = getDueState(task.dueDate);
  return (
    <article draggable onDragStart={() => onDragStart(task.id)} onDragEnd={() => onDragStart("")} onDragOver={(event) => event.preventDefault()} onDrop={(event) => { event.stopPropagation(); onDrop(task.id); }} onClick={() => onOpen(task)} onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") onOpen(task); }} tabIndex={0} className={`group cursor-grab rounded-lg border bg-background p-3.5 text-left shadow-sm outline-none transition hover:-translate-y-0.5 hover:ring-1 hover:ring-primary/50 focus-visible:ring-2 focus-visible:ring-primary active:cursor-grabbing ${isDragging ? "opacity-40" : ""} ${task.status === "done" ? "opacity-65" : ""} ${task.status === "todo" && task.priority === "high" ? "border-2 border-primary" : "border-border"}`}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex min-w-0 items-start gap-1.5"><GripVertical className="mt-0.5 size-3.5 shrink-0 text-muted-foreground/60 opacity-0 transition group-hover:opacity-100" /><span className={`text-sm font-semibold leading-snug ${task.status === "done" ? "text-muted-foreground line-through" : "text-foreground"}`}>{task.title}</span></div>
        <PriorityBadge priority={task.priority} />
      </div>
      {task.description && <p className="mt-1.5 line-clamp-2 text-xs leading-relaxed text-muted-foreground">{task.description}</p>}
      <div className="mt-3 flex items-center justify-between gap-2">
        <span className={`text-[11px] font-medium ${dueState === "overdue" ? "text-destructive" : dueState === "today" ? "text-chart-4" : "text-muted-foreground"}`}>{dueLabel(task, dueState)}</span>
        {task.status === "done" && <span className="grid size-4 place-items-center rounded-full bg-muted text-muted-foreground"><Check className="size-2.5" /></span>}
        {task.status !== "done" && task.dueDate && <span className="text-[11px] text-muted-foreground">{formatDate(task.dueDate)}</span>}
      </div>
    </article>
  );
}

function TaskDialog({ state, onOpenChange, onSaved }: { state: { mode: "create" | "edit"; status: TaskStatus; task?: Task } | null; onOpenChange: (open: boolean) => void; onSaved: () => Promise<void> }) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [priority, setPriority] = useState<Priority>("medium");
  const [saving, setSaving] = useState(false);
  useEffect(() => {
    setTitle(state?.task?.title ?? "");
    setDescription(state?.task?.description ?? "");
    setDueDate(state?.task?.dueDate ?? "");
    setPriority(state?.task?.priority ?? "medium");
  }, [state]);
  if (!state) return null;
  const activeState = state;
  async function save() {
    if (!title.trim()) { toast.error("A task needs a title."); return; }
    setSaving(true);
    try {
      if (activeState.mode === "create") await apiClient.createTask({ title: title.trim(), description: description.trim(), dueDate, priority, status: activeState.status });
      else if (activeState.task) await apiClient.updateTask(activeState.task.id, { title: title.trim(), description: description.trim(), dueDate, priority });
      toast.success(activeState.mode === "create" ? "Task added." : "Task updated.");
      await onSaved();
    } catch (error) { toast.error(error instanceof Error ? error.message : "Could not save that task."); }
    finally { setSaving(false); }
  }
  async function remove() {
    if (!activeState.task || !window.confirm(`Delete “${activeState.task.title}”?`)) return;
    setSaving(true);
    try {
      await apiClient.deleteTask(activeState.task.id);
      toast.success("Task deleted.");
      await onSaved();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Could not delete that task.");
    } finally {
      setSaving(false);
    }
  }
  return <Dialog open={Boolean(state)} onOpenChange={onOpenChange}><DialogContent className="border-border bg-card sm:max-w-lg"><DialogHeader><DialogTitle className="font-display text-xl">{state.mode === "create" ? "Add task" : "Edit task"}</DialogTitle><DialogDescription>{state.mode === "create" ? `New task in ${labelForStatus(state.status)}.` : `${labelForStatus(state.status)} · edit the details below.`}</DialogDescription></DialogHeader><div className="flex flex-col gap-4"><Field label="Title"><Input autoFocus value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Name the next thing" /></Field><Field label="Description"><Textarea value={description} onChange={(event) => setDescription(event.target.value)} placeholder="Optional notes" rows={4} /></Field><div className="grid gap-4 sm:grid-cols-2"><Field label="Due date"><div className="relative"><CalendarDays className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" /><Input type="date" value={dueDate} onChange={(event) => setDueDate(event.target.value)} className="pl-9" /></div></Field><Field label="Priority"><div className="grid grid-cols-3 gap-1 rounded-md border border-input bg-background p-1">{priorities.map((value) => <Button key={value} type="button" variant={priority === value ? "secondary" : "ghost"} size="sm" className={`h-8 capitalize ${priority === value ? "ring-1 ring-primary/30" : "text-muted-foreground"}`} onClick={() => setPriority(value)}>{value}</Button>)}</div></Field></div></div><DialogFooter className="mt-2 flex-row items-center justify-between sm:justify-between"><div>{state.mode === "edit" && <Button type="button" variant="ghost" className="px-0 text-destructive hover:text-destructive" onClick={remove} disabled={saving}><Trash2 /> Delete</Button>}</div><div className="flex gap-2"><Button type="button" variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button><Button type="button" onClick={save} disabled={saving}>{saving ? "Saving…" : "Save changes"}</Button></div></DialogFooter></DialogContent></Dialog>;
}

function AuthScreen({ mode, onModeChange, onSignedIn }: { mode: "login" | "register"; onModeChange: (mode: "login" | "register") => void; onSignedIn: (user: { id: string; email: string }) => void }) {
  const [email, setEmail] = useState("ada@example.com");
  const [password, setPassword] = useState("focus");
  const [busy, setBusy] = useState(false);
  async function submit(event: React.FormEvent) {
    event.preventDefault(); setBusy(true);
    try { const user = mode === "login" ? await apiClient.signIn(email, password) : await apiClient.register(email, password); onSignedIn(user); toast.success(mode === "login" ? "Welcome back." : "Your board is ready."); }
    catch (error) { toast.error(error instanceof Error ? error.message : "Could not sign you in."); }
    finally { setBusy(false); }
  }
  return <main className="flex min-h-screen items-center justify-center bg-background px-5 py-10"><div className="w-full max-w-md"><div className="mb-8 flex items-center gap-3"><div className="grid size-9 place-items-center rounded-md bg-primary font-display text-lg font-bold text-primary-foreground">K</div><span className="font-display text-sm font-semibold uppercase tracking-[0.2em]">Korda</span></div><div className="rounded-xl border border-border bg-card p-6 shadow-sm sm:p-8"><p className="text-xs font-semibold uppercase tracking-[0.25em] text-muted-foreground">Personal board</p><h1 className="mt-3 font-display text-4xl font-bold tracking-tight">{mode === "login" ? "Back to focus." : "Start with a blank board."}</h1><p className="mt-3 text-sm leading-relaxed text-muted-foreground">{mode === "login" ? "Sign in to pick up where you left off." : "Create a simple space for the work in front of you."}</p><form onSubmit={submit} className="mt-7 flex flex-col gap-4"><Field label="Email"><Input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required /></Field><Field label="Password"><Input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required minLength={4} /></Field><Button type="submit" className="mt-2 w-full" disabled={busy}>{busy ? "Loading…" : mode === "login" ? "Sign in" : "Create account"}</Button></form><div className="mt-6 border-t border-border pt-5 text-center text-sm text-muted-foreground">{mode === "login" ? "New here?" : "Already have an account?"} <Button variant="link" type="button" className="h-auto p-0" onClick={() => onModeChange(mode === "login" ? "register" : "login")}>{mode === "login" ? "Create an account" : "Sign in instead"}</Button></div><p className="mt-5 text-center text-xs text-muted-foreground">FastAPI backend authentication</p></div></div></main>;
}

function Field({ label, children }: { label: string; children: React.ReactNode }) { return <label className="block"><span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-muted-foreground">{label}</span>{children}</label>; }
function LoadingScreen() { return <main className="grid min-h-screen place-items-center bg-background text-sm text-muted-foreground">Loading your board…</main>; }
function PriorityBadge({ priority }: { priority: Priority }) { return <span className={`shrink-0 rounded border px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${priority === "high" ? "border-primary/40 text-primary" : priority === "medium" ? "border-border text-muted-foreground" : "border-border text-muted-foreground/80"}`}>{priority === "medium" ? "Med" : priority}</span>; }
function FilterSelect<T extends string>({ value, onChange, options, label }: { value: T; onChange: (value: T) => void; options: T[]; label: string }) { return <div className="relative"><select aria-label={`${label} filter`} value={value} onChange={(event) => onChange(event.target.value as T)} className="h-9 appearance-none rounded-full border border-border bg-card py-1.5 pl-3 pr-8 text-xs font-semibold text-foreground outline-none transition focus:ring-2 focus:ring-primary/30">{options.map((option) => <option key={option} value={option}>{option === "all" ? `${label} · All` : option.charAt(0).toUpperCase() + option.slice(1)}</option>)}</select><ChevronDown className="pointer-events-none absolute right-2.5 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" /></div>; }
type DueFilter = "all" | "overdue" | "today" | "upcoming" | "none";
function getDueState(date: string): DueFilter {
  if (!date) return "none";
  try {
    const today = new Date();
    const dateStr = date.includes("T") ? date.slice(0, 10) : date;
    const due = new Date(`${dateStr}T00:00:00`);
    const now = new Date(`${today.toISOString().slice(0, 10)}T00:00:00`);
    if (isNaN(due.getTime()) || isNaN(now.getTime())) return "none";
    if (due < now) return "overdue";
    if (due.getTime() === now.getTime()) return "today";
    return "upcoming";
  } catch {
    return "none";
  }
}
function dueLabel(task: Task, state: DueFilter) {
  if (task.status === "done") {
    const formatted = task.completedAt ? formatDate(task.completedAt) : "";
    return formatted ? `✓ Done ${formatted}` : "✓ Done";
  }
  if (state === "overdue") return "Overdue";
  if (state === "today") return "Due today";
  return task.dueDate ? "Upcoming" : "No date";
}
function formatDate(date: string): string {
  if (!date) return "";
  try {
    const cleanDate = date.includes("T") ? date : `${date}T00:00:00`;
    const parsed = new Date(cleanDate);
    if (isNaN(parsed.getTime())) {
      const direct = new Date(date);
      if (isNaN(direct.getTime())) return date;
      return new Intl.DateTimeFormat("en", { month: "short", day: "numeric" }).format(direct);
    }
    return new Intl.DateTimeFormat("en", { month: "short", day: "numeric" }).format(parsed);
  } catch {
    return date;
  }
}
function labelForStatus(status: TaskStatus) { return columns.find((column) => column.id === status)?.label ?? status; }
function initials(email: string) { return (email.split("@")[0] ?? "").slice(0, 2).toUpperCase(); }