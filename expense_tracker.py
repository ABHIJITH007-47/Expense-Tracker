import tkinter as tk
from tkinter import messagebox
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

# ---------------- DATABASE ----------------

conn = sqlite3.connect("expense_tracker.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
username TEXT PRIMARY KEY,
password TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS expenses(
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT,
category TEXT,
amount REAL,
type TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS budgets(
username TEXT PRIMARY KEY,
limit_amount REAL
)
""")

conn.commit()

current_user = None

# ---------------- LOGIN ----------------

def register():
    user = username_entry.get().strip()
    pwd = password_entry.get().strip()

    if not user or not pwd:
        messagebox.showwarning("Error", "Enter username & password")
        return

    try:
        cursor.execute("INSERT INTO users VALUES (?, ?)", (user, pwd))
        conn.commit()
        messagebox.showinfo("Success", "Account created!")
    except:
        messagebox.showerror("Error", "User already exists")

def login():
    global current_user

    user = username_entry.get().strip()
    pwd = password_entry.get().strip()

    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (user, pwd))
    if cursor.fetchone():
        current_user = user
        login_window.destroy()
        open_main_app()
    else:
        messagebox.showerror("Error", "Invalid login")

# ---------------- MAIN APP ----------------

def open_main_app():

    root = tk.Tk()
    root.title("Expense Tracker")
    root.geometry("450x750")

    # -------- SUMMARY FUNCTION --------

    def update_summary():
        cursor.execute(
            "SELECT SUM(amount) FROM expenses WHERE username=? AND type='Income'",
            (current_user,)
        )
        income = cursor.fetchone()[0] or 0

        cursor.execute(
            "SELECT SUM(amount) FROM expenses WHERE username=? AND type='Expense'",
            (current_user,)
        )
        expense = cursor.fetchone()[0] or 0

        balance = income - expense

        income_label.config(text=f"Total Income: ₹{income}")
        expense_label.config(text=f"Total Expense: ₹{expense}")
        balance_label.config(text=f"Balance: ₹{balance}")

        # Color change
        if balance >= 0:
            balance_label.config(fg="green")
        else:
            balance_label.config(fg="red")

    # -------- FUNCTIONS --------

    def update_display():
        display_box.delete(1.0, tk.END)

        cursor.execute("SELECT * FROM expenses WHERE username=?", (current_user,))
        rows = cursor.fetchall()

        if not rows:
            display_box.insert(tk.END, "No transactions yet\n")
        else:
            for r in rows:
                display_box.insert(
                    tk.END,
                    f"ID:{r[0]} | {r[4]} | {r[2]} | ₹{r[3]}\n"
                )

        update_summary()

    def check_budget():
        cursor.execute(
            "SELECT SUM(amount) FROM expenses WHERE username=? AND type='Expense'",
            (current_user,)
        )
        total = cursor.fetchone()[0] or 0

        cursor.execute(
            "SELECT limit_amount FROM budgets WHERE username=?",
            (current_user,)
        )
        result = cursor.fetchone()

        if result:
            budget = result[0]
            if total > budget:
                messagebox.showwarning(
                    "⚠ Budget Exceeded!",
                    f"Expense: ₹{total}\nBudget: ₹{budget}"
                )

    def add_entry():
        category = category_entry.get().strip()
        t_type = type_var.get()

        try:
            amount = float(amount_entry.get())
        except:
            messagebox.showerror("Error", "Enter valid amount")
            return

        if category == "":
            messagebox.showwarning("Error", "Enter category")
            return

        cursor.execute(
            "INSERT INTO expenses (username, category, amount, type) VALUES (?, ?, ?, ?)",
            (current_user, category, amount, t_type)
        )
        conn.commit()

        update_display()
        check_budget()

        category_entry.delete(0, tk.END)
        amount_entry.delete(0, tk.END)

    def delete_transaction():
        try:
            eid = int(delete_entry.get())
        except:
            messagebox.showerror("Error", "Enter valid ID")
            return

        cursor.execute(
            "DELETE FROM expenses WHERE id=? AND username=?",
            (eid, current_user)
        )
        conn.commit()

        update_display()
        delete_entry.delete(0, tk.END)

    def show_graph():
        cursor.execute("""
        SELECT type, SUM(amount)
        FROM expenses
        WHERE username=?
        GROUP BY type
        """, (current_user,))

        data = cursor.fetchall()

        if not data:
            messagebox.showwarning("No Data", "Nothing to show")
            return

        labels = [d[0] for d in data]
        values = [d[1] for d in data]

        plt.bar(labels, values)
        plt.title("Income vs Expense")
        plt.xlabel("Type")
        plt.ylabel("Amount")
        plt.show()

    def export_excel():
        df = pd.read_sql_query(
            "SELECT * FROM expenses WHERE username=?",
            conn,
            params=(current_user,)
        )
        df.to_excel(f"{current_user}_expenses.xlsx", index=False)
        messagebox.showinfo("Exported", "Excel saved")

    def set_budget():
        try:
            limit = float(budget_entry.get())
        except:
            messagebox.showerror("Error", "Enter valid budget")
            return

        cursor.execute(
            "INSERT OR REPLACE INTO budgets VALUES (?, ?)",
            (current_user, limit)
        )
        conn.commit()

        messagebox.showinfo("Success", f"Budget set: ₹{limit}")
        budget_entry.delete(0, tk.END)

    # -------- UI --------

    tk.Label(root, text=f"Welcome {current_user}", font=("Arial", 16)).pack(pady=10)

    # SUMMARY DISPLAY
    income_label = tk.Label(root, text="Total Income: ₹0", font=("Arial", 12))
    income_label.pack()

    expense_label = tk.Label(root, text="Total Expense: ₹0", font=("Arial", 12))
    expense_label.pack()

    balance_label = tk.Label(root, text="Balance: ₹0", font=("Arial", 14, "bold"))
    balance_label.pack(pady=5)

    tk.Label(root, text="Type").pack()
    type_var = tk.StringVar(value="Expense")
    tk.OptionMenu(root, type_var, "Expense", "Income").pack()

    tk.Label(root, text="Category").pack()
    category_entry = tk.Entry(root)
    category_entry.pack()

    tk.Label(root, text="Amount").pack()
    amount_entry = tk.Entry(root)
    amount_entry.pack()

    tk.Button(root, text="Add Entry", command=add_entry).pack(pady=5)
    tk.Button(root, text="Refresh", command=update_display).pack(pady=5)
    tk.Button(root, text="Show Graph", command=show_graph).pack(pady=5)
    tk.Button(root, text="Export Excel", command=export_excel).pack(pady=5)

    # Budget
    tk.Label(root, text="Set Budget").pack()
    budget_entry = tk.Entry(root)
    budget_entry.pack()
    tk.Button(root, text="Set Budget", command=set_budget).pack(pady=5)

    # Delete
    tk.Label(root, text="Delete by ID").pack()
    delete_entry = tk.Entry(root)
    delete_entry.pack()
    tk.Button(root, text="Delete", command=delete_transaction).pack(pady=5)

    # Display box
    frame = tk.Frame(root)
    frame.pack(pady=10)

    scrollbar = tk.Scrollbar(frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    display_box = tk.Text(
        frame,
        height=15,
        width=50,
        bg="black",
        fg="lime",
        insertbackground="white",
        yscrollcommand=scrollbar.set
    )
    display_box.pack()

    scrollbar.config(command=display_box.yview)

    update_display()

    tk.Button(root, text="Exit", command=root.quit).pack(pady=10)

    root.mainloop()

# ---------------- LOGIN WINDOW ----------------

login_window = tk.Tk()
login_window.title("Login System")
login_window.geometry("300x250")

tk.Label(login_window, text="Username").pack(pady=5)
username_entry = tk.Entry(login_window)
username_entry.pack()

tk.Label(login_window, text="Password").pack(pady=5)
password_entry = tk.Entry(login_window, show="*")
password_entry.pack()

tk.Button(login_window, text="Register", command=register).pack(pady=5)
tk.Button(login_window, text="Login", command=login).pack(pady=5)

login_window.mainloop()
 
