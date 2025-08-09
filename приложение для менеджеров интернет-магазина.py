# main.py
import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import re
import json
import csv

# models.py
class Customer:
    """Класс для представления клиента."""
    def __init__(self, name, email, phone, address):
        self.name = name
        self.email = email
        self.phone = phone
        self.address = address

    def validate(self):
        """Проверяет корректность данных клиента."""
        if not re.match(r"[^@]+@[^@]+\.[^@]+", self.email):
            return False
        if not re.match(r"\+?\d[\d -]{8,}\d", self.phone):
            return False
        return True

class Product:
    """Класс для представления товара."""
    def __init__(self, name, price):
        self.name = name
        self.price = price

class Order:
    """Класс для представления заказа."""
    def __init__(self, customer, products, date):
        self.customer = customer
        self.products = products
        self.date = date

    def total_cost(self):
        """Возвращает общую стоимость заказа."""
        return sum(product.price for product in self.products)

# db.py
class Database:
    """Класс для работы с базой данных SQLite."""
    def __init__(self, db_name="orders.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        """Создает таблицы в базе данных."""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                email TEXT,
                phone TEXT,
                address TEXT
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                price REAL
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                date TEXT,
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                product_id INTEGER,
                FOREIGN KEY (order_id) REFERENCES orders(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)
        self.conn.commit()

    def add_customer(self, customer):
        """Добавляет клиента в базу данных."""
        self.cursor.execute("""
            INSERT INTO customers (name, email, phone, address)
            VALUES (?, ?, ?, ?)
        """, (customer.name, customer.email, customer.phone, customer.address))
        self.conn.commit()

    def add_order(self, order):
        """Добавляет заказ в базу данных."""
        self.cursor.execute("""
            INSERT INTO orders (customer_id, date)
            VALUES (?, ?)
        """, (self.get_customer_id(order.customer), order.date))
        order_id = self.cursor.lastrowid
        for product in order.products:
            self.cursor.execute("""
                INSERT INTO order_items (order_id, product_id)
                VALUES (?, ?)
            """, (order_id, self.get_product_id(product)))
        self.conn.commit()

    def get_customer_id(self, customer):
        """Возвращает ID клиента по его данным."""
        self.cursor.execute("""
            SELECT id FROM customers WHERE email = ?
        """, (customer.email,))
        return self.cursor.fetchone()[0]

    def get_product_id(self, product):
        """Возвращает ID товара по его данным."""
        self.cursor.execute("""
            SELECT id FROM products WHERE name = ? AND price = ?
        """, (product.name, product.price))
        return self.cursor.fetchone()[0]

    def export_to_csv(self, table_name, filename):
        """Экспортирует данные из таблицы в CSV."""
        self.cursor.execute(f"SELECT * FROM {table_name}")
        rows = self.cursor.fetchall()
        with open(filename, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([description[0] for description in self.cursor.description])
            writer.writerows(rows)

    def import_from_csv(self, table_name, filename):
        """Импортирует данные из CSV в таблицу."""
        with open(filename, 'r') as file:
            reader = csv.reader(file)
            next(reader)  # Пропуск заголовка
            for row in reader:
                self.cursor.execute(f"INSERT INTO {table_name} VALUES (?, ?, ?, ?)", row)
        self.conn.commit()

# gui.py
class GUI:
    """Класс для графического интерфейса."""
    def __init__(self, db):
        self.db = db
        self.root = tk.Tk()
        self.root.title("Система учёта заказов")
        self.create_widgets()

    def create_widgets(self):
        """Создает виджеты для интерфейса."""
        # Добавление клиента
        self.name_label = tk.Label(self.root, text="Имя:")
        self.name_label.grid(row=0, column=0)
        self.name_entry = tk.Entry(self.root)
        self.name_entry.grid(row=0, column=1)

        self.email_label = tk.Label(self.root, text="Email:")
        self.email_label.grid(row=1, column=0)
        self.email_entry = tk.Entry(self.root)
        self.email_entry.grid(row=1, column=1)

        self.phone_label = tk.Label(self.root, text="Телефон:")
        self.phone_label.grid(row=2, column=0)
        self.phone_entry = tk.Entry(self.root)
        self.phone_entry.grid(row=2, column=1)

        self.address_label = tk.Label(self.root, text="Адрес:")
        self.address_label.grid(row=3, column=0)
        self.address_entry = tk.Entry(self.root)
        self.address_entry.grid(row=3, column=1)

        self.add_customer_button = tk.Button(self.root, text="Добавить клиента", command=self.add_customer)
        self.add_customer_button.grid(row=4, column=0, columnspan=2)

    def add_customer(self):
        """Добавляет клиента."""
        name = self.name_entry.get()
        email = self.email_entry.get()
        phone = self.phone_entry.get()
        address = self.address_entry.get()
        customer = Customer(name, email, phone, address)
        if customer.validate():
            self.db.add_customer(customer)
            messagebox.showinfo("Успех", "Клиент успешно добавлен!")
        else:
            messagebox.showerror("Ошибка", "Некорректные данные клиента!")

    def run(self):
        """Запускает основной цикл интерфейса."""
        self.root.mainloop()

# analysis.py
def plot_sales(db):
    """Строит график динамики продаж."""
    df = pd.read_sql_query("SELECT date, COUNT(*) as orders FROM orders GROUP BY date", db.conn)
    df.plot(x='date', y='orders', kind='bar')
    plt.show()

# main.py
if __name__ == "__main__":
    db = Database()
    gui = GUI(db)
    gui.run()