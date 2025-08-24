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

    # Top nav with Back and Refresh
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
        padx=10,
        pady=4,
    ).pack(side=LEFT)
    refresh_btn_container = Frame(nav_frame, bg="#f8f9fc")
    refresh_btn_container.pack(side=RIGHT)

    # Main split container (form left, table right)
    main_container = Frame(parent_frame, bg="#f8f9fc")
    main_container.pack(fill=BOTH, expand=True, padx=20, pady=10)
    main_container.grid_columnconfigure(0, weight=0)
    main_container.grid_columnconfigure(1, weight=1)
    main_container.grid_rowconfigure(0, weight=1)

    # Form container (left)
    form_container = Frame(main_container, bg="#ffffff", relief="raised", bd=2)
    form_container.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

    Label(
        form_container,
        text="📝 Task Details",
        font=("Segoe UI", 16, "bold"),
        bg="#ffffff",
        fg="#2c3e50",
    ).pack(pady=10)

    form_frame = Frame(form_container, bg="#ffffff")
    form_frame.pack(pady=10, padx=16, fill=X)

    # Fields
    Label(form_frame, text="Task Title:", font=("Segoe UI", 12, "bold"), bg="#ffffff", fg="#2c3e50").grid(row=0, column=0, sticky=W, pady=(0, 6))
    title_entry = ttk.Entry(form_frame, font=("Segoe UI", 11), width=28)
    title_entry.grid(row=0, column=1, padx=10, pady=(0, 6), sticky=W)

    Label(form_frame, text="Description:", font=("Segoe UI", 12, "bold"), bg="#ffffff", fg="#2c3e50").grid(row=1, column=0, sticky=NW, pady=(0, 6))
    desc_text = Text(form_frame, width=28, height=6, font=("Segoe UI", 11), relief="solid", bd=1)
    desc_text.grid(row=1, column=1, padx=10, pady=(0, 6), sticky=W)
    desc_scroll = ttk.Scrollbar(form_frame, orient=VERTICAL, command=desc_text.yview)
    desc_text.configure(yscrollcommand=desc_scroll.set)
    desc_scroll.grid(row=1, column=2, sticky="nsw", pady=(0, 6))

    Label(form_frame, text="Priority:", font=("Segoe UI", 12, "bold"), bg="#ffffff", fg="#2c3e50").grid(row=2, column=0, sticky=W, pady=(0, 6))
    priority_var = StringVar(value="Medium")
    priority_combo = ttk.Combobox(form_frame, textvariable=priority_var, values=("Low", "Medium", "High"), state="readonly", width=26)
    priority_combo.grid(row=2, column=1, padx=10, pady=(0, 6), sticky=W)

    Label(form_frame, text="Status:", font=("Segoe UI", 12, "bold"), bg="#ffffff", fg="#2c3e50").grid(row=3, column=0, sticky=W, pady=(0, 6))
    status_var = StringVar(value="Pending")
    status_combo = ttk.Combobox(form_frame, textvariable=status_var, values=("Pending", "In Progress", "Completed"), state="readonly", width=26)
    status_combo.grid(row=3, column=1, padx=10, pady=(0, 6), sticky=W)

    # Validation/info label
    info_var = StringVar(value="")
    info_label = Label(form_container, textvariable=info_var, font=("Segoe UI", 10), bg="#ffffff", fg="#7f8c8d")
    info_label.pack(pady=(0, 6), padx=12, anchor=W)

    selected_task_id = StringVar()

    def clear_form():
        title_entry.delete(0, END)
        desc_text.delete("1.0", END)
        priority_var.set("Medium")
        status_var.set("Pending")
        selected_task_id.set("")
        info_var.set("")

    all_rows = []  # cache for filtering/sorting

    def render_rows(rows):
        for row in task_table.get_children():
            task_table.delete(row)
        for i, r in enumerate(rows):
            tag = "even" if i % 2 == 0 else "odd"
            task_table.insert("", END, values=r, tags=(tag,))

    def apply_filter(*_):
        q = search_var.get().strip().lower()
        f_status = filter_status_var.get()
        f_priority = filter_priority_var.get()
        rows = all_rows
        if f_status and f_status != "All":
            rows = [r for r in rows if (r[4] or "").lower() == f_status.lower()]
        if f_priority and f_priority != "All":
            rows = [r for r in rows if (r[3] or "").lower() == f_priority.lower()]
        if q:
            rows = [r for r in rows if q in str(r[1]).lower() or q in str(r[2]).lower()]
        render_rows(rows)

    def refresh_table():
        nonlocal all_rows
        all_rows = []
        db = connect_db()
        if not db:
            info_var.set("Database connection failed.")
            render_rows([])
            return
        cursor = db.cursor()
        try:
            cursor.execute("SELECT id, title, description, priority, status FROM tasks")
            all_rows = cursor.fetchall()
        except Exception as e:
            info_var.set(f"Error loading tasks: {e}")
        finally:
            try:
                cursor.close()
            except Exception:
                pass
            try:
                db.close()
            except Exception:
                pass
        apply_filter()

    def save_task():
        title = title_entry.get()
        desc = desc_text.get("1.0", "end-1c").strip()
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
            desc_text.delete("1.0", END)
            desc_text.insert("1.0", values[2])
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
    button_frame.pack(pady=10)

    ttk.Button(button_frame, text="💾 Save", command=save_task).grid(row=0, column=0, padx=6)
    ttk.Button(button_frame, text="♻️ Clear", command=clear_form).grid(row=0, column=1, padx=6)
    ttk.Button(button_frame, text="🗑️ Delete", command=delete_task).grid(row=0, column=2, padx=6)
    ttk.Button(refresh_btn_container, text="🔄 Refresh", command=lambda: [clear_form(), refresh_table()]).pack(side=RIGHT)

    # Table (right)
    table_container = Frame(main_container, bg="#ffffff", relief="raised", bd=2)
    table_container.grid(row=0, column=1, sticky="nsew")

    Label(
        table_container,
        text="� Your Tasks Overview",
        font=("Segoe UI", 16, "bold"),
        bg="#ffffff",
        fg="#2c3e50",
    ).pack(pady=10)

    # Filters row
    filter_bar = Frame(table_container, bg="#ffffff")
    filter_bar.pack(fill=X, padx=16)
    Label(filter_bar, text="Search:", bg="#ffffff").pack(side=LEFT)
    search_var = StringVar()
    search_entry = ttk.Entry(filter_bar, textvariable=search_var, width=24)
    search_entry.pack(side=LEFT, padx=(6, 16))
    Label(filter_bar, text="Priority:", bg="#ffffff").pack(side=LEFT)
    filter_priority_var = StringVar(value="All")
    filter_priority = ttk.Combobox(filter_bar, textvariable=filter_priority_var, values=("All", "High", "Medium", "Low"), state="readonly", width=10)
    filter_priority.pack(side=LEFT, padx=(6, 16))
    Label(filter_bar, text="Status:", bg="#ffffff").pack(side=LEFT)
    filter_status_var = StringVar(value="All")
    filter_status = ttk.Combobox(filter_bar, textvariable=filter_status_var, values=("All", "Pending", "In Progress", "Completed"), state="readonly", width=12)
    filter_status.pack(side=LEFT, padx=(6, 0))

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

    # Scrollbars
    yscroll = ttk.Scrollbar(table_container, orient=VERTICAL, command=task_table.yview)
    xscroll = ttk.Scrollbar(table_container, orient=HORIZONTAL, command=task_table.xview)
    task_table.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)

    task_table.pack(fill=BOTH, expand=True, padx=16, pady=(8, 0))
    yscroll.pack(side=RIGHT, fill=Y)
    xscroll.pack(side=BOTTOM, fill=X)

    # Row styling
    task_table.tag_configure("even", background="#f9fbfd")
    task_table.tag_configure("odd", background="#ffffff")

    # Sorting support
    sort_state = {"ID": False, "Title": False, "Description": False, "Priority": False, "Status": False}

    def sort_by(column, reverse=False):
        key_index = {"ID": 0, "Title": 1, "Description": 2, "Priority": 3, "Status": 4}[column]
        rows = list(task_table.get_children())
        data = [(task_table.set(k, column), k) for k in rows]
        if column == "ID":
            data.sort(key=lambda t: int(t[0]) if str(t[0]).isdigit() else 0, reverse=reverse)
        else:
            data.sort(key=lambda t: str(t[0]).lower(), reverse=reverse)
        for index, (val, k) in enumerate(data):
            task_table.move(k, "", index)
            task_table.item(k, tags=("even" if index % 2 == 0 else "odd",))
        sort_state[column] = reverse

    for col in ("ID", "Title", "Description", "Priority", "Status"):
        task_table.heading(col, text=task_table.heading(col, option="text"), command=lambda c=col: sort_by(c, not sort_state[c]))

    # Bindings
    task_table.bind("<ButtonRelease-1>", on_row_select)
    task_table.bind("<Double-1>", on_row_select)
    parent_frame.bind_all("<Control-s>", lambda e: save_task())
    parent_frame.bind_all("<Escape>", lambda e: clear_form())
    search_var.trace_add("write", apply_filter)
    filter_status_var.trace_add("write", apply_filter)
    filter_priority_var.trace_add("write", apply_filter)

    refresh_table()
