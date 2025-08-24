from tkinter import *
from tkinter import messagebox, ttk


def _clear_frame(frame: Frame):
    for widget in frame.winfo_children():
        widget.destroy()


def show_tasks(parent_frame: Frame, connect_db, go_back):
    """Render the Task CRUD UI inside the given parent frame.

    Args:
        parent_frame: The container where the UI should be rendered.
        connect_db: Callable returning a DB connection.
        go_back: Callback to navigate back to the dashboard.
    """
    _clear_frame(parent_frame)

    # Header
    header_frame = Frame(parent_frame, bg="#27ae60", height=70)
    header_frame.pack(fill=X, pady=(0, 20))
    header_frame.pack_propagate(False)

    Label(
        header_frame,
        text="✅ Task Management System",
        font=("Segoe UI", 24, "bold"),
        bg="#27ae60",
        fg="#ffffff",
    ).pack(pady=15)

    # Back button
    nav_frame = Frame(parent_frame, bg="#f8f9fc")
    nav_frame.pack(fill=X, padx=20, pady=(0, 10))
    Button(
        nav_frame,
        text="🏠 Back to Dashboard",
        command=go_back,
        bg="#34495e",
        fg="white",
        font=("Segoe UI", 10),
        relief="flat",
    ).pack(side=LEFT)

    # Form container
    form_container = Frame(parent_frame, bg="#ffffff", relief="raised", bd=2)
    form_container.pack(fill=X, padx=20, pady=10)

    Label(
        form_container,
        text="📝 Task Information",
        font=("Segoe UI", 16, "bold"),
        bg="#ffffff",
        fg="#2c3e50",
    ).pack(pady=10)

    form_frame = Frame(form_container, bg="#ffffff")
    form_frame.pack(pady=10, padx=20)

    # Fields
    Label(
        form_frame,
        text="Task Title:",
        font=("Segoe UI", 12, "bold"),
        bg="#ffffff",
        fg="#2c3e50",
    ).grid(row=0, column=0, sticky=W, pady=5)
    title_entry = Entry(form_frame, font=("Segoe UI", 12), width=25, relief="solid", bd=1)
    title_entry.grid(row=0, column=1, padx=10, pady=5, ipady=3)

    Label(
        form_frame,
        text="Description:",
        font=("Segoe UI", 12, "bold"),
        bg="#ffffff",
        fg="#2c3e50",
    ).grid(row=1, column=0, sticky=W, pady=5)
    desc_entry = Entry(form_frame, font=("Segoe UI", 12), width=25, relief="solid", bd=1)
    desc_entry.grid(row=1, column=1, padx=10, pady=5, ipady=3)

    Label(
        form_frame,
        text="Priority Level:",
        font=("Segoe UI", 12, "bold"),
        bg="#ffffff",
        fg="#2c3e50",
    ).grid(row=2, column=0, sticky=W, pady=5)
    priority_var = StringVar()
    priority_menu = OptionMenu(form_frame, priority_var, "Low", "Medium", "High")
    priority_menu.configure(font=("Segoe UI", 11), bg="#ecf0f1", relief="solid")
    priority_var.set("Medium")
    priority_menu.grid(row=2, column=1, padx=10, pady=5, sticky=W)

    Label(
        form_frame,
        text="Task Status:",
        font=("Segoe UI", 12, "bold"),
        bg="#ffffff",
        fg="#2c3e50",
    ).grid(row=3, column=0, sticky=W, pady=5)
    status_var = StringVar()
    status_menu = OptionMenu(form_frame, status_var, "Pending", "In Progress", "Completed")
    status_menu.configure(font=("Segoe UI", 11), bg="#ecf0f1", relief="solid")
    status_var.set("Pending")
    status_menu.grid(row=3, column=1, padx=10, pady=5, sticky=W)

    selected_task_id = StringVar()

    def clear_form():
        title_entry.delete(0, END)
        desc_entry.delete(0, END)
        priority_var.set("Medium")
        status_var.set("Pending")
        selected_task_id.set("")

    def refresh_table():
        for row in task_table.get_children():
            task_table.delete(row)

        db = connect_db()
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT id, title, description, priority, status FROM tasks")
            for row in cursor.fetchall():
                task_table.insert("", END, values=row)
            try:
                cursor.close()
            except Exception:
                pass
            try:
                db.close()
            except Exception:
                pass

    def save_task():
        title = title_entry.get()
        desc = desc_entry.get()
        priority = priority_var.get()
        status = status_var.get()

        if not title:
            messagebox.showwarning("Validation Error", "⚠️ Task title is required.")
            return

        db = connect_db()
        if db:
            cursor = db.cursor()
            try:
                if selected_task_id.get():
                    cursor.execute(
                        "UPDATE tasks SET title=%s, description=%s, priority=%s, status=%s WHERE id=%s",
                        (title, desc, priority, status, selected_task_id.get()),
                    )
                    messagebox.showinfo("Success", "✅ Task updated successfully!")
                else:
                    cursor.execute(
                        "INSERT INTO tasks (title, description, priority, status) VALUES (%s, %s, %s, %s)",
                        (title, desc, priority, status),
                    )
                    messagebox.showinfo("Success", "✅ Task added successfully!")
                db.commit()
                clear_form()
                refresh_table()
            except Exception as e:
                messagebox.showerror("Database Error", f"❌ Error: {str(e)}")
            finally:
                try:
                    cursor.close()
                except Exception:
                    pass
                try:
                    db.close()
                except Exception:
                    pass

    def on_row_select(event):
        selected = task_table.focus()
        if selected:
            values = task_table.item(selected, "values")
            selected_task_id.set(values[0])
            title_entry.delete(0, END)
            title_entry.insert(0, values[1])
            desc_entry.delete(0, END)
            desc_entry.insert(0, values[2])
            priority_var.set(values[3])
            status_var.set(values[4])

    def delete_task():
        if not selected_task_id.get():
            messagebox.showwarning("Delete Task", "⚠️ Please select a task to delete.")
            return

        confirm = messagebox.askyesno(
            "Delete Task", "🗑️ Are you sure you want to delete this task?"
        )
        if confirm:
            db = connect_db()
            if db:
                cursor = db.cursor()
                try:
                    cursor.execute("DELETE FROM tasks WHERE id=%s", (selected_task_id.get(),))
                    db.commit()
                    clear_form()
                    refresh_table()
                    messagebox.showinfo("Deleted", "✅ Task deleted successfully!")
                except Exception as e:
                    messagebox.showerror("Database Error", f"❌ Error: {str(e)}")
                finally:
                    try:
                        cursor.close()
                    except Exception:
                        pass
                    try:
                        db.close()
                    except Exception:
                        pass

    # Buttons
    button_frame = Frame(form_container, bg="#ffffff")
    button_frame.pack(pady=15)

    Button(
        button_frame,
        text="💾 Save Task",
        command=save_task,
        bg="#27ae60",
        fg="white",
        font=("Segoe UI", 11, "bold"),
        relief="flat",
        padx=20,
        pady=8,
    ).grid(row=0, column=0, padx=8)
    Button(
        button_frame,
        text="♻️ Reset Form",
        command=clear_form,
        bg="#3498db",
        fg="white",
        font=("Segoe UI", 11, "bold"),
        relief="flat",
        padx=20,
        pady=8,
    ).grid(row=0, column=1, padx=8)
    Button(
        button_frame,
        text="🗑️ Delete Task",
        command=delete_task,
        bg="#e74c3c",
        fg="white",
        font=("Segoe UI", 11, "bold"),
        relief="flat",
        padx=20,
        pady=8,
    ).grid(row=0, column=2, padx=8)

    # Table
    table_container = Frame(parent_frame, bg="#ffffff", relief="raised", bd=2)
    table_container.pack(fill=BOTH, expand=True, padx=20, pady=10)

    Label(
        table_container,
        text="📊 Your Tasks Overview",
        font=("Segoe UI", 16, "bold"),
        bg="#ffffff",
        fg="#2c3e50",
    ).pack(pady=10)

    task_table = ttk.Treeview(
        table_container,
        columns=("ID", "Title", "Description", "Priority", "Status"),
        show="headings",
        style="Custom.Treeview",
    )

    task_table.heading("ID", text="🆔 ID")
    task_table.heading("Title", text="📝 Title")
    task_table.heading("Description", text="📋 Description")
    task_table.heading("Priority", text="⚡ Priority")
    task_table.heading("Status", text="📊 Status")

    task_table.column("ID", width=60, anchor=CENTER)
    task_table.column("Title", width=150, anchor=W)
    task_table.column("Description", width=200, anchor=W)
    task_table.column("Priority", width=100, anchor=CENTER)
    task_table.column("Status", width=120, anchor=CENTER)

    task_table.pack(fill=BOTH, expand=True, padx=20, pady=(0, 20))
    task_table.bind("<ButtonRelease-1>", on_row_select)

    refresh_table()
