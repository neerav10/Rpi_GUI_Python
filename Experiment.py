import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import Calendar
from datetime import datetime
from dateutil.relativedelta import relativedelta
import math, random

# =================== Main Window ===================
root = tk.Tk()
root.title("High-End Multi-Tool Calculator")
root.geometry("1000x750")
root.minsize(950, 700)

# Make root grid expandable
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)

# ----------------- Global Variables -----------------
expression = ""
datetime1_str = tk.StringVar()
datetime2_str = tk.StringVar()
diff_text = tk.StringVar()

# ----------------- Frame Switching -----------------
def show_frame(frame):
    for f in (welcome_frame, calc_frame, date_frame):
        f.grid_forget()
    frame.grid(row=0, column=0, sticky="nsew")

# ----------------- Button Hover -----------------
def on_hover(e):
    e.widget['bg'] = '#ffd966'
def on_leave(e):
    e.widget['bg'] = e.widget.original_bg

# ================== Welcome Frame ===================
welcome_frame = tk.Frame(root, bg="#6a11cb")
welcome_frame.grid(row=0, column=0, sticky="nsew")
welcome_frame.grid_rowconfigure(0, weight=1)
welcome_frame.grid_rowconfigure(1, weight=1)
welcome_frame.grid_columnconfigure(0, weight=1)

tk.Label(welcome_frame, text="Welcome! Enter a Choice.",
         font=('Helvetica', 42, 'bold'), bg="#6a11cb", fg="white").grid(row=0, column=0, pady=60)

button_frame = tk.Frame(welcome_frame, bg="#6a11cb")
button_frame.grid(row=1, column=0)

def create_welcome_button(text, command, width, height, bg, fg):
    btn = tk.Button(button_frame, text=text, font=('Helvetica', 18, 'bold'),
                    bg=bg, fg=fg, width=width, height=height, relief='raised', bd=4, command=command)
    btn.original_bg = bg
    btn.bind("<Enter>", on_hover)
    btn.bind("<Leave>", on_leave)
    return btn

create_welcome_button("Standard Calculator", lambda: show_frame(calc_frame), 28, 4, "#3399ff", "white").grid(row=0, column=0, padx=20, pady=10)
create_welcome_button("Date & Time Calculator", lambda: show_frame(date_frame), 28, 4, "#ff33a0", "black").grid(row=1, column=0, padx=20, pady=10)

# ================== Standard Calculator Frame ===================
calc_frame = tk.Frame(root, bg="#f6f0ff")
calc_frame.grid(row=0, column=0, sticky="nsew")

# Grid configuration
for i in range(11):
    calc_frame.grid_rowconfigure(i, weight=1)
for i in range(7):
    calc_frame.grid_columnconfigure(i, weight=1)

header_calc = tk.Label(calc_frame, text="Standard Calculator", font=('Helvetica', 24, 'bold'),
                       bg="#d9b3ff", fg="#2a0a3d")
header_calc.grid(row=0, column=0, columnspan=7, pady=10, sticky="nsew")
def on_enter(e): header_calc.config(bg="#b366ff", fg="white")
def on_leave(e): header_calc.config(bg="#d9b3ff", fg="#2a0a3d")
header_calc.bind("<Enter>", on_enter)
header_calc.bind("<Leave>", on_leave)

entry = tk.Entry(calc_frame, font=('Consolas', 20, 'bold'), borderwidth=3,
                 relief='ridge', justify='right', bg="#ffffff", fg="#000000",
                 insertbackground="black")
entry.grid(row=1, column=0, columnspan=6, padx=5, pady=5, sticky="nsew")

# Control Functions
def press(num):
    global expression
    expression += str(num)
    entry.delete(0, tk.END)
    entry.insert(tk.END, expression)

def clear():
    global expression
    expression = ""
    entry.delete(0, tk.END)

def backspace():
    global expression
    expression = expression[:-1]
    entry.delete(0, tk.END)
    entry.insert(tk.END, expression)

def equalpress():
    global expression
    try:
        result = str(eval(expression, {"_builtins_": None},
                          {"sin": math.sin, "cos": math.cos, "tan": math.tan,
                           "log": math.log10, "ln": math.log, "sqrt": math.sqrt,
                           "pi": math.pi, "e": math.e, "pow": pow,
                           "factorial": math.factorial, "rand": random.random}))
        entry.delete(0, tk.END)
        entry.insert(tk.END, result)
        add_history(expression + " = " + result)
        expression = result
    except:
        messagebox.showerror("Error", "Invalid Input")
        expression = ""
        entry.delete(0, tk.END)

tk.Button(calc_frame, text='C', width=7, height=2, font=('Arial', 14, 'bold'),
          bg='#ff6666', fg='#000000', command=clear).grid(row=2, column=0, padx=3, pady=3, sticky="nsew")
tk.Button(calc_frame, text='⌫', width=7, height=2, font=('Arial', 14, 'bold'),
          bg='#ffa500', fg='#000000', command=backspace).grid(row=2, column=5, padx=3, pady=3, sticky="nsew")

# Buttons layout
buttons = [
    ['7','8','9','/','sin(','cos('],
    ['4','5','6','*','tan(','log('],
    ['1','2','3','-','ln(','√'],
    ['0','.','%','+','^','!'],
    ['π','e','rand()','(',')','=']
]
def make_button(b):
    if b == '=':
        cmd = equalpress
        bgc = '#66ff66'  # Distinct color for "=" button
        fgc = '#000000'
    elif b == '√':
        cmd = lambda t='sqrt(': press(t)
        bgc = '#e6ccff'
        fgc = '#000000'
    elif b == '^':
        cmd = lambda t='': press(t)
        bgc = '#e6ccff'
        fgc = '#000000'
    elif b == '!':
        cmd = lambda t='factorial(': press(t)
        bgc = '#e6ccff'
        fgc = '#000000'
    elif b == 'π':
        cmd = lambda t='pi': press(t)
        bgc = '#e6ccff'
        fgc = '#000000'
    elif b == 'e':
        cmd = lambda t='e': press(t)
        bgc = '#e6ccff'
        fgc = '#000000'
    else:
        cmd = lambda t=b: press(t)
        if b in '0123456789.':
            bgc = '#d9f0ff'  # Numeric
        elif b in '+-*/%^':
            bgc = '#ffe0b3'  # Operators
        else:
            bgc = '#e6ccff'  # Scientific
        fgc = '#000000'

    # Create button with fixed color (no hover/press change)
    btn = tk.Button(calc_frame, text=b, font=('Arial', 14, 'bold'),
                    bg=bgc, fg=fgc, relief='raised', bd=2,
                    activebackground=bgc, activeforeground=fgc,
                    command=cmd)
    return btn

for r, row in enumerate(buttons, start=3):
    for c, b in enumerate(row):
        make_button(b).grid(row=r, column=c, padx=2, pady=2, sticky="nsew")

# History panel
history_frame = tk.Frame(calc_frame, bg="#d9d9d9", relief='sunken', bd=2)
history_frame.grid(row=1, column=6, rowspan=7, sticky="nsew", padx=5, pady=5)
history_frame.grid_rowconfigure(0, weight=1)
history_frame.grid_columnconfigure(0, weight=1)
history_label = tk.Label(history_frame, text="History", font=('Arial', 12, 'bold'), bg="#d9d9d9")
history_label.pack(pady=5)
history_canvas = tk.Canvas(history_frame, bg="#f5f5f5")
history_scroll = tk.Scrollbar(history_frame, orient="vertical", command=history_canvas.yview)
scrollable_frame = tk.Frame(history_canvas, bg="#f5f5f5")
scrollable_frame.bind("<Configure>", lambda e: history_canvas.configure(scrollregion=history_canvas.bbox("all")))
history_canvas.create_window((0,0), window=scrollable_frame, anchor="nw")
history_canvas.configure(yscrollcommand=history_scroll.set)
history_canvas.pack(side="left", fill="both", expand=True)
history_scroll.pack(side="right", fill="y")
def add_history(msg):
    tk.Label(scrollable_frame, text=msg, anchor="w", bg="#f5f5f5", font=('Arial',12)).pack(fill="x", padx=2, pady=1)
    history_canvas.yview_moveto(1)

# Back menu
tk.Button(calc_frame, text="Back to Menu", font=('Arial', 16, 'bold'),
          bg="#999999", fg="white", command=lambda: show_frame(welcome_frame)).grid(row=10, column=6, sticky="e", padx=10, pady=5)

# ================== Date-Time Frame ===================
date_frame = tk.Frame(root, bg="#f0fff0")
date_frame.grid(row=0, column=0, sticky="nsew")
for i in range(6):
    date_frame.grid_columnconfigure(i, weight=1)
for i in range(5):
    date_frame.grid_rowconfigure(i, weight=1)

header_date = tk.Label(date_frame, text="Date & Time Difference Calculator", font=('Helvetica', 24, 'bold'),
                       bg="#66ff99", fg="#004d00")
header_date.grid(row=0, column=0, columnspan=6, pady=10, sticky="nsew")
def on_enter_date(e): header_date.config(bg="#33cc33", fg="white")
def on_leave_date(e): header_date.config(bg="#66ff99", fg="#004d00")
header_date.bind("<Enter>", on_enter_date)
header_date.bind("<Leave>", on_leave_date)

# Function to update entry with selected date & time
def update_datetime(entry_var, cal, hour, minute, second):
    selected_date = cal.get_date()
    full_dt = f"{selected_date} {int(hour.get()):02}:{int(minute.get()):02}:{int(second.get()):02}"
    entry_var.set(full_dt)

# Enlarged calendar frames (left and right)
for i, var_label in enumerate([datetime1_str, datetime2_str]):
    frame = tk.Frame(date_frame, bg="#f0fff0", bd=2, relief='groove')
    frame.grid(row=1, column=i*3, columnspan=3, padx=10, pady=10, sticky="nsew")
    frame.grid_rowconfigure(0, weight=0)
    frame.grid_rowconfigure(1, weight=0)
    frame.grid_rowconfigure(2, weight=1)
    frame.grid_rowconfigure(3, weight=0)
    frame.grid_columnconfigure(0, weight=1)

    ttk.Label(frame, text=f"Date & Time {i+1}:", background="#f0fff0", foreground="#000000",
              font=('Helvetica', 14, 'bold')).grid(row=0, column=0, pady=5)

    entry_dt = tk.Entry(frame, textvariable=var_label, width=25, bg="#ffffff", fg="#000000",
             insertbackground="black", font=('Helvetica', 14))
    entry_dt.grid(row=1, column=0, pady=5, sticky="ew")

    cal = Calendar(frame, selectmode='day', date_pattern='yyyy-mm-dd',
                   font=('Helvetica', 12), showweeknumbers=False, width=18, height=8)
    cal.grid(row=2, column=0, pady=5, sticky="nsew")

    time_frame = tk.Frame(frame, bg="#f0fff0")
    time_frame.grid(row=3, column=0, pady=5)
    hour = tk.Spinbox(time_frame, from_=0, to=23, width=3, font=('Helvetica',12), format="%02.0f")
    hour.pack(side="left", padx=5)
    minute = tk.Spinbox(time_frame, from_=0, to=59, width=3, font=('Helvetica',12), format="%02.0f")
    minute.pack(side="left", padx=5)
    second = tk.Spinbox(time_frame, from_=0, to=59, width=3, font=('Helvetica',12), format="%02.0f")
    second.pack(side="left", padx=5)

    ttk.Button(frame, text="Set Date & Time",
               command=lambda e=var_label, c=cal, h=hour, m=minute, s=second: update_datetime(e,c,h,m,s)).grid(row=4, column=0, pady=5, sticky="ew")

# Calculate difference
def calculate_difference():
    try:
        dt1 = datetime.strptime(datetime1_str.get(), "%Y-%m-%d %H:%M:%S")
        dt2 = datetime.strptime(datetime2_str.get(), "%Y-%m-%d %H:%M:%S")
        rd = relativedelta(dt2, dt1) if dt2 > dt1 else relativedelta(dt1, dt2)
        total_seconds = abs(int((dt2 - dt1).total_seconds()))
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        diff_text.set(f"{abs(rd.years)} year(s) {abs(rd.months)} month(s) {abs(rd.days)} day(s) {hours} hour(s) {minutes} minute(s) {seconds} second(s)")
    except:
        diff_text.set("Error: Invalid date/time")

ttk.Button(date_frame, text="Calculate Difference", command=calculate_difference).grid(row=2, column=1, columnspan=4, pady=10, sticky="nsew")
ttk.Label(date_frame, textvariable=diff_text, font=('Helvetica', 12, 'bold'),
          background="#f0fff0", foreground="#008000").grid(row=3, column=0, columnspan=6, pady=10, sticky="nsew")
tk.Button(date_frame, text="Back to Menu", font=('Arial', 16, 'bold'),
          bg="#999999", fg="white", command=lambda: show_frame(welcome_frame)).grid(row=4, column=5, sticky="e", padx=10, pady=10)

# Start with Welcome Frame
show_frame(welcome_frame)
root.mainloop()