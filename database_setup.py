# database_setup.py
# Run this script once to create your new database structure.
# Make sure to delete any old 'diet_planner.db' file first.

import sqlite3
import hashlib # For basic password hashing

# --- Connect to SQLite database ---
conn = sqlite3.connect('diet_planner.db')
cursor = conn.cursor()

# --- 1. Create the 'users' table ---
# This table will store user login information.
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
print("Table 'users' created successfully.")

# --- 2. Create the 'user_progress' table ---
# This table will store daily weight entries for each user.
cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        weight_kg REAL NOT NULL,
        log_date DATE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
''')
print("Table 'user_progress' created successfully.")


# --- 3. Create the 'diet_plans' table (Updated) ---
# This table now links each plan to a user.
cursor.execute('''
    CREATE TABLE IF NOT EXISTS diet_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        weight_kg REAL NOT NULL,
        height_cm REAL NOT NULL,
        activity_level TEXT NOT NULL,
        dietary_preference TEXT NOT NULL,
        include_cheat_meal BOOLEAN NOT NULL,
        bmi REAL NOT NULL,
        generated_plan_json TEXT NOT NULL,
        exercise_plan_json TEXT, -- New column for exercises
        shopping_list_json TEXT, -- New column for shopping list
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
''')
print("Table 'diet_plans' updated successfully.")


# --- Commit the changes and close the connection ---
conn.commit()
conn.close()

print("\nDatabase 'diet_planner.db' and all tables created successfully.")
print("You can now run the new backend_server.py.")
