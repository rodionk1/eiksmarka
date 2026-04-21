PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS Workers (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS Raw_products (
    Raw_id INTEGER PRIMARY KEY AUTOINCREMENT,
    Raw_name_nor TEXT NOT NULL UNIQUE,
    Raw_name_rus TEXT,
    Raw_name_pl TEXT
);

CREATE TABLE IF NOT EXISTS Storage_raw (
    Raw_id INTEGER PRIMARY KEY,
    Unit TEXT NOT NULL CHECK(Unit IN ('stk', 'kg', 'g')),
    Quantity REAL NOT NULL DEFAULT 0,
    Min_quantity REAL NOT NULL DEFAULT 0,
    Price_pr_unit REAL NOT NULL DEFAULT 0,
    FOREIGN KEY(Raw_id) REFERENCES Raw_products(Raw_id)
);

CREATE TABLE IF NOT EXISTS Preps (
    Prep_id INTEGER PRIMARY KEY AUTOINCREMENT,
    Prep_name TEXT NOT NULL UNIQUE,
    Ingredients_prep TEXT NOT NULL DEFAULT '{}',
    Ingredients_raw TEXT NOT NULL DEFAULT '{}',
    Unit TEXT NOT NULL CHECK(Unit IN ('stk', 'kg', 'g')),
    Default_qty REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS Storage_prep (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Prep_id INTEGER NOT NULL,
    Quantity REAL NOT NULL,
    Unit TEXT NOT NULL CHECK(Unit IN ('stk', 'kg', 'g')),
    Made_date TEXT NOT NULL,
    Made_by INTEGER,
    FOREIGN KEY(Prep_id) REFERENCES Preps(Prep_id),
    FOREIGN KEY(Made_by) REFERENCES Workers(ID)
);

CREATE TABLE IF NOT EXISTS Products (
    Prod_id INTEGER PRIMARY KEY AUTOINCREMENT,
    Prod_name TEXT NOT NULL UNIQUE,
    Unit TEXT NOT NULL CHECK(Unit IN ('stk', 'kg', 'g')),
    Default_quantity REAL NOT NULL,
    Ingredients_prep TEXT NOT NULL DEFAULT '{}',
    Ingredients_raw TEXT NOT NULL DEFAULT '{}',
    Sales_price_pr_unit REAL NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS Storage_prod (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Prod_id INTEGER NOT NULL,
    Quantity REAL NOT NULL,
    Made_date TEXT NOT NULL,
    Made_by INTEGER,
    FOREIGN KEY(Prod_id) REFERENCES Products(Prod_id),
    FOREIGN KEY(Made_by) REFERENCES Workers(ID)
);

CREATE TABLE IF NOT EXISTS Kafe_2 (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Prod_id INTEGER NOT NULL,
    Quantity REAL NOT NULL,
    Made_date TEXT NOT NULL,
    Made_by INTEGER,
    FOREIGN KEY(Prod_id) REFERENCES Products(Prod_id),
    FOREIGN KEY(Made_by) REFERENCES Workers(ID)
);

CREATE TABLE IF NOT EXISTS Purchase (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Date TEXT NOT NULL,
    Contents TEXT NOT NULL,
    Purchase_type TEXT NOT NULL CHECK(Purchase_type IN ('raw', 'product')) DEFAULT 'raw',
    Made_by INTEGER,
    Control INTEGER NOT NULL DEFAULT 0,
    Accomplished INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS Activity (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Order_id INTEGER,
    Product_type TEXT NOT NULL CHECK(Product_type IN ('prep', 'prod')),
    Product_id INTEGER NOT NULL,
    Quantity REAL NOT NULL,
    Unit TEXT NOT NULL CHECK(Unit IN ('stk', 'kg', 'g')),
    Date TEXT NOT NULL,
    Control INTEGER NOT NULL DEFAULT 0,
    Accomplished INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY(Order_id) REFERENCES Orders(ID)
);

CREATE TABLE IF NOT EXISTS Customers (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Phone TEXT,
    Name TEXT,
    Email TEXT
);

CREATE TABLE IF NOT EXISTS Orders (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Customer_id INTEGER,
    Cafeteria TEXT NOT NULL CHECK(Cafeteria IN ('kafe_1', 'kafe_2')),
    Date TEXT NOT NULL,
    Delivery_date TEXT,
    Delivery_window TEXT NOT NULL DEFAULT 'morning' CHECK(Delivery_window IN ('morning', 'noon')),
    Status TEXT NOT NULL DEFAULT 'pending' CHECK(Status IN ('pending', 'produced', 'delivered')),
    Content TEXT NOT NULL,
    Warning TEXT,
    FOREIGN KEY(Customer_id) REFERENCES Customers(ID)
);
