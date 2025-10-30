from tkinter import *
from tkinter import messagebox, ttk
from datetime import datetime

try:
    from tkcalendar import DateEntry
    _TKCALENDAR_AVAILABLE = True
except ImportError:
    _TKCALENDAR_AVAILABLE = False


def _clear_frame(frame: Frame):
    for widget in frame.winfo_children():
        widget.destroy()

def show_goals(parent_frame: Frame, connect_db, go_back):
    _clear_frame(parent_frame)

    header_frame = Frame(parent_frame, bg="#8e44ad", height=70)
    header_frame.pack(fill=X, pady=(0, 20))
    header_frame.pack_propagate(False)

    Label(
        header_frame,
        text="🎯 Goal Achievement System",
        font=("Segoe UI", 24, "bold"),
        bg="#8e44ad",
        fg="#ffffff",
    ).pack(pady=15)

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

    main_container = Frame(parent_frame, bg="#f8f9fc")
    main_container.pack(fill=BOTH, expand=True, padx=20, pady=10)
    main_container.grid_columnconfigure(0, weight=0)
    main_container.grid_columnconfigure(1, weight=1)
    main_container.grid_rowconfigure(0, weight=1)

    form_container = Frame(main_container, bg="#ffffff", relief="raised", bd=2)
    form_container.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

    Label(
        form_container,
        text="🎯 Goal Details",
        font=("Segoe UI", 16, "bold"),
        bg="#ffffff",
        fg="#2c3e50",
    ).pack(pady=10)

    form_frame = Frame(form_container, bg="#ffffff")
    form_frame.pack(pady=10, padx=16, fill=X)

    Label(form_frame, text="Goal Title:", font=("Segoe UI", 12, "bold"), bg="#ffffff", fg="#2c3e50").grid(row=0, column=0, sticky=W, pady=(0, 6))
    title_entry = ttk.Entry(form_frame, font=("Segoe UI", 11), width=28)
    title_entry.grid(row=0, column=1, padx=10, pady=(0, 6), sticky=W)

    Label(form_frame, text="Description:", font=("Segoe UI", 12, "bold"), bg="#ffffff", fg="#2c3e50").grid(row=1, column=0, sticky=NW, pady=(0, 6))
    desc_text = Text(form_frame, width=28, height=4, font=("Segoe UI", 11), relief="solid", bd=1)
    desc_text.grid(row=1, column=1, padx=10, pady=(0, 6), sticky=W)
    desc_scroll = ttk.Scrollbar(form_frame, orient=VERTICAL, command=desc_text.yview)
    desc_text.configure(yscrollcommand=desc_scroll.set)
    desc_scroll.grid(row=1, column=2, sticky="nsw", pady=(0, 6))

    Label(form_frame, text="Target Date:", font=("Segoe UI", 12, "bold"), bg="#ffffff", fg="#2c3e50").grid(row=2, column=0, sticky=W, pady=(0, 6))
    if _TKCALENDAR_AVAILABLE:
        date_entry = DateEntry(form_frame, width=26, background='darkblue', foreground='white', borderwidth=2, date_pattern='y-mm-dd', font=("Segoe UI", 11))
    else:
        date_entry = ttk.Entry(form_frame, font=("Segoe UI", 11), width=28)
        try:
            date_entry.insert(0, datetime.today().strftime('%Y-%m-%d'))
        except Exception:
            pass
    date_entry.grid(row=2, column=1, padx=10, pady=(0, 6), sticky=W)

    Label(form_frame, text="Status:", font=("Segoe UI", 12, "bold"), bg="#ffffff", fg="#2c3e50").grid(row=3, column=0, sticky=W, pady=(0, 6))
    status_var = StringVar(value="Not Started")
    status_combo = ttk.Combobox(form_frame, textvariable=status_var, values=("Not Started", "In Progress", "Achieved"), state="readonly", width=26)
    status_combo.grid(row=3, column=1, padx=10, pady=(0, 6), sticky=W)

    info_var = StringVar(value="")
    info_label = Label(form_container, textvariable=info_var, font=("Segoe UI", 10), bg="#ffffff", fg="#7f8c8d")
    info_label.pack(pady=(0, 6), padx=12, anchor=W)

    selected_goal_id = StringVar()

    def clear_form():
        selected_goal_id.set("")
        title_entry.delete(0, END)
        desc_text.delete("1.0", END)
        date_entry.delete(0, END)
        try:
            date_entry.insert(0, datetime.today().strftime('%Y-%m-%d'))
        except:
            pass
        status_var.set("Not Started")
        info_var.set("")

    all_rows = []

    def render_rows(rows):
        for i in tree.get_children():
            tree.delete(i)
        for row in rows:
            tree.insert("", "end", values=row)

    def apply_filter(*_):
        query = search_var.get().lower()
        if not query:
            render_rows(all_rows)
            return
        filtered_rows = [row for row in all_rows if query in str(row[1]).lower()]
        render_rows(filtered_rows)

    def refresh_table():
        conn = connect_db()
        if not conn:
            messagebox.showerror("Database Error", "Could not connect to the database.")
            return
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, title, target_date, status, progress FROM goals ORDER BY created_at DESC")
            rows = cursor.fetchall()
            all_rows[:] = rows
            render_rows(rows)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch goals: {e}")
        finally:
            if conn:
                conn.close()

    def save_goal():
        title = title_entry.get().strip()
        description = desc_text.get("1.0", END).strip()
        target_date = date_entry.get().strip()
        status = status_var.get()
        goal_id = selected_goal_id.get()

        if not title or not target_date:
            messagebox.showwarning("Validation Error", "Title and Target Date are required.")
            return

        conn = connect_db()
        if not conn:
            messagebox.showerror("Database Error", "Could not connect to the database.")
            return
        try:
            cursor = conn.cursor()
            if goal_id:
                cursor.execute(
                    "UPDATE goals SET title=%s, description=%s, target_date=%s, status=%s WHERE id=%s",
                    (title, description, target_date, status, goal_id)
                )
            else:
                cursor.execute(
                    "INSERT INTO goals (title, description, target_date, status) VALUES (%s, %s, %s, %s)",
                    (title, description, target_date, status)
                )
            conn.commit()
            info_var.set("Goal saved successfully!")
            clear_form()
            refresh_table()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save goal: {e}")
        finally:
            if conn:
                conn.close()

    def on_row_select(event):
        selected_item = tree.focus()
        if not selected_item:
            return
        
        item_values = tree.item(selected_item, "values")
        goal_id = item_values[0]
        
        conn = connect_db()
        if not conn: return
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM goals WHERE id = %s", (goal_id,))
            goal = cursor.fetchone()
            if goal:
                clear_form()
                selected_goal_id.set(goal['id'])
                title_entry.insert(0, goal['title'])
                desc_text.insert("1.0", goal['description'] or "")
                date_entry.insert(0, goal['target_date'].strftime('%Y-%m-%d'))
                status_var.set(goal['status'])
        except Exception as e:
            messagebox.showerror("Error", f"Could not fetch goal details: {e}")
        finally:
            if conn: conn.close()

    def delete_goal():
        goal_id = selected_goal_id.get()
        if not goal_id:
            messagebox.showwarning("Selection Error", "Please select a goal to delete.")
            return
        
        if not messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this goal?"):
            return

        conn = connect_db()
        if not conn: return
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM goals WHERE id = %s", (goal_id,))
            conn.commit()
            messagebox.showinfo("Success", "Goal deleted successfully.")
            clear_form()
            refresh_table()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete goal: {e}")
        finally:
            if conn: conn.close()

    button_frame = Frame(form_container, bg="#ffffff")
    button_frame.pack(pady=10)

    ttk.Button(button_frame, text="💾 Save", command=save_goal).grid(row=0, column=0, padx=6)
    ttk.Button(button_frame, text="♻️ Clear", command=clear_form).grid(row=0, column=1, padx=6)
    ttk.Button(button_frame, text="🗑️ Delete", command=delete_goal).grid(row=0, column=2, padx=6)
    ttk.Button(refresh_btn_container, text="🔄 Refresh", command=lambda: [clear_form(), refresh_table()]).pack(side=RIGHT)

    table_container = Frame(main_container, bg="#ffffff", relief="raised", bd=2)
    table_container.grid(row=0, column=1, sticky="nsew")

    Label(
        table_container,
        text="📊 Your Goals Overview",
        font=("Segoe UI", 16, "bold"),
        bg="#ffffff",
        fg="#2c3e50",
    ).pack(pady=10)

    filter_bar = Frame(table_container, bg="#ffffff")
    filter_bar.pack(fill=X, padx=16)
    Label(filter_bar, text="Search:", bg="#ffffff").pack(side=LEFT)
    search_var = StringVar()
    search_entry = ttk.Entry(filter_bar, textvariable=search_var, width=24)
    search_entry.pack(side=LEFT, padx=(6, 16))
    search_var.trace_add("write", apply_filter)

    tree_frame = Frame(table_container, bg="#ffffff")
    tree_frame.pack(expand=True, fill=BOTH, padx=16, pady=10)
    
    columns = ("id", "title", "target_date", "status", "progress")
    tree = ttk.Treeview(tree_frame, columns=columns, show="headings", style="Custom.Treeview")
    
    tree.heading("id", text="ID")
    tree.heading("title", text="Title")
    tree.heading("target_date", text="Target Date")
    tree.heading("status", text="Status")
    tree.heading("progress", text="Progress (%)")

    tree.column("id", width=40, anchor=CENTER)
    tree.column("title", width=200)
    tree.column("target_date", width=100, anchor=CENTER)
    tree.column("status", width=100, anchor=CENTER)
    tree.column("progress", width=80, anchor=CENTER)

    vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    vsb.pack(side=RIGHT, fill=Y)
    tree.pack(expand=True, fill=BOTH)
    
    tree.bind("<<TreeviewSelect>>", on_row_select)

    refresh_table()
