import tkinter as tk
from tkinter import messagebox

def calculate(operation):
    try:
        num1 = float(entry1.get())
        num2 = float(entry2.get())

        if operation == '+':
            result = num1 + num2
        elif operation == '-':
            result = num1 - num2
        elif operation == '*':
            result = num1 * num2
        elif operation == '/':
            result = num1 / num2

        result_label.config(text=f"Result: {result}")

    except ValueError:
        messagebox.showerror("Input Error", "Please enter valid numbers.")
    except ZeroDivisionError:
        messagebox.showerror("Math Error", "Cannot divide by zero.")

# Create the main window
root = tk.Tk()
root.title("Simple GUI Calculator")

# Input fields
entry1 = tk.Entry(root, width=10)
entry1.grid(row=0, column=0, padx=10, pady=10)

entry2 = tk.Entry(root, width=10)
entry2.grid(row=0, column=1, padx=10, pady=10)

# Operation buttons
button_add = tk.Button(root, text="+", width=5, command=lambda: calculate('+'), bg="red")
button_add.grid(row=1, column=0, pady=5)

button_subtract = tk.Button(root, text="-", width=5, command=lambda: calculate('-'))
button_subtract.grid(row=1, column=1, pady=5)

button_multiply = tk.Button(root, text="*", width=5, command=lambda: calculate('*'))
button_multiply.grid(row=2, column=0, pady=5)

button_divide = tk.Button(root, text="/", width=5, command=lambda: calculate('/'))
button_divide.grid(row=2, column=1, pady=5)

# Result label
result_label = tk.Label(root, text="Result: ", font=("Arial", 14))
result_label.grid(row=3, column=0, columnspan=2, pady=10)

# Run the GUI
root.mainloop()
