import os
import re
import threading
from tkinter import *
from tkinter import messagebox, ttk, scrolledtext
from datetime import datetime

try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
    _TRANSFORMERS_AVAILABLE = True
except ImportError:
    AutoModelForCausalLM, AutoTokenizer = None, None
    _TRANSFORMERS_AVAILABLE = False

try:
    from tkcalendar import DateEntry
    _TKCALENDAR_AVAILABLE = True
except ImportError:
    _TKCALENDAR_AVAILABLE = False


# --- AI Model Configuration ---
MODEL_NAME = "distilgpt2"
MODEL_PATH = os.path.join(".", "model_cache", MODEL_NAME)
model = None
tokenizer = None
# --- End AI Configuration ---


def _clear_frame(frame: Frame):
    for widget in frame.winfo_children():
        widget.destroy()

def show_goals(parent_frame: Frame, connect_db, go_back):
    _clear_frame(parent_frame)

    # --- AI Model Handling ---
    ai_status_var = StringVar(value="AI model not loaded.")
    
    # --- Smart deterministic planner (fallback when LLM outputs are poor) ---
    def _limit_words(s: str, n: int = 10) -> str:
        words = s.strip().split()
        return (" ".join(words[:n]) + ("..." if len(words) > n else "")).strip()

    def _infer_weeks_from_text(text: str) -> int:
        """Roughly infer weeks from natural language like 'in 1 month', 'for 6 weeks', '10 days'."""
        t = (text or "").lower()
        # months
        m = re.search(r"(\d+)\s*(month|months|mon)\b", t)
        if m:
            return max(1, int(m.group(1)) * 4)
        # weeks
        w = re.search(r"(\d+)\s*(week|weeks|wk|wks)\b", t)
        if w:
            return max(1, int(w.group(1)))
        # days
        d = re.search(r"(\d+)\s*(day|days)\b", t)
        if d:
            days = int(d.group(1))
            return max(1, (days + 6) // 7)
        return 0

    def _detect_topic(title: str, desc: str) -> str:
        text = f"{title} {desc}".lower()
        office_keywords = [
            "ms office", "microsoft office", "word", "excel", "powerpoint", "outlook", "onedrive"
        ]
        if any(k in text for k in office_keywords):
            return "ms_office"
        return "generic_learn"

    def _tasks_for_topic(topic: str) -> list:
        if topic == "ms_office":
            base = [
                "Install Microsoft Office and sign in",
                "Learn Word: formatting, styles, page layout",
                "Write one-page document with headings",
                "Learn Excel: cells, formulas, functions",
                "Practice Excel: SUM, AVERAGE, IF, VLOOKUP",
                "Create Excel chart and pivot table",
                "Learn PowerPoint: slides, themes, layouts",
                "Build 10-slide presentation with transitions",
                "Learn Outlook: mail, calendar, rules",
                "Set up OneDrive and file sharing",
                "Practice keyboard shortcuts daily",
                "Review templates: resume, invoice, report",
            ]
        else:
            # very generic study plan
            base = [
                "Define clear learning objectives",
                "Collect the best beginner resources",
                "Schedule daily 30-minute study blocks",
                "Complete one focused practice session",
                "Create a mini project to apply skills",
                "Review mistakes and notes daily",
                "Seek feedback from a knowledgeable peer",
                "Summarize learnings into a cheat sheet",
            ]
        return [_limit_words(t, 10) for t in base]

    def _build_rule_based_plan(title: str, desc: str) -> list:
        topic = _detect_topic(title, desc)
        weeks = _infer_weeks_from_text(desc)
        tasks = _tasks_for_topic(topic)
        # Cap total tasks to a reasonable number for short timeframes
        max_tasks = 8 if weeks and weeks <= 4 else min(12, len(tasks))
        tasks = tasks[:max_tasks]
        # If we know the weeks, prefix early tasks with week labels
        if weeks > 0:
            # use up to min(weeks, len(tasks)) week labels
            label_count = min(weeks, len(tasks))
            labeled = []
            for i, t in enumerate(tasks):
                if i < label_count:
                    pref = f"Week {i+1}: "
                    labeled.append(_limit_words(pref + t, 10))
                else:
                    labeled.append(_limit_words(t, 10))
            tasks = labeled
        else:
            tasks = [_limit_words(t, 10) for t in tasks]
        # Final sanitizer: drop any empty strings
        return [t for t in tasks if t]
    # --- End Smart deterministic planner ---
    
    def load_model_offline():
        """Loads the model from local cache in a background thread."""
        global model, tokenizer
        if not _TRANSFORMERS_AVAILABLE:
            ai_status_var.set("❌ 'transformers' library not found.")
            return

        if model and tokenizer:
            ai_status_var.set("✅ AI model is ready.")
            generate_ai_tasks_button.config(state=NORMAL)
            return

        ai_status_var.set("🔄 Loading AI model...")
        try:
            if not os.path.exists(MODEL_PATH):
                ai_status_var.set(f"❌ Model not found at '{MODEL_PATH}'.")
                messagebox.showwarning("AI Model Not Found", f"The model cache was not found at '{MODEL_PATH}'.\nPlease run `download_model.py` first.")
                return

            tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, local_files_only=True)
            model = AutoModelForCausalLM.from_pretrained(MODEL_PATH, local_files_only=True)
            ai_status_var.set("✅ AI model is ready.")
            generate_ai_tasks_button.config(state=NORMAL)
        except Exception as e:
            ai_status_var.set("❌ Error loading AI model.")
            messagebox.showerror("AI Model Error", f"Failed to load the local AI model:\n{e}")

    def generate_tasks_threaded():
        """Generates tasks in a thread to keep UI responsive."""
        goal_title = title_entry.get().strip()
        goal_desc = desc_text.get("1.0", END).strip()

        if not goal_title:
            messagebox.showwarning("Input Needed", "Please provide a Goal Title to generate tasks.")
            return
        
        threading.Thread(target=generate_tasks, args=(goal_title, goal_desc)).start()

    def generate_tasks(goal_title, goal_desc):
        """Uses the AI model to generate tasks."""
        if not model or not tokenizer:
            ai_status_var.set("❌ AI model not loaded.")
            return

        ai_status_var.set("⏳ Generating tasks...")
        generate_ai_tasks_button.config(state=DISABLED)
        ai_tasks_listbox.delete(0, END)

        try:
            # 1) Try deterministic smart planner first for relevance and brevity
            planner_tasks = _build_rule_based_plan(goal_title, goal_desc)
            if planner_tasks:
                for task in planner_tasks:
                    ai_tasks_listbox.insert(END, task)
                ai_status_var.set(f"✅ Generated {len(planner_tasks)} tasks (smart planner).")
                return

            # 2) Fallback to the offline model if planner yields nothing
            # A much simpler and more direct prompt to avoid confusing the small model.
            # It no longer contains a complex example that the model might copy.
            prompt = (
                "Create a short, numbered list of tasks for the following goal. "
                "Base the tasks ONLY on the Goal and Description provided.\n"
                f"Goal: {goal_title}\n"
                f"Description: {goal_desc}\n\n"
                "Tasks:\n1."
            )
            inputs = tokenizer(prompt, return_tensors="pt")
            outputs = model.generate(
                **inputs,
                max_new_tokens=100,
                num_return_sequences=1,
                no_repeat_ngram_size=2,
                temperature=0.7,
                top_k=50,
                top_p=0.95,
                pad_token_id=tokenizer.eos_token_id
            )
            generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            tasks = parse_generated_tasks(generated_text)
            
            if tasks:
                for task in tasks:
                    ai_tasks_listbox.insert(END, task)
                ai_status_var.set(f"✅ Generated {len(tasks)} tasks.")
            else:
                ai_status_var.set("⚠️ No tasks generated. Try a different goal.")
        except Exception as e:
            ai_status_var.set("❌ Task generation failed.")
            messagebox.showerror("AI Generation Error", f"An error occurred: {e}")
        finally:
            generate_ai_tasks_button.config(state=NORMAL)

    def parse_generated_tasks(text: str) -> list:
        """
        Parses the raw model output to extract a clean list of tasks,
        enforcing a word limit and filtering out irrelevant content.
        """
        # Find the 'Tasks:' section and work from there.
        plan_section_match = re.search(r"Tasks:(.*)", text, re.DOTALL)
        if not plan_section_match:
            return []
        
        plan_section = plan_section_match.group(1)
        
        # Extract numbered list items.
        raw_tasks = re.findall(r"\d+\.\s*(.+)", plan_section)
        
        cleaned_tasks = []
        # Keywords to filter out irrelevant, example-based responses.
        filter_keywords = ['python', 'numpy', 'pandas', 'matplotlib', 'data analysis', 'skill']

        for task in raw_tasks:
            task_lower = task.lower()
            # 1. Filter out tasks that contain keywords from the old, irrelevant examples.
            if any(keyword in task_lower for keyword in filter_keywords):
                continue

            # 2. Truncate to 10 words to keep tasks concise.
            words = task.strip().split()
            if len(words) > 10:
                task = ' '.join(words[:10]) + '...'
            else:
                task = ' '.join(words)
            
            if task:
                cleaned_tasks.append(task)
                
        return cleaned_tasks

    # --- End AI Model Handling ---

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

    # --- AI Task Generation UI ---
    ai_frame = Frame(form_container, bg="#ffffff")
    ai_frame.pack(pady=10, padx=16, fill=X)

    generate_ai_tasks_button = ttk.Button(ai_frame, text="🤖 Generate Tasks with AI", command=generate_tasks_threaded, state=DISABLED)
    generate_ai_tasks_button.pack(pady=(5, 10))

    ai_status_label = Label(ai_frame, textvariable=ai_status_var, font=("Segoe UI", 9), bg="#ffffff", fg="#555")
    ai_status_label.pack()

    ai_tasks_listbox = Listbox(ai_frame, height=6, font=("Segoe UI", 10), relief="solid", bd=1)
    ai_tasks_listbox.pack(fill=X, expand=True, pady=(5, 10))
    
    def save_generated_tasks():
        goal_id = selected_goal_id.get()
        if not goal_id:
            messagebox.showwarning("No Goal Selected", "Please save the main goal first or select an existing one.")
            return
            
        tasks_to_save = ai_tasks_listbox.get(0, END)
        if not tasks_to_save:
            messagebox.showwarning("No Tasks", "There are no generated tasks to save.")
            return

        conn = connect_db()
        if not conn: return
        try:
            cursor = conn.cursor()
            for task_desc in tasks_to_save:
                cursor.execute("INSERT INTO goal_tasks (goal_id, task_description) VALUES (%s, %s)", (goal_id, task_desc))
            conn.commit()
            messagebox.showinfo("Success", f"{len(tasks_to_save)} AI-generated tasks have been saved for this goal.")
            ai_tasks_listbox.delete(0, END)
            # Optionally, refresh the single goal view if it's open
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to save generated tasks: {e}")
        finally:
            if conn: conn.close()

    ttk.Button(ai_frame, text="💾 Save Generated Tasks", command=save_generated_tasks).pack(pady=5)
    # --- End AI Task Generation UI ---

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
        
        # Clear AI tasks when a new goal is selected
        ai_tasks_listbox.delete(0, END)
        ai_status_var.set("✅ AI model is ready.")

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
    
    def on_double_click(event):
        selected_item = tree.focus()
        if not selected_item:
            return
        item_values = tree.item(selected_item, "values")
        goal_id = item_values[0]
        show_single_goal_view(goal_id)

    tree.bind("<<TreeviewSelect>>", on_row_select)
    tree.bind("<Double-1>", on_double_click)

    # --- Load AI model in background ---
    threading.Thread(target=load_model_offline, daemon=True).start()
    # ---

    def show_single_goal_view(goal_id):
        _clear_frame(parent_frame)

        conn = connect_db()
        if not conn:
            messagebox.showerror("Database Error", "Could not connect to the database.")
            go_back()
            return
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM goals WHERE id = %s", (goal_id,))
            goal = cursor.fetchone()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch goal: {e}")
            conn.close()
            go_back()
            return
        
        if not goal:
            messagebox.showerror("Error", "Goal not found.")
            conn.close()
            go_back()
            return

        header_frame = Frame(parent_frame, bg="#8e44ad", height=70)
        header_frame.pack(fill=X, pady=(0, 20))
        header_frame.pack_propagate(False)
        Label(header_frame, text=f"🎯 {goal['title']}", font=("Segoe UI", 24, "bold"), bg="#8e44ad", fg="#ffffff").pack(pady=15)

        nav_frame = Frame(parent_frame, bg="#f8f9fc")
        nav_frame.pack(fill=X, padx=20, pady=(0, 10))
        Button(nav_frame, text="⬅️ Back to All Goals", command=lambda: show_goals(parent_frame, connect_db, go_back), bg="#34495e", fg="white", font=("Segoe UI", 10), relief="flat", padx=10, pady=4).pack(side=LEFT)

        main_container = Frame(parent_frame, bg="#f8f9fc")
        main_container.pack(fill=BOTH, expand=True, padx=20, pady=10)

        # Goal Details
        details_frame = Frame(main_container, bg="#ffffff", relief="raised", bd=2)
        details_frame.pack(fill=X, pady=(0, 10))
        Label(details_frame, text=f"Description: {goal['description'] or 'N/A'}", font=("Segoe UI", 12), bg="#ffffff", wraplength=500, justify=LEFT).pack(anchor=W, padx=10, pady=5)
        Label(details_frame, text=f"Target Date: {goal['target_date'].strftime('%Y-%m-%d')}", font=("Segoe UI", 12), bg="#ffffff").pack(anchor=W, padx=10, pady=5)
        status_text_var = StringVar(value=f"Status: {goal['status']}")
        status_label = Label(details_frame, textvariable=status_text_var, font=("Segoe UI", 12), bg="#ffffff")
        status_label.pack(anchor=W, padx=10, pady=5)
        
        progress_var = DoubleVar(value=goal['progress'])
        progress_bar = ttk.Progressbar(details_frame, orient=HORIZONTAL, length=300, mode='determinate', variable=progress_var)
        progress_bar.pack(pady=10, padx=10)
        progress_label = Label(details_frame, text=f"{goal['progress']}%", font=("Segoe UI", 12, "bold"), bg="#ffffff")
        progress_label.pack()

        # Sub-tasks
        tasks_container = Frame(main_container, bg="#ffffff", relief="raised", bd=2)
        tasks_container.pack(fill=BOTH, expand=True)
        Label(tasks_container, text="Sub-tasks", font=("Segoe UI", 16, "bold"), bg="#ffffff").pack(pady=10)

        tasks_frame = Frame(tasks_container, bg="#ffffff")
        tasks_frame.pack(fill=BOTH, expand=True, padx=10)

        sub_tasks = []

        def update_progress():
            completed_tasks = sum(1 for _, _, var in sub_tasks if var.get())
            total_tasks = len(sub_tasks)
            progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            progress_var.set(progress)
            progress_label.config(text=f"{progress:.0f}%")
            try:
                c = conn.cursor()
                # Decide new status based on completion
                new_status = None
                if total_tasks > 0:
                    if completed_tasks == 0:
                        new_status = "Not Started"
                    elif completed_tasks == total_tasks:
                        new_status = "Achieved"
                    else:
                        new_status = "In Progress"

                if new_status is not None:
                    c.execute("UPDATE goals SET progress = %s, status = %s WHERE id = %s", (progress, new_status, goal_id))
                    status_text_var.set(f"Status: {new_status}")
                else:
                    c.execute("UPDATE goals SET progress = %s WHERE id = %s", (progress, goal_id))
                conn.commit()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update progress: {e}")

        def toggle_task_completion(task_id, check_var):
            try:
                c = conn.cursor()
                c.execute("UPDATE goal_tasks SET is_completed = %s WHERE id = %s", (check_var.get(), task_id))
                conn.commit()
                update_progress()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update sub-task: {e}")

        def render_sub_tasks():
            for widget in tasks_frame.winfo_children():
                widget.destroy()
            sub_tasks.clear()
            try:
                c = conn.cursor(dictionary=True)
                c.execute("SELECT id, task_description, is_completed FROM goal_tasks WHERE goal_id = %s ORDER BY created_at ASC", (goal_id,))
                tasks = c.fetchall()
                for task in tasks:
                    var = BooleanVar(value=task['is_completed'])
                    cb = ttk.Checkbutton(tasks_frame, text=task['task_description'], variable=var, command=lambda t_id=task['id'], v=var: toggle_task_completion(t_id, v))
                    cb.pack(anchor=W, padx=10)
                    sub_tasks.append((task['id'], task['task_description'], var))
                update_progress()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to fetch sub-tasks: {e}")

        add_task_frame = Frame(tasks_container, bg="#ffffff")
        add_task_frame.pack(fill=X, pady=10, padx=10)
        new_task_entry = ttk.Entry(add_task_frame, font=("Segoe UI", 11), width=40)
        new_task_entry.pack(side=LEFT, expand=True, fill=X)

        def add_new_task():
            desc = new_task_entry.get().strip()
            if not desc:
                return
            try:
                c = conn.cursor()
                c.execute("INSERT INTO goal_tasks (goal_id, task_description) VALUES (%s, %s)", (goal_id, desc))
                conn.commit()
                new_task_entry.delete(0, END)
                render_sub_tasks()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add sub-task: {e}")

        ttk.Button(add_task_frame, text="Add Task", command=add_new_task).pack(side=LEFT, padx=5)
        
        render_sub_tasks()
        
        def on_close():
            if conn:
                conn.close()
            parent_frame.destroy()

    refresh_table()
