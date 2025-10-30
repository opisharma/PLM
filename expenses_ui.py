from tkinter import *
from tkinter import messagebox, ttk
from datetime import datetime
import calendar

# Optional: matplotlib for charts (installed via requirements)
try:
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    _MATPLOTLIB_AVAILABLE = True
except Exception:
    _MATPLOTLIB_AVAILABLE = False

try:
    from tkcalendar import DateEntry
    _TKCALENDAR_AVAILABLE = True
except ImportError:
    _TKCALENDAR_AVAILABLE = False



def _clear_frame(frame: Frame):
    for widget in frame.winfo_children():
        try:
            widget.destroy()
        except Exception:
            pass


def show_expenses(parent_frame: Frame, connect_db, go_back):
    """Render the Expense Tracker UI inside the given parent frame.

    Args:
        parent_frame: The container where the UI should be rendered.
        connect_db: Callable returning a DB connection.
        go_back: Callback to navigate back to the dashboard.
    """
    _clear_frame(parent_frame)

    # Header
    header_frame = Frame(parent_frame, bg="#f39c12", height=70)
    header_frame.pack(fill=X, pady=(0, 20))
    header_frame.pack_propagate(False)

    Label(
        header_frame,
        text="💰 Expense Management System",
        font=("Segoe UI", 24, "bold"),
        bg="#f39c12",
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
        text="🧾 Expense Details",
        font=("Segoe UI", 16, "bold"),
        bg="#ffffff",
        fg="#2c3e50",
    ).pack(pady=10)

    form_frame = Frame(form_container, bg="#ffffff")
    form_frame.pack(pady=10, padx=16, fill=X)

    # Fields
    Label(form_frame, text="Title:", font=("Segoe UI", 12, "bold"), bg="#ffffff", fg="#2c3e50").grid(row=0, column=0, sticky=W, pady=(0, 6))
    title_entry = ttk.Entry(form_frame, font=("Segoe UI", 11), width=28)
    title_entry.grid(row=0, column=1, padx=10, pady=(0, 6), sticky=W)

    Label(form_frame, text="Amount:", font=("Segoe UI", 12, "bold"), bg="#ffffff", fg="#2c3e50").grid(row=1, column=0, sticky=W, pady=(0, 6))
    amount_entry = ttk.Entry(form_frame, font=("Segoe UI", 11), width=28)
    amount_entry.grid(row=1, column=1, padx=10, pady=(0, 6), sticky=W)

    Label(form_frame, text="Category:", font=("Segoe UI", 12, "bold"), bg="#ffffff", fg="#2c3e50").grid(row=2, column=0, sticky=W, pady=(0, 6))
    category_var = StringVar(value="General")
    category_combo = ttk.Combobox(
        form_frame,
        textvariable=category_var,
        values=(
            "General",
            "Food",
            "Transport",
            "Utilities",
            "Rent",
            "Healthcare",
            "Entertainment",
            "Shopping",
            "Education",
            "Travel",
            "Other",
        ),
        state="readonly",
        width=26,
    )
    category_combo.grid(row=2, column=1, padx=10, pady=(0, 6), sticky=W)

    Label(form_frame, text="Date:", font=("Segoe UI", 12, "bold"), bg="#ffffff", fg="#2c3e50").grid(row=3, column=0, sticky=W, pady=(0, 6))
    if _TKCALENDAR_AVAILABLE:
        date_entry = DateEntry(form_frame, width=26, background='darkblue',
                               foreground='white', borderwidth=2, date_pattern='y-mm-dd', font=("Segoe UI", 11))
    else:
        date_entry = ttk.Entry(form_frame, font=("Segoe UI", 11), width=28)
        try:
            date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        except Exception:
            pass
    date_entry.grid(row=3, column=1, padx=10, pady=(0, 6), sticky=W)

    Label(form_frame, text="Payment Method:", font=("Segoe UI", 12, "bold"), bg="#ffffff", fg="#2c3e50").grid(row=4, column=0, sticky=W, pady=(0, 6))
    payment_var = StringVar(value="Cash")
    payment_combo = ttk.Combobox(
        form_frame,
        textvariable=payment_var,
        values=("Cash", "Card", "Bank", "Bkash", "Nagad", "Other"),
        state="readonly",
        width=26,
    )
    payment_combo.grid(row=4, column=1, padx=10, pady=(0, 6), sticky=W)

    Label(form_frame, text="Status:", font=("Segoe UI", 12, "bold"), bg="#ffffff", fg="#2c3e50").grid(row=5, column=0, sticky=W, pady=(0, 6))
    status_var = StringVar(value="Paid")
    status_combo = ttk.Combobox(
        form_frame,
        textvariable=status_var,
        values=("Planned", "Incurred", "Paid"),
        state="readonly",
        width=26,
    )
    status_combo.grid(row=5, column=1, padx=10, pady=(0, 6), sticky=W)

    Label(form_frame, text="Notes:", font=("Segoe UI", 12, "bold"), bg="#ffffff", fg="#2c3e50").grid(row=6, column=0, sticky=NW, pady=(0, 6))
    notes_text = Text(form_frame, width=28, height=5, font=("Segoe UI", 11), relief="solid", bd=1)
    notes_text.grid(row=6, column=1, padx=10, pady=(0, 6), sticky=W)
    notes_scroll = ttk.Scrollbar(form_frame, orient=VERTICAL, command=notes_text.yview)
    notes_text.configure(yscrollcommand=notes_scroll.set)
    notes_scroll.grid(row=6, column=2, sticky="nsw", pady=(0, 6))

    # Validation/info label
    info_var = StringVar(value="")
    info_label = Label(form_container, textvariable=info_var, font=("Segoe UI", 10), bg="#ffffff", fg="#7f8c8d")
    info_label.pack(pady=(0, 6), padx=12, anchor=W)

    selected_expense_id = StringVar()

    def clear_form():
        selected_expense_id.set("")
        title_entry.delete(0, END)
        amount_entry.delete(0, END)
        category_var.set("General")
        try:
            date_entry.delete(0, END)
            date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        except Exception:
            pass
        payment_var.set("Cash")
        status_var.set("Paid")
        notes_text.delete("1.0", END)
        info_var.set("")

    all_rows = []  # cache for filtering/sorting

    # Helper to convert various date representations (str/date/datetime) to a date
    def _to_date(val):
        try:
            # If it's already a datetime/date-like with year/month/day
            if hasattr(val, "year") and hasattr(val, "month") and hasattr(val, "day"):
                # If datetime, convert to date
                try:
                    if isinstance(val, datetime):
                        return val.date()
                except Exception:
                    pass
                # Assume it's a date-like
                from datetime import date as _date_cls  # local import to avoid top-level
                try:
                    if isinstance(val, _date_cls):
                        return val
                except Exception:
                    pass
                # Fallback: build date from attributes
                try:
                    return datetime(int(val.year), int(val.month), int(val.day)).date()
                except Exception:
                    return None

            # If it's a string, try multiple formats
            if isinstance(val, str):
                fmts = [
                    "%Y-%m-%d",
                    "%Y/%m/%d",
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%dT%H:%M:%S",
                ]
                for f in fmts:
                    try:
                        return datetime.strptime(val, f).date()
                    except Exception:
                        pass
                # Try fromisoformat
                try:
                    return datetime.fromisoformat(val).date()
                except Exception:
                    return None
        except Exception:
            return None
        return None

    def render_rows(rows):
        # Clear existing
        for child in expense_table.get_children():
            expense_table.delete(child)
        # Insert new
        for r in rows:
            expense_table.insert(
                "",
                END,
                values=(
                    r["id"],
                    r["title"],
                    r["category"],
                    f"{r['amount']:.2f}",
                    r["date"],
                    r["payment_method"],
                    r["status"],
                ),
            )

    def apply_filter(*_):
        text = search_var.get().strip().lower()
        cat = filter_category_var.get()
        sts = filter_status_var.get()

        def ok(row):
            if cat != "All" and row["category"] != cat:
                return False
            if sts != "All" and row["status"] != sts:
                return False
            if text and (text not in row["title"].lower() and text not in (row.get("notes") or "").lower()):
                return False
            return True

        render_rows([r for r in all_rows if ok(r)])

    def refresh_table():
        nonlocal all_rows
        conn = None
        cur = None
        try:
            conn = connect_db()
            if conn is None:
                messagebox.showerror("Database Error", "Unable to connect to database.")
                return
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, title, category, amount, date, payment_method, status, notes
                FROM expenses
                ORDER BY date DESC, id DESC
                """
            )
            rows = cur.fetchall()
            # Map to list of dicts
            cols = ["id", "title", "category", "amount", "date", "payment_method", "status", "notes"]
            all_rows = [dict(zip(cols, r)) for r in rows]
            apply_filter()
            # Update year options for report
            try:
                _update_year_options()
            except Exception:
                pass
        except Exception as e:
            messagebox.showerror("Query Error", f"Failed to load expenses.\n{e}")
        finally:
            try:
                if cur:
                    cur.close()
            except Exception:
                pass
            try:
                if conn:
                    conn.close()
            except Exception:
                pass

    def save_expense():
        # Validate
        title = title_entry.get().strip()
        amount_raw = amount_entry.get().strip()
        category = category_var.get()
        date_str = date_entry.get().strip()
        payment_method = payment_var.get()
        status = status_var.get()
        notes = notes_text.get("1.0", END).strip()

        if not title:
            info_var.set("Please enter a title.")
            return
        if not amount_raw:
            info_var.set("Please enter an amount.")
            return
        try:
            amount = float(amount_raw)
            if amount <= 0:
                raise ValueError("Amount must be positive")
        except Exception:
            info_var.set("Amount must be a positive number.")
            return
        # Validate date
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            info_var.set("Date must be in YYYY-MM-DD format.")
            return

        conn = None
        cur = None
        try:
            conn = connect_db()
            if conn is None:
                messagebox.showerror("Database Error", "Unable to connect to database.")
                return
            cur = conn.cursor()

            if selected_expense_id.get():
                # Update
                cur.execute(
                    """
                    UPDATE expenses
                    SET title=%s, amount=%s, category=%s, date=%s, payment_method=%s, status=%s, notes=%s
                    WHERE id=%s
                    """,
                    (
                        title,
                        amount,
                        category,
                        date_str,
                        payment_method,
                        status,
                        notes,
                        selected_expense_id.get(),
                    ),
                )
            else:
                # Insert
                cur.execute(
                    """
                    INSERT INTO expenses (title, amount, category, date, payment_method, status, notes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (title, amount, category, date_str, payment_method, status, notes),
                )
            conn.commit()
            clear_form()
            refresh_table()
            info_var.set("Saved successfully.")
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save expense.\n{e}")
        finally:
            try:
                if cur:
                    cur.close()
            except Exception:
                pass
            try:
                if conn:
                    conn.close()
            except Exception:
                pass

    def on_row_select(event):
        try:
            sel = expense_table.selection()
            if not sel:
                return
            vals = expense_table.item(sel[0], "values")
            # values order: id, title, category, amount, date, payment, status
            selected_expense_id.set(vals[0])
            title_entry.delete(0, END)
            title_entry.insert(0, vals[1])
            category_var.set(vals[2])
            amount_entry.delete(0, END)
            try:
                amount_entry.insert(0, float(vals[3]))
            except Exception:
                amount_entry.insert(0, vals[3])
            date_entry.delete(0, END)
            date_entry.insert(0, vals[4])
            payment_var.set(vals[5])
            status_var.set(vals[6])

            # Load notes from cache
            try:
                rid = int(vals[0])
                cached = next((r for r in all_rows if r["id"] == rid), None)
                notes_text.delete("1.0", END)
                if cached and cached.get("notes"):
                    notes_text.insert("1.0", cached["notes"])
            except Exception:
                pass
        except Exception:
            pass

    def delete_expense():
        if not selected_expense_id.get():
            info_var.set("Select a row to delete.")
            return
        if not messagebox.askyesno("Confirm", "Delete selected expense? This cannot be undone."):
            return
        conn = None
        cur = None
        try:
            conn = connect_db()
            if conn is None:
                messagebox.showerror("Database Error", "Unable to connect to database.")
                return
            cur = conn.cursor()
            cur.execute("DELETE FROM expenses WHERE id=%s", (selected_expense_id.get(),))
            conn.commit()
            clear_form()
            refresh_table()
            info_var.set("Deleted successfully.")
        except Exception as e:
            messagebox.showerror("Delete Error", f"Failed to delete expense.\n{e}")
        finally:
            try:
                if cur:
                    cur.close()
            except Exception:
                pass
            try:
                if conn:
                    conn.close()
            except Exception:
                pass

    # Buttons
    button_frame = Frame(form_container, bg="#ffffff")
    button_frame.pack(pady=10)

    ttk.Button(button_frame, text="💾 Save", command=save_expense).grid(row=0, column=0, padx=6)
    ttk.Button(button_frame, text="♻️ Clear", command=clear_form).grid(row=0, column=1, padx=6)
    ttk.Button(button_frame, text="🗑️ Delete", command=delete_expense).grid(row=0, column=2, padx=6)
    ttk.Button(refresh_btn_container, text="🔄 Refresh", command=lambda: [clear_form(), refresh_table()]).pack(side=RIGHT)

    # Table (right)
    table_container = Frame(main_container, bg="#ffffff", relief="raised", bd=2)
    table_container.grid(row=0, column=1, sticky="nsew")

    Label(
        table_container,
        text="📒 Your Expenses Overview",
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
    Label(filter_bar, text="Category:", bg="#ffffff").pack(side=LEFT)
    filter_category_var = StringVar(value="All")
    filter_category = ttk.Combobox(
        filter_bar,
        textvariable=filter_category_var,
        values=("All", "General", "Food", "Transport", "Utilities", "Rent", "Healthcare", "Entertainment", "Shopping", "Education", "Travel", "Other"),
        state="readonly",
        width=14,
    )
    filter_category.pack(side=LEFT, padx=(6, 16))
    Label(filter_bar, text="Status:", bg="#ffffff").pack(side=LEFT)
    filter_status_var = StringVar(value="All")
    filter_status = ttk.Combobox(filter_bar, textvariable=filter_status_var, values=("All", "Planned", "Incurred", "Paid"), state="readonly", width=12)
    filter_status.pack(side=LEFT, padx=(6, 0))

    expense_table = ttk.Treeview(
        table_container,
        columns=("ID", "Title", "Category", "Amount", "Date", "Payment", "Status"),
        show="headings",
        style="Custom.Treeview",
    )

    expense_table.heading("ID", text="🆔 ID")
    expense_table.heading("Title", text="🧾 Title")
    expense_table.heading("Category", text="🏷️ Category")
    expense_table.heading("Amount", text="💲 Amount")
    expense_table.heading("Date", text="📅 Date")
    expense_table.heading("Payment", text="💳 Payment")
    expense_table.heading("Status", text="⚙️ Status")

    expense_table.column("ID", width=60, anchor=CENTER)
    expense_table.column("Title", width=180, anchor=W)
    expense_table.column("Category", width=120, anchor=W)
    expense_table.column("Amount", width=100, anchor=E)
    expense_table.column("Date", width=110, anchor=CENTER)
    expense_table.column("Payment", width=110, anchor=W)
    expense_table.column("Status", width=110, anchor=W)

    expense_table.pack(fill=BOTH, expand=True, padx=16, pady=10)
    expense_table.bind("<<TreeviewSelect>>", on_row_select)

    # --------- Monthly Report (Chart) ---------
    report_container = Frame(table_container, bg="#ffffff")
    report_container.pack(fill=X, padx=16, pady=(0, 16))

    Label(
        report_container,
        text="📊 Monthly Report",
        font=("Segoe UI", 14, "bold"),
        bg="#ffffff",
        fg="#2c3e50",
    ).pack(anchor=W, pady=(0, 6))

    controls_frame = Frame(report_container, bg="#ffffff")
    controls_frame.pack(fill=X)

    # Month selector
    Label(controls_frame, text="Month:", bg="#ffffff").pack(side=LEFT)
    month_var = StringVar(value=str(datetime.now().month).zfill(2))
    month_values = [str(i).zfill(2) + " - " + calendar.month_name[i] for i in range(1, 12 + 1)]
    month_combo = ttk.Combobox(controls_frame, textvariable=month_var, state="readonly", width=14,
                               values=[mv.split(" - ")[0] for mv in month_values])
    month_combo.pack(side=LEFT, padx=(6, 16))

    # Year selector (populate later from data)
    Label(controls_frame, text="Year:", bg="#ffffff").pack(side=LEFT)
    year_var = StringVar(value=str(datetime.now().year))
    year_combo = ttk.Combobox(controls_frame, textvariable=year_var, state="readonly", width=10)
    year_combo.pack(side=LEFT, padx=(6, 16))

    # Chart type
    Label(controls_frame, text="Chart:", bg="#ffffff").pack(side=LEFT)
    chart_type_var = StringVar(value="Pie")
    chart_type = ttk.Combobox(controls_frame, textvariable=chart_type_var, state="readonly", width=10,
                              values=("Pie", "Bar"))
    chart_type.pack(side=LEFT, padx=(6, 16))

    # Generate button
    def _ensure_matplotlib():
        if not _MATPLOTLIB_AVAILABLE:
            messagebox.showinfo(
                "Chart Support Missing",
                "Matplotlib is not installed. Please install it to view charts (pip install matplotlib).",
            )
            return False
        return True

    chart_frame = Frame(report_container, bg="#ffffff")
    chart_frame.pack(fill=BOTH, expand=False, pady=(10, 0))
    current_canvas = {"canvas": None}

    def _update_year_options():
        try:
            years = set()
            for r in all_rows:
                d = _to_date(r.get("date"))
                if d:
                    years.add(str(d.year))
            years = sorted(years, reverse=True)
        except Exception:
            years = [str(datetime.now().year)]
        if not years:
            years = [str(datetime.now().year)]
        year_combo["values"] = years
        if year_var.get() not in years:
            year_var.set(years[0])

    def render_report():
        if not _ensure_matplotlib():
            return
        # Clear previous chart
        if current_canvas["canvas"] is not None:
            try:
                current_canvas["canvas"].get_tk_widget().destroy()
            except Exception:
                pass
            current_canvas["canvas"] = None

        # Aggregate by category for selected month/year
        sel_month = month_var.get()
        sel_year = year_var.get()
        try:
            m = int(sel_month)
            y = int(sel_year)
        except Exception:
            info_var.set("Invalid month/year selected for report.")
            return

        totals = {}
        for r in all_rows:
            d = _to_date(r.get("date"))
            if not d:
                continue
            if d.year == y and d.month == m:
                cat = r.get("category") or "General"
                try:
                    amt = float(r.get("amount") or 0)
                except Exception:
                    amt = 0.0
                totals[cat] = totals.get(cat, 0.0) + amt

        if not totals:
            info_var.set("No expenses found for the selected month.")
            return

        # Build chart figure
        fig = Figure(figsize=(5.5, 2.6), dpi=100)
        ax = fig.add_subplot(111)
        labels = list(totals.keys())
        values = list(totals.values())

        if chart_type_var.get() == "Bar":
            ax.bar(labels, values, color="#3498db")
            ax.set_ylabel("Amount")
            ax.set_title(f"Spending by Category - {calendar.month_name[m]} {y}")
            ax.tick_params(axis='x', rotation=20)
        else:
            ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=140)
            ax.set_title(f"Spending Distribution - {calendar.month_name[m]} {y}")
            ax.axis('equal')

        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=X)
        current_canvas["canvas"] = canvas
        info_var.set("")

    ttk.Button(controls_frame, text="Generate", command=render_report).pack(side=LEFT)

    # Wire filters
    search_var.trace_add("write", apply_filter)
    filter_category_var.trace_add("write", apply_filter)
    filter_status_var.trace_add("write", apply_filter)

    # Initial load
    refresh_table()
    _update_year_options()
