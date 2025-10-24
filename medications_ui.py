from tkinter import *
from tkinter import messagebox, ttk
from datetime import datetime

def _clear_frame(frame: Frame):
    for widget in frame.winfo_children():
        widget.destroy()

def show_medications(parent_frame: Frame, connect_db, go_back):
    _clear_frame(parent_frame)

    header_frame = Frame(parent_frame, bg="#16a085", height=70)
    header_frame.pack(fill=X, pady=(0, 20))
    header_frame.pack_propagate(False)

    Label(
        header_frame,
        text="💊 Medication Reminder System",
        font=("Segoe UI", 24, "bold"),
        bg="#16a085",
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
        text="💊 Medication Details",
        font=("Segoe UI", 16, "bold"),
        bg="#ffffff",
        fg="#2c3e50",
    ).pack(pady=10)

    form_frame = Frame(form_container, bg="#ffffff")
    form_frame.pack(pady=10, padx=16, fill=X)

    Label(form_frame, text="Medication Name:", font=("Segoe UI", 12, "bold"), bg="#ffffff", fg="#2c3e50").grid(row=0, column=0, sticky=W, pady=(0, 6))
    name_entry = ttk.Entry(form_frame, font=("Segoe UI", 11), width=28)
    name_entry.grid(row=0, column=1, padx=10, pady=(0, 6), sticky=W)

    Label(form_frame, text="Dosage:", font=("Segoe UI", 12, "bold"), bg="#ffffff", fg="#2c3e50").grid(row=1, column=0, sticky=W, pady=(0, 6))
    dosage_entry = ttk.Entry(form_frame, font=("Segoe UI", 11), width=28)
    dosage_entry.grid(row=1, column=1, padx=10, pady=(0, 6), sticky=W)

    Label(form_frame, text="Schedule (Time):", font=("Segoe UI", 12, "bold"), bg="#ffffff", fg="#2c3e50").grid(row=2, column=0, sticky=W, pady=(0, 6))
    schedule_entry = ttk.Entry(form_frame, font=("Segoe UI", 11), width=28)
    schedule_entry.grid(row=2, column=1, padx=10, pady=(0, 6), sticky=W)

    Label(form_frame, text="Start Date:", font=("Segoe UI", 12, "bold"), bg="#ffffff", fg="#2c3e50").grid(row=3, column=0, sticky=W, pady=(0, 6))
    start_date_entry = ttk.Entry(form_frame, font=("Segoe UI", 11), width=28)
    start_date_entry.grid(row=3, column=1, padx=10, pady=(0, 6), sticky=W)
    try:
        start_date_entry.insert(0, datetime.today().strftime('%Y-%m-%d'))
    except:
        pass

    Label(form_frame, text="End Date:", font=("Segoe UI", 12, "bold"), bg="#ffffff", fg="#2c3e50").grid(row=4, column=0, sticky=W, pady=(0, 6))
    end_date_entry = ttk.Entry(form_frame, font=("Segoe UI", 11), width=28)
    end_date_entry.grid(row=4, column=1, padx=10, pady=(0, 6), sticky=W)

    info_var = StringVar(value="")
    info_label = Label(form_container, textvariable=info_var, font=("Segoe UI", 10), bg="#ffffff", fg="#7f8c8d")
    info_label.pack(pady=(0, 6), padx=12, anchor=W)

    selected_med_id = StringVar()

    def clear_form():
        selected_med_id.set("")
        name_entry.delete(0, END)
        dosage_entry.delete(0, END)
        schedule_entry.delete(0, END)
        start_date_entry.delete(0, END)
        end_date_entry.delete(0, END)
        try:
            start_date_entry.insert(0, datetime.today().strftime('%Y-%m-%d'))
        except:
            pass
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
            cursor.execute("SELECT id, name, dosage, schedule, start_date, end_date FROM medications ORDER BY start_date DESC")
            rows = cursor.fetchall()
            all_rows[:] = rows
            render_rows(rows)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch medications: {e}")
        finally:
            if conn:
                conn.close()

    def save_medication():
        name = name_entry.get().strip()
        dosage = dosage_entry.get().strip()
        schedule = schedule_entry.get().strip()
        start_date = start_date_entry.get().strip()
        end_date = end_date_entry.get().strip()
        med_id = selected_med_id.get()

        if not name or not dosage or not schedule or not start_date:
            messagebox.showwarning("Validation Error", "Name, Dosage, Schedule, and Start Date are required.")
            return

        conn = connect_db()
        if not conn:
            messagebox.showerror("Database Error", "Could not connect to the database.")
            return
        try:
            cursor = conn.cursor()
            if med_id:
                cursor.execute(
                    "UPDATE medications SET name=%s, dosage=%s, schedule=%s, start_date=%s, end_date=%s WHERE id=%s",
                    (name, dosage, schedule, start_date, end_date if end_date else None, med_id)
                )
            else:
                cursor.execute(
                    "INSERT INTO medications (name, dosage, schedule, start_date, end_date) VALUES (%s, %s, %s, %s, %s)",
                    (name, dosage, schedule, start_date, end_date if end_date else None)
                )
            conn.commit()
            info_var.set("Medication saved successfully!")
            clear_form()
            refresh_table()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save medication: {e}")
        finally:
            if conn:
                conn.close()

    def on_row_select(event):
        selected_item = tree.focus()
        if not selected_item:
            return
        
        item_values = tree.item(selected_item, "values")
        med_id = item_values[0]
        
        conn = connect_db()
        if not conn: return
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM medications WHERE id = %s", (med_id,))
            med = cursor.fetchone()
            if med:
                clear_form()
                selected_med_id.set(med['id'])
                name_entry.insert(0, med['name'])
                dosage_entry.insert(0, med['dosage'])
                schedule_entry.insert(0, med['schedule'])
                start_date_entry.insert(0, med['start_date'].strftime('%Y-%m-%d'))
                if med['end_date']:
                    end_date_entry.insert(0, med['end_date'].strftime('%Y-%m-%d'))
        except Exception as e:
            messagebox.showerror("Error", f"Could not fetch medication details: {e}")
        finally:
            if conn: conn.close()

    def delete_medication():
        med_id = selected_med_id.get()
        if not med_id:
            messagebox.showwarning("Selection Error", "Please select a medication to delete.")
            return
        
        if not messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this medication?"):
            return

        conn = connect_db()
        if not conn: return
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM medications WHERE id = %s", (med_id,))
            conn.commit()
            messagebox.showinfo("Success", "Medication deleted successfully.")
            clear_form()
            refresh_table()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete medication: {e}")
        finally:
            if conn: conn.close()

    button_frame = Frame(form_container, bg="#ffffff")
    button_frame.pack(pady=10)

    ttk.Button(button_frame, text="💾 Save", command=save_medication).grid(row=0, column=0, padx=6)
    ttk.Button(button_frame, text="♻️ Clear", command=clear_form).grid(row=0, column=1, padx=6)
    ttk.Button(button_frame, text="🗑️ Delete", command=delete_medication).grid(row=0, column=2, padx=6)
    ttk.Button(refresh_btn_container, text="🔄 Refresh", command=lambda: [clear_form(), refresh_table()]).pack(side=RIGHT)

    table_container = Frame(main_container, bg="#ffffff", relief="raised", bd=2)
    table_container.grid(row=0, column=1, sticky="nsew")

    Label(
        table_container,
        text="📊 Your Medications Overview",
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
    
    columns = ("id", "name", "dosage", "schedule", "start_date", "end_date")
    tree = ttk.Treeview(tree_frame, columns=columns, show="headings", style="Custom.Treeview")
    
    tree.heading("id", text="ID")
    tree.heading("name", text="Name")
    tree.heading("dosage", text="Dosage")
    tree.heading("schedule", text="Schedule")
    tree.heading("start_date", text="Start Date")
    tree.heading("end_date", text="End Date")

    tree.column("id", width=40, anchor=CENTER)
    tree.column("name", width=150)
    tree.column("dosage", width=100)
    tree.column("schedule", width=120)
    tree.column("start_date", width=100, anchor=CENTER)
    tree.column("end_date", width=100, anchor=CENTER)

    vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    vsb.pack(side=RIGHT, fill=Y)
    tree.pack(expand=True, fill=BOTH)
    
    tree.bind("<<TreeviewSelect>>", on_row_select)

    refresh_table()
