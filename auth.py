from tkinter import *
from tkinter import messagebox
import mysql.connector
import hashlib
import subprocess
import sys
import os

# === Database Connection ===
def connect_db():
    try:
        db = mysql.connector.connect(
            host="localhost",     
            user="root",          
            password="",          
            database="life_manger"  
        )
        print("✅ Connected to MySQL database successfully!")
        return db
    except mysql.connector.Error as err:
        print("❌ Failed to connect:", err)
        return None

# === Hash Password ===
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# === Registration Logic ===
def register_user():
    username = reg_username_entry.get().strip()
    email = reg_email_entry.get().strip()
    password = reg_password_entry.get().strip()
    confirm_password = reg_confirm_password_entry.get().strip()

    # Validation
    if username == "" or email == "" or password == "" or confirm_password == "":
        messagebox.showwarning("Warning", "⚠️ Please fill all fields")
        return

    if len(password) < 6:
        messagebox.showwarning("Warning", "⚠️ Password must be at least 6 characters")
        return
    
    if password != confirm_password:
        messagebox.showerror("Error", "❌ Passwords do not match!")
        return
        
    if "@" not in email or "." not in email:
        messagebox.showwarning("Warning", "⚠️ Please enter a valid email address")
        return

    try:
        conn = connect_db()
        if conn is None:
            return
            
        cursor = conn.cursor()
        hashed_pw = hash_password(password)

        cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                       (username, email, hashed_pw))
        conn.commit()
        conn.close()

        messagebox.showinfo("Success", "✅ Registration Successful!\nRedirecting to Login...")
        
        # Clear registration fields
        reg_username_entry.delete(0, END)
        reg_email_entry.delete(0, END)
        reg_password_entry.delete(0, END)
        reg_confirm_password_entry.delete(0, END)
        
        # Switch to login page
        root.after(1000, show_login_page)  # Wait 1 second then show login

    except mysql.connector.IntegrityError:
        messagebox.showerror("Error", "❌ Username or Email already exists")
    except Exception as e:
        messagebox.showerror("Error", f"Something went wrong:\n{e}")

# === Show Login Page ===
def show_login_page():
    registration_frame.pack_forget()
    login_frame.pack(fill="both", expand=True)
    login_username_entry.focus()

# === Dashboard Launch Function (FIXED) ===
def launch_dashboard():
    """Launch dashboard.py with proper error handling"""
    try:
        # Get current script directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        dashboard_path = os.path.join(current_dir, "dashboard.py")
        
        print(f"🔍 Looking for dashboard.py at: {dashboard_path}")
        
        # Check if dashboard.py exists
        if not os.path.exists(dashboard_path):
            messagebox.showerror("File Not Found", 
                               f"❌ dashboard.py not found!\n\nExpected location:\n{dashboard_path}\n\nPlease make sure dashboard.py is in the same folder as this file.")
            return False
        
        # Try different methods to launch dashboard
        try:
            # Method 1: Use sys.executable with full path (Most reliable)
            process = subprocess.Popen([sys.executable, dashboard_path], 
                                     cwd=current_dir,
                                     creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0)
            print("✅ Dashboard launched successfully with sys.executable")
            
            # Check if process started successfully
            if process.poll() is None:  # Process is running
                return True
            else:
                raise subprocess.SubprocessError("Process failed to start")
                
        except Exception as e1:
            print(f"❌ Method 1 failed: {e1}")
            
            try:
                # Method 2: Direct python command
                process = subprocess.Popen(["python", dashboard_path], 
                                         cwd=current_dir,
                                         shell=True)
                print("✅ Dashboard launched with python command")
                return True
            except Exception as e2:
                print(f"❌ Method 2 failed: {e2}")
                
                try:
                    # Method 3: Python3 command (Linux/Mac)
                    process = subprocess.Popen(["python3", dashboard_path], 
                                             cwd=current_dir)
                    print("✅ Dashboard launched with python3 command")
                    return True
                except Exception as e3:
                    print(f"❌ Method 3 failed: {e3}")
                    
                    # Method 4: Show integrated dashboard as fallback
                    print("⚠️ All external launch methods failed. Opening integrated dashboard...")
                    show_integrated_dashboard()
                    return True
                    
    except Exception as e:
        print(f"❌ Critical error in launch_dashboard: {e}")
        messagebox.showerror("Launch Error", f"❌ Failed to launch dashboard:\n{str(e)}")
        return False

# === Login Logic (FIXED) ===
def login_user():
    username = login_username_entry.get().strip()
    password = login_password_entry.get().strip()

    if not username or not password:
        messagebox.showwarning("Warning", "⚠️ Please fill all fields")
        return

    # Disable login button during processing
    login_btn = None
    for widget in login_button_frame.winfo_children():
        if isinstance(widget, Button) and "Login" in widget['text']:
            login_btn = widget
            break
    
    if login_btn:
        login_btn.config(state='disabled', text="🔄 Logging in...")
        root.update()

    try:
        db = connect_db()
        if db is None:
            if login_btn:
                login_btn.config(state='normal', text="🚀 Login")
            return

        cursor = db.cursor()
        hashed_pw = hash_password(password)
        query = "SELECT id, username, email FROM users WHERE username=%s AND password=%s"
        cursor.execute(query, (username, hashed_pw))
        result = cursor.fetchone()
        
        if result:
            user_id, db_username, email = result
            print(f"✅ Login successful for user: {db_username} (ID: {user_id})")
            
            # Show success message
            messagebox.showinfo("Login Success", f"🎉 Welcome {db_username}!\nOpening Life Manager Dashboard...")
            
            # Close database connection
            cursor.close()
            db.close()
            
            # Launch dashboard
            if launch_dashboard():
                print("✅ Dashboard launched successfully. Closing login window...")
                root.quit()  # Use quit() first
                root.destroy()  # Then destroy
            else:
                print("❌ Dashboard launch failed")
                if login_btn:
                    login_btn.config(state='normal', text="🚀 Login")
                
        else:
            messagebox.showerror("Login Failed", "❌ Invalid username or password!")
            login_password_entry.delete(0, END)
            login_username_entry.focus()
            if login_btn:
                login_btn.config(state='normal', text="🚀 Login")

    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"❌ Database error:\n{str(err)}")
        if login_btn:
            login_btn.config(state='normal', text="🚀 Login")
    except Exception as e:
        messagebox.showerror("Unexpected Error", f"❌ An unexpected error occurred:\n{str(e)}")
        if login_btn:
            login_btn.config(state='normal', text="🚀 Login")

# === Integrated Dashboard (Fallback) ===
def show_integrated_dashboard():
    """Show dashboard in same window if external file fails"""
    
    # Hide current frames
    try:
        registration_frame.pack_forget()
        login_frame.pack_forget()
    except:
        pass
    
    # Clear the root window
    for widget in root.winfo_children():
        widget.destroy()
    
    # Reconfigure root for dashboard
    root.title("🧠 Life Manager - Dashboard")
    root.geometry("900x700")
    root.configure(bg="#f8f9fc")
    
    # Try to maximize window
    try:
        root.state('zoomed')
    except:
        pass
    
    # Header
    header_frame = Frame(root, bg="#2c3e50", height=80)
    header_frame.pack(fill=X, pady=(0, 20))
    header_frame.pack_propagate(False)

    Label(header_frame, text="🧠 Life Manager Dashboard", font=("Segoe UI", 24, "bold"),
          bg="#2c3e50", fg="#ffffff").pack(pady=20)

    # Welcome message
    welcome_frame = Frame(root, bg="#e8f5e8", relief="raised", bd=1)
    welcome_frame.pack(fill=X, padx=40, pady=10)
    
    Label(welcome_frame, text="✨ Welcome to Life Manager! ✨", 
          font=("Segoe UI", 18, "bold"), bg="#e8f5e8", fg="#27ae60").pack(pady=10)
    Label(welcome_frame, text="Dashboard loaded successfully in integrated mode", 
          font=("Segoe UI", 12), bg="#e8f5e8", fg="#2c3e50").pack(pady=(0, 10))

    # Cards container
    cards_container = Frame(root, bg="#f8f9fc")
    cards_container.pack(expand=True, fill=BOTH, padx=20, pady=20)

    def create_card(parent, emoji, title, command, color):
        card_frame = Frame(parent, bg="#ffffff", relief="raised", bd=2)
        
        card = Button(card_frame, text=f"{emoji}\n{title}", width=18, height=8,
                      bg=color, fg="white", font=("Segoe UI", 12, "bold"),
                      relief="flat", bd=0, cursor="hand2", command=command,
                      wraplength=120, justify="center",
                      activebackground="#2c3e50", activeforeground="white")
        card.pack(padx=8, pady=8, fill=BOTH, expand=True)
        
        return card_frame

    def show_message(feature):
        messagebox.showinfo("Feature Coming Soon", f"🚀 {feature} module will be available soon!\n\nThis is the integrated dashboard fallback.")

    def logout_dashboard():
        result = messagebox.askyesno("Logout", "🔓 Are you sure you want to logout?")
        if result:
            root.quit()
            root.destroy()
            # Restart the auth app
            subprocess.Popen([sys.executable, __file__])

    # Create cards
    cards = [
        {"emoji": "✅", "title": "Tasks\nManagement", "command": lambda: show_message("Task Management"), "color": "#27ae60"},
        {"emoji": "💰", "title": "Expense\nTracker", "command": lambda: show_message("Expense Tracker"), "color": "#f39c12"},
        {"emoji": "🎯", "title": "Goal\nSetting", "command": lambda: show_message("Goal Setting"), "color": "#8e44ad"},
        {"emoji": "💊", "title": "Medication\nReminder", "command": lambda: show_message("Medication Reminder"), "color": "#16a085"},
        {"emoji": "📊", "title": "Analytics", "command": lambda: show_message("Analytics"), "color": "#3498db"},
        {"emoji": "⚙️", "title": "Settings", "command": lambda: show_message("Settings"), "color": "#34495e"},
        {"emoji": "📝", "title": "Notes", "command": lambda: show_message("Notes"), "color": "#e67e22"},
        {"emoji": "🔔", "title": "Notifications", "command": lambda: show_message("Notifications"), "color": "#9b59b6"},
        {"emoji": "🔓", "title": "Logout", "command": logout_dashboard, "color": "#c0392b"},
    ]

    # Grid layout (3 columns)
    for i, card_info in enumerate(cards):
        row = i // 3
        col = i % 3
        
        card = create_card(cards_container, card_info["emoji"], card_info["title"], 
                          card_info["command"], card_info["color"])
        card.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")

    # Configure grid weights
    for i in range(3):
        cards_container.columnconfigure(i, weight=1)
    for i in range(3):  # 3 rows for 9 cards
        cards_container.rowconfigure(i, weight=1)

    # Footer
    footer_frame = Frame(root, bg="#34495e", height=50)
    footer_frame.pack(fill=X, side=BOTTOM)
    footer_frame.pack_propagate(False)
    
    Label(footer_frame, text="💡 Integrated Dashboard Mode - dashboard.py not found or failed to launch", 
          font=("Segoe UI", 11), bg="#34495e", fg="#ecf0f1").pack(pady=5)
    Label(footer_frame, text="🔧 Place dashboard.py in the same folder for external dashboard", 
          font=("Segoe UI", 9), bg="#34495e", fg="#bdc3c7").pack()

def back_to_registration():
    login_frame.pack_forget()
    registration_frame.pack(fill="both", expand=True)

# === Main Window ===
root = Tk()
root.title("Life Manager - Registration")
root.geometry("450x550")
root.configure(bg="#ecf0f1")
root.resizable(False, False)

# Center window on screen
root.eval('tk::PlaceWindow . center')

# === Header ===
header = Frame(root, bg="#2c3e50", height=80)
header.pack(fill="x")
header.pack_propagate(False)

Label(header, text="🧠", font=("Helvetica", 32), 
      bg="#2c3e50", fg="white").pack(pady=5)
Label(header, text="Life Manager", font=("Helvetica", 18, "bold"), 
      bg="#2c3e50", fg="white").pack()

# === REGISTRATION FRAME (Main Page) ===
registration_frame = Frame(root, bg="#ecf0f1")
registration_frame.pack(fill="both", expand=True)

# Welcome message
welcome_frame = Frame(registration_frame, bg="#ffffff", relief="raised", bd=1)
welcome_frame.pack(fill="x", padx=30, pady=20)

Label(welcome_frame, text="📝 Create Your Account", font=("Helvetica", 20, "bold"), 
      bg="#ffffff", fg="#2c3e50").pack(pady=10)
Label(welcome_frame, text="Join Life Manager to organize your life efficiently", 
      font=("Helvetica", 11), bg="#ffffff", fg="#7f8c8d").pack(pady=(0, 10))

# Registration Form
form_container = Frame(registration_frame, bg="#ffffff", relief="raised", bd=2)
form_container.pack(fill="x", padx=30, pady=10)

Label(form_container, text="📋 Registration Form", font=("Helvetica", 16, "bold"),
      bg="#ffffff", fg="#2c3e50").pack(pady=15)

reg_form = Frame(form_container, bg="#ffffff")
reg_form.pack(pady=10, padx=20)

# Form Fields with improved styling
Label(reg_form, text="👤 Username:", bg="#ffffff", font=("Helvetica", 11, "bold"), 
      fg="#2c3e50").grid(row=0, column=0, sticky="w", pady=8, padx=(0, 10))
reg_username_entry = Entry(reg_form, width=25, font=("Helvetica", 11), 
                          relief="solid", bd=1, bg="#f8f9fa")
reg_username_entry.grid(row=0, column=1, pady=8, ipady=5)

Label(reg_form, text="📧 Email:", bg="#ffffff", font=("Helvetica", 11, "bold"), 
      fg="#2c3e50").grid(row=1, column=0, sticky="w", pady=8, padx=(0, 10))
reg_email_entry = Entry(reg_form, width=25, font=("Helvetica", 11), 
                       relief="solid", bd=1, bg="#f8f9fa")
reg_email_entry.grid(row=1, column=1, pady=8, ipady=5)

Label(reg_form, text="🔒 Password:", bg="#ffffff", font=("Helvetica", 11, "bold"), 
      fg="#2c3e50").grid(row=2, column=0, sticky="w", pady=8, padx=(0, 10))
reg_password_entry = Entry(reg_form, show="*", width=25, font=("Helvetica", 11), 
                          relief="solid", bd=1, bg="#f8f9fa")
reg_password_entry.grid(row=2, column=1, pady=8, ipady=5)

Label(reg_form, text="🔐 Confirm Password:", bg="#ffffff", font=("Helvetica", 11, "bold"), 
      fg="#2c3e50").grid(row=3, column=0, sticky="w", pady=8, padx=(0, 10))
reg_confirm_password_entry = Entry(reg_form, show="*", width=25, font=("Helvetica", 11), 
                                  relief="solid", bd=1, bg="#f8f9fa")
reg_confirm_password_entry.grid(row=3, column=1, pady=8, ipady=5)

# Password requirements
requirements_frame = Frame(form_container, bg="#ffffff")
requirements_frame.pack(pady=10)

Label(requirements_frame, text="💡 Password Requirements:", 
      bg="#ffffff", fg="#34495e", font=("Helvetica", 10, "bold")).pack(anchor=W)
Label(requirements_frame, text="• At least 6 characters long", 
      bg="#ffffff", fg="#7f8c8d", font=("Helvetica", 9)).pack(anchor=W)
Label(requirements_frame, text="• Use a strong, unique password", 
      bg="#ffffff", fg="#7f8c8d", font=("Helvetica", 9)).pack(anchor=W)

# Register Button
Button(form_container, text="✅ Create Account", bg="#27ae60", fg="white", width=25, 
       font=("Helvetica", 12, "bold"), command=register_user, relief="flat", 
       pady=10, cursor="hand2", activebackground="#229954").pack(pady=20)

# === LOGIN FRAME (Second Page) ===
login_frame = Frame(root, bg="#ecf0f1")

# Login welcome
login_welcome_frame = Frame(login_frame, bg="#ffffff", relief="raised", bd=1)
login_welcome_frame.pack(fill="x", padx=30, pady=20)

Label(login_welcome_frame, text="🔑 Welcome Back!", font=("Helvetica", 20, "bold"), 
      bg="#ffffff", fg="#2c3e50").pack(pady=10)
Label(login_welcome_frame, text="Please sign in to your Life Manager account", 
      font=("Helvetica", 11), bg="#ffffff", fg="#7f8c8d").pack(pady=(0, 10))

# Login Form
login_container = Frame(login_frame, bg="#ffffff", relief="raised", bd=2)
login_container.pack(fill="x", padx=30, pady=10)

Label(login_container, text="🚀 Sign In", font=("Helvetica", 16, "bold"),
      bg="#ffffff", fg="#2c3e50").pack(pady=15)

login_form = Frame(login_container, bg="#ffffff")
login_form.pack(pady=10, padx=20)

Label(login_form, text="👤 Username:", bg="#ffffff", font=("Helvetica", 11, "bold"), 
      fg="#2c3e50").grid(row=0, column=0, sticky="w", pady=10, padx=(0, 15))
login_username_entry = Entry(login_form, width=25, font=("Helvetica", 11), 
                            relief="solid", bd=1, bg="#f8f9fa")
login_username_entry.grid(row=0, column=1, pady=10, ipady=5)

Label(login_form, text="🔒 Password:", bg="#ffffff", font=("Helvetica", 11, "bold"), 
      fg="#2c3e50").grid(row=1, column=0, sticky="w", pady=10, padx=(0, 15))
login_password_entry = Entry(login_form, show="*", width=25, font=("Helvetica", 11), 
                            relief="solid", bd=1, bg="#f8f9fa")
login_password_entry.grid(row=1, column=1, pady=10, ipady=5)

# Login Buttons
login_button_frame = Frame(login_container, bg="#ffffff")
login_button_frame.pack(pady=15)

Button(login_button_frame, text="🚀 Login", bg="#3498db", fg="white", width=20, 
       font=("Helvetica", 12, "bold"), command=login_user, relief="flat", 
       pady=10, cursor="hand2", activebackground="#2980b9").pack(pady=5)

Label(login_container, text="Don't have an account?", 
      bg="#ffffff", fg="#7f8c8d", font=("Helvetica", 10)).pack(pady=5)

Button(login_container, text="📝 Back to Registration", command=back_to_registration, 
       bg="#95a5a6", fg="white", font=("Helvetica", 10, "bold"), relief="flat", 
       cursor="hand2", activebackground="#7f8c8d").pack(pady=5)

# === Enhanced Keyboard bindings ===
def on_register_enter(event):
    register_user()

def on_login_enter(event):
    login_user()

# Registration form navigation
reg_username_entry.bind("<Return>", lambda e: reg_email_entry.focus())
reg_email_entry.bind("<Return>", lambda e: reg_password_entry.focus())
reg_password_entry.bind("<Return>", lambda e: reg_confirm_password_entry.focus())
reg_confirm_password_entry.bind("<Return>", on_register_enter)

# Login form navigation
login_username_entry.bind("<Return>", lambda e: login_password_entry.focus())
login_password_entry.bind("<Return>", on_login_enter)

# Start with registration page and focus
reg_username_entry.focus()

# Footer
footer_frame = Frame(root, bg="#34495e", height=35)
footer_frame.pack(fill="x", side="bottom")
footer_frame.pack_propagate(False)

Label(footer_frame, text="🌟 Life Manager - Your Personal Life Organization System", 
      font=("Helvetica", 10), bg="#34495e", fg="#ecf0f1").pack(pady=8)

# Handle window close properly
def on_closing():
    if messagebox.askokcancel("Quit", "Do you want to quit Life Manager?"):
        root.quit()
        root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

# Start the application
if __name__ == "__main__":
    print("🚀 Starting Life Manager...")
    print(f"📁 Script location: {os.path.abspath(__file__)}")
    print(f"📂 Working directory: {os.getcwd()}")
    
    root.mainloop()