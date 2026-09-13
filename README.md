# My Simple Board

I want to build a mini Kanban board for personal use. For this project, build the front end with backend in mind, build with a mock backend, mock the calls to the backend. This is the specification: 




# Mini Personal Kanban — Specification




## 1. Product Overview




A simple, personal Kanban board for managing tasks visually.




The application has **one Kanban board per user** with four fixed columns:




1. **Ideas**

2. **To Do**

3. **In Progress**

4. **Done**




The goal is to keep task management lightweight—no teams, comments, complex project management, or enterprise features.




---




## 2. Authentication & Users




* Users can **register and log in**.

* Each authenticated user has their own personal board.

* A user can have **one board only**.

* Users can log out.

* Basic authentication is sufficient; no social login or complex account-management features are required.




---




## 3. Tasks




Each task contains:




| Field           | Description                          |

| --------------- | ------------------------------------ |

| Title           | Required task name                   |

| Description     | Optional additional information      |

| Due date        | Date the task should be completed    |

| Priority        | High, Medium, or Low                 |

| Status          | Ideas, To Do, In Progress, or Done   |

| Position        | Determines its order within a column |

| Completed state | Determined by whether it is in Done  |




Tasks are created through an **Add Task** action at the bottom of each column.




When creating a task from a column, it is automatically assigned to that column.




---




## 4. Task Editing




Clicking a task opens an **edit modal**.




The modal allows the user to:




* Change title

* Change description

* Change due date

* Change priority

* Delete the task




Deleting requires a **confirmation prompt**.




---




## 5. Drag & Drop




Tasks support drag-and-drop.




The user can:




* Move tasks between columns.

* Reorder tasks within a column.

* Move tasks backward or forward freely.




For example:




> Ideas → To Do → In Progress → Done




But the user can also move:




> In Progress → To Do




if they decide a task needs more preparation.




### Done behavior




Moving a task into **Done** marks it completed.




Moving it out of **Done** marks it incomplete again.




---




## 6. Priority




Each task has one of three priorities:




* **High**

* **Medium**

* **Low**




Priority is displayed on the task card.




Priority **does not automatically determine the task's position**.




The user controls the actual order by dragging cards.




This gives the user both:




> **Priority = how important the task is**




and




> **Position = the order I personally want to tackle it**




---




## 7. Due Dates




Due dates are displayed on task cards.




The interface provides simple visual status indicators:




* **Overdue** — due date has passed

* **Due today** — due today

* **Upcoming** — due date is in the future




There is no automatic movement of tasks based on their due date.




---




## 8. Search & Filtering




The board provides simple search and filtering.




### Search




Searches through:




* Task title

* Task description




### Filters




Users can filter by:




* Priority

* Due-date status




Filtering is purely visual. It doesn't modify task status or ordering.




---




## 9. Completed Tasks




Completed tasks remain in **Done** until manually removed.




A **Clear Completed** action allows the user to remove completed tasks.




The action should include a confirmation because it is destructive.




---




## 10. Board Layout




The interface is **responsive**.




### Desktop




The four columns appear side-by-side:




**Ideas | To Do | In Progress | Done**




### Smaller screens




The board adapts to the available screen size while preserving the Kanban interaction. Horizontal scrolling is acceptable where necessary rather than forcing an awkward compressed four-column layout.




---




## 11. Data Persistence




The application is **database-backed**.




Tasks and their associated board/user information persist between sessions.




The application does not rely on browser `localStorage` as its primary source of truth.




---




# 12. Remaining Decisions — Simplified Defaults




For the decisions we didn't explicitly discuss, I'll choose the simplest functional behavior.




### Task ordering




Each task has a persistent position/order value within its column.




Dragging a card updates that order.




### Default task priority




New tasks default to **Medium** priority.




### Default task position




A newly created task is placed at the **bottom of its selected column**.




### Default status




The status is determined by the column in which the task currently resides.




### Empty columns




Empty columns display a simple message such as:




> No tasks yet




and retain their **Add Task** action.




### Deleting




Deleted tasks are permanently removed after confirmation. No complicated trash/recovery system.




### Clear Completed




Clears completed tasks from **Done** after confirmation.




### Board naming




There is no board-name management. The application simply has the user's personal Kanban board.




### Notifications




No push notifications, email reminders, or notification system.




### Attachments




No file attachments.




### Comments




No comments.




### Subtasks




No subtasks.




### Labels/tags




No user-defined tags. **Priority** is the only task classification mechanism.




### Recurring tasks




Not supported.




### Activity history




Not supported.




### Collaboration




Not supported.




### Sharing




Not supported.




### Multiple boards/projects




Not supported.




---




# 13. Core User Flow




The primary experience should be:




**Login → Board → Create task → Organize → Work → Complete**




For example:




1. User logs in.

2. They add an idea under **Ideas**.

3. They later drag it into **To Do**.

4. They prioritize it as **High**.

5. They position it above other To Do tasks.

6. They drag it into **In Progress** when they start working.

7. They eventually drag it into **Done**.

8. They periodically use **Clear Completed** to clean up the board.




That's essentially the entire product loop.




---




# 14. Deliberately Out of Scope




To protect the "mini personal Kanban" concept, the first version should **not** include:




* Multiple boards

* Teams

* Team members

* Comments

* Chat

* File attachments

* Subtasks

* Custom workflows

* Custom columns

* Recurring tasks

* Notifications

* Calendar integration

* Time tracking

* Reporting/analytics

* Activity feeds

* Public sharing

* Third-party integrations

* Complex permissions

* Custom labels

* AI features




The guiding principle is:




> **If it doesn't directly help one person create, prioritize, organize, work on, and complete a task, it probably doesn't belong in the MVP.**

This project was built with [Lovable](https://lovable.dev).

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/e6432f5a-7c29-4809-8d6a-b39d46e5a60c).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```
