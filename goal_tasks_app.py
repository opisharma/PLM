# goal_tasks_app.py
import os
import re
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext

# --- Check for Transformers ---
try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
except ImportError:
    messagebox.showerror(
        "Dependency Missing",
        "The 'transformers' library is not installed.\n"
        "Please install it by running: pip install transformers"
    )
    exit()

# --- Configuration ---
MODEL_NAME = "distilgpt2"
MODEL_PATH = os.path.join(".", "model_cache", MODEL_NAME)

# --- Global Variables ---
model = None
tokenizer = None
model_loading_thread = None
stop_event = threading.Event()

# --- AI Model Handling ---
def load_model_offline():
    """
    Loads the model and tokenizer from the local cache directory.
    Updates the UI status label accordingly.
    """
    global model, tokenizer
    
    status_var.set("🔄 Loading model... Please wait.")
    root.update_idletasks()

    try:
        if not os.path.exists(MODEL_PATH):
            status_var.set(f"❌ Error: Model directory not found at '{MODEL_PATH}'.")
            messagebox.showerror(
                "Model Not Found",
                f"The model cache was not found at '{MODEL_PATH}'.\n"
                "Please run the `download_model.py` script first while you have an internet connection."
            )
            return

        # Load tokenizer and model from the local directory only
        tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, local_files_only=True)
        model = AutoModelForCausalLM.from_pretrained(MODEL_PATH, local_files_only=True)
        
        status_var.set("✅ Model loaded successfully. Ready to generate tasks!")
        generate_button.config(state=tk.NORMAL)

    except Exception as e:
        status_var.set("❌ Error loading model. Check console for details.")
        messagebox.showerror("Model Loading Failed", f"An error occurred: {e}")
        print(f"Full error: {e}")

def generate_tasks_threaded(goal_title, goal_description):
    """
    Wrapper to run the task generation in a separate thread to keep the UI responsive.
    """
    thread = threading.Thread(target=generate_tasks, args=(goal_title, goal_description))
    thread.start()

def generate_tasks(goal_title, goal_description):
    """
    Generates a list of tasks based on the goal's title and description using the local model.
    """
    if not model or not tokenizer:
        status_var.set("❌ Model is not loaded. Cannot generate tasks.")
        return

    status_var.set("⏳ Generating tasks...")
    generate_button.config(state=tk.DISABLED)
    task_listbox.delete(0, tk.END)
    root.update_idletasks()

    try:
        # Create a detailed prompt for the AI
        prompt = (
            f"Goal: {goal_title}\n"
            f"Description: {goal_description}\n\n"
            "Based on the goal above, generate a numbered list of 5 simple, actionable tasks to achieve it. "
            "Each task should be short and clear.\n\n"
            "Here are the tasks:\n1."
        )

        inputs = tokenizer(prompt, return_tensors="pt")
        
        # Generate text with adjusted parameters for better task lists
        outputs = model.generate(
            **inputs,
            max_length=150,
            num_return_sequences=1,
            no_repeat_ngram_size=2,
            temperature=0.7,
            top_k=50,
            top_p=0.95,
            pad_token_id=tokenizer.eos_token_id
        )

        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Parse the generated text to extract clean tasks
        tasks = parse_generated_tasks(generated_text)

        # Update the UI with the generated tasks
        task_listbox.delete(0, tk.END)
        if tasks:
            for i, task in enumerate(tasks, 1):
                task_listbox.insert(tk.END, f"{i}. {task}")
            status_var.set(f"✅ Successfully generated {len(tasks)} tasks!")
        else:
            status_var.set("⚠️ Generation finished, but no tasks were found.")
            task_listbox.insert(tk.END, "No tasks generated. Try a different goal.")

    except Exception as e:
        status_var.set("❌ Task generation failed. See console for error.")
        messagebox.showerror("Generation Error", f"An error occurred: {e}")
    finally:
        generate_button.config(state=tk.NORMAL)

def parse_generated_tasks(text: str) -> list:
    """
    Parses the raw output from the model to extract a clean list of tasks.
    It looks for numbered lines and cleans them up.
    """
    # Find the part of the text that contains the task list
    tasks_section = text.split("Here are the tasks:")[-1]
    
    # Use regex to find numbered list items
    # This pattern looks for a number, a dot, optional space, and then captures the text
    tasks = re.findall(r"\d+\.\s*(.+)", tasks_section)
    
    # Clean up each task: strip whitespace and remove trailing noise
    cleaned_tasks = [task.strip() for task in tasks if task.strip()]
    
    return cleaned_tasks

# --- UI Setup ---
def setup_ui():
    """
    Initializes and configures the main Tkinter UI components.
    """
    global root, status_var, generate_button, task_listbox

    root = tk.Tk()
    root.title("🎯 AI Goal to Task Generator (Offline)")
    root.geometry("700x600")
    root.configure(bg="#f0f2f5")

    main_frame = tk.Frame(root, bg="#f0f2f5", padx=20, pady=20)
    main_frame.pack(fill=tk.BOTH, expand=True)

    # --- Input Frame ---
    input_frame = tk.LabelFrame(main_frame, text="Goal Details", font=("Segoe UI", 12, "bold"), bg="white", padx=15, pady=15)
    input_frame.pack(fill=tk.X, pady=(0, 20))

    tk.Label(input_frame, text="Goal Title:", font=("Segoe UI", 11), bg="white").grid(row=0, column=0, sticky="w", pady=5)
    title_entry = tk.Entry(input_frame, font=("Segoe UI", 11), width=60)
    title_entry.grid(row=0, column=1, pady=5, padx=10)

    tk.Label(input_frame, text="Goal Description:", font=("Segoe UI", 11), bg="white").grid(row=1, column=0, sticky="nw", pady=5)
    desc_text = scrolledtext.ScrolledText(input_frame, height=5, width=60, font=("Segoe UI", 11), wrap=tk.WORD)
    desc_text.grid(row=1, column=1, pady=5, padx=10)

    # --- Control Frame ---
    control_frame = tk.Frame(main_frame, bg="#f0f2f5")
    control_frame.pack(fill=tk.X, pady=(0, 10))

    generate_button = tk.Button(
        control_frame,
        text="🚀 Generate Tasks",
        font=("Segoe UI", 12, "bold"),
        bg="#007bff",
        fg="white",
        state=tk.DISABLED,  # Disabled until model is loaded
        command=lambda: generate_tasks_threaded(title_entry.get(), desc_text.get("1.0", tk.END))
    )
    generate_button.pack(side=tk.LEFT)

    # --- Status Label ---
    status_var = tk.StringVar()
    status_label = tk.Label(main_frame, textvariable=status_var, font=("Segoe UI", 10), bg="#f0f2f5", fg="#555")
    status_label.pack(fill=tk.X, pady=(5, 10))

    # --- Output Frame ---
    output_frame = tk.LabelFrame(main_frame, text="Generated Tasks", font=("Segoe UI", 12, "bold"), bg="white", padx=15, pady=15)
    output_frame.pack(fill=tk.BOTH, expand=True)

    task_listbox = tk.Listbox(output_frame, font=("Segoe UI", 11), bg="#ffffff", selectbackground="#cce5ff")
    task_listbox.pack(fill=tk.BOTH, expand=True)

    # --- Start model loading in a separate thread ---
    global model_loading_thread
    model_loading_thread = threading.Thread(target=load_model_offline)
    model_loading_thread.start()

    root.mainloop()

if __name__ == "__main__":
    setup_ui()
