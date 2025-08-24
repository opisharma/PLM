import tkinter as tk
from tkinter import messagebox
import subprocess
import hashlib
import os
import sys
from db_connect import connect_db

# === Database connection ===
# Use shared connection helper from db_connect.py to keep a single source of truth

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# === Dashboard launching function ===
def launch_dashboard(user_data=None):
    """Launch dashboard with user data"""
    try:
        # Method 1: Try to import and run dashboard directly
        try:
            import dashboard
            if hasattr(dashboard, "launch_dashboard"):
                dashboard.launch_dashboard(user_data)
                return True
            elif hasattr(dashboard, "main"):
                dashboard.main(user_data)
                return True
        except ImportError:
            pass
        
        # Method 2: Run dashboard as separate process
        script_dir = os.path.dirname(os.path.abspath(__file__))
        dashboard_path = os.path.join(script_dir, "dashboard.py")
        
        if os.path.exists(dashboard_path):
            # Pass user data as command line argument if needed
            if user_data:
                subprocess.Popen([
                    sys.executable, dashboard_path, 
                    f"--user_id={user_data.get('id', '')}"
                ], cwd=script_dir)
            else:
                subprocess.Popen([sys.executable, dashboard_path], cwd=script_dir)
            return True
        else:
            messagebox.showerror("Error", "dashboard.py file not found!")
            return False
            
    except Exception as e:
        messagebox.showerror("Dashboard Error", f"Failed to launch dashboard: {str(e)}")
        return False

# === Login function ===
def login():
    email = email_entry.get().strip()
    password = password_entry.get().strip()

    # Input validation
    if not email or not password:
        messagebox.showwarning("Validation Error", "⚠️ Email এবং Password দুটোই দিতে হবে!")
        return

    if len(password) < 6:
        messagebox.showwarning("Validation Error", "⚠️ Password কমপক্ষে ৬ অক্ষরের হতে হবে!")
        return

    # Disable login button during processing
    login_btn.config(state='disabled', text="Logging in...")
    root.update()

    db = None
    cursor = None
    try:
        db = connect_db()
        if db is None:
            messagebox.showerror("Database Connection Error", "Database connection failed. Please try again later.")
            return

        cursor = db.cursor()
        hashed_pw = hash_password(password)
        
        # Get user details by email
        query = "SELECT id, name, email FROM users WHERE email=%s AND password=%s"
        cursor.execute(query, (email, hashed_pw))
        result = cursor.fetchone()

        if result:
            # Create user data dictionary
            user_data = {
                'id': result[0],
                'name': result[1],
                'email': result[2] if len(result) > 2 else None,
            }
            
            messagebox.showinfo("Login Success", f"🎉 স্বাগতম {user_data.get('name') or user_data.get('email')}! Life Manager এ আপনাকে স্বাগতম!")
            
            # Launch dashboard
            if launch_dashboard(user_data):
                print(f"✅ Dashboard launched successfully for user: {user_data.get('email')}")
                root.quit()  # Use quit() instead of destroy() for better cleanup
                root.destroy()
            else:
                messagebox.showerror("Error", "Dashboard খুলতে সমস্যা হয়েছে!")
                
        else:
            messagebox.showerror("Login Failed", "❌ ভুল Email অথবা Password!")
            # Clear password field
            password_entry.delete(0, tk.END)
            email_entry.focus()

    except Exception as e:
        messagebox.showerror("Unexpected Error", f"An error occurred: {str(e)}")
    finally:
        # Re-enable login button
        login_btn.config(state='normal', text="Login")
        
        # Clean up database connections
        try:
            if cursor:
                cursor.close()
        except Exception:
            pass
        try:
            if db and db.is_connected():
                db.close()
                print("✅ Database connection closed")
        except Exception:
            pass

# === Enter key binding ===
def on_enter(event):
    login()

# === UI Setup ===
root = tk.Tk()
root.title("Login - Life Manager")
root.geometry("640x520")  # Match register.py window size
root.resizable(True, True)
root.configure(bg="#ecf0f1")

# Center the window
root.eval('tk::PlaceWindow . center')

# Header
header_frame = tk.Frame(root, bg="#3498db", height=60)
header_frame.pack(fill="x")
header_frame.pack_propagate(False)

tk.Label(header_frame, text="🔐 Life Manager Login", 
         font=("Segoe UI", 18, "bold"), 
         bg="#3498db", fg="white").pack(expand=True)

# Main content
main_frame = tk.Frame(root, bg="#ecf0f1")
main_frame.pack(expand=True, fill="both", padx=40, pady=30)

# Email field
tk.Label(main_frame, text="Email:", 
         font=("Segoe UI", 12), bg="#ecf0f1").pack(anchor="w")
email_entry = tk.Entry(main_frame, font=("Segoe UI", 12), width=30, 
                      relief="solid", borderwidth=1, bg="white")
email_entry.pack(pady=(5, 15), ipady=5)

# Password field  
tk.Label(main_frame, text="Password:", 
         font=("Segoe UI", 12), bg="#ecf0f1").pack(anchor="w")
password_entry = tk.Entry(main_frame, show="*", font=("Segoe UI", 12), width=30,
                         relief="solid", borderwidth=1, bg="white")
password_entry.pack(pady=(5, 25), ipady=5)

# Login button
login_btn = tk.Button(main_frame, text="Login", command=login,
                     bg="#3498db", fg="white", font=("Segoe UI", 12, "bold"), 
                     width=25, height=2, relief="flat",
                     activebackground="#2980b9", activeforeground="white",
                     cursor="hand2")
login_btn.pack(pady=10)

# Status label
status_label = tk.Label(main_frame, text="আপনার Email এবং Password দিন", 
                       font=("Segoe UI", 10), bg="#ecf0f1", fg="#7f8c8d")
status_label.pack(pady=10)

# Bind Enter key to login
root.bind('<Return>', on_enter)
password_entry.bind('<Return>', on_enter)
email_entry.bind('<Return>', on_enter)

# Focus on email entry
email_entry.focus()

# Handle window close
def on_closing():
    root.quit()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

# Start the GUI
if __name__ == "__main__":
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\n⚠️ Application interrupted by user")
    except Exception as e:
        print(f"❌ Application error: {e}")
    finally:
        try:
            root.destroy()
        except:
            pass