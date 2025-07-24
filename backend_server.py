# backend_server.py
# This version includes stricter AI instructions to ensure only
# Andhra & Telangana dishes are included in the diet plan.

import sqlite3
import json
import os
import hashlib
from flask import Flask, request, jsonify
from ariadne import QueryType, MutationType, make_executable_schema, gql, graphql_sync
from ariadne.explorer import ExplorerGraphiQL
import openai
from dotenv import load_dotenv

# --- Load Environment Variables ---
load_dotenv()

# --- OpenAI API Configuration ---
openai.api_key = os.getenv("OPENAI_API_KEY")

# --- Define Database Path ---
DATA_DIR = "data"
DB_PATH = os.path.join(DATA_DIR, "diet_planner.db")


# --- Database Initialization ---
def init_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Create 'users' table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Create 'user_progress' table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            weight_kg REAL NOT NULL,
            log_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(user_id, log_date)
        )
    ''')
    # Create 'diet_plans' table
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
            exercise_plan_json TEXT,
            shopping_list_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()
    print("Database initialized successfully.")


# --- Database Helper Functions ---
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# --- Password Hashing ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# --- GraphQL Schema Definition (SDL) ---
type_defs = gql("""
    scalar Date
    type Query { getUserDashboard(userId: ID!): UserDashboard }
    type Mutation {
        registerUser(username: String!, password: String!): AuthResponse
        loginUser(username: String!, password: String!): AuthResponse
        generateDietPlan(
            userId: ID!, weight: Float!, height: Float!, activityLevel: String!, 
            includeCheatMeal: Boolean!, dietaryPreference: String!, allergies: [String!]
        ): DietPlanResponse
        swapMeal(mealName: String!, dishToSwap: String!, dietaryPreference: String!): Meal
        getRecipe(dishName: String!): String
        logWeight(userId: ID!, weight: Float!, date: Date!): ProgressResponse
    }
    type AuthResponse { success: Boolean!, message: String, user: User }
    type User { id: ID!, username: String! }
    type ProgressEntry { weight_kg: Float!, log_date: Date! }
    type UserDashboard { pastPlans: [DietPlan!], progressHistory: [ProgressEntry!] }
    type Meal { name: String!, dish: String!, quantity: String!, nutrition: Nutrition! }
    type Nutrition { calories: Int!, protein_g: Int!, carbs_g: Int!, fat_g: Int! }
    type DayPlan { day: String!, daily_calories: Int!, meals: [Meal!]! }
    type Exercise { day: String!, activity: String! }
    type ShoppingList { category: String!, items: [String!]! }
    type Plan { diet: [DayPlan!]!, exercises: [Exercise!]!, shoppingList: [ShoppingList!]! }
    type DietPlan { 
        id: ID!, 
        created_at: String!, 
        weight_kg: Float!, 
        bmi: Float!, 
        dietary_preference: String!, 
        generated_plan: Plan! 
    }
    type DietPlanResponse { success: Boolean!, message: String, dietPlan: DietPlan }
    type ProgressResponse { success: Boolean!, message: String }
""")

# --- Ariadne Type Definitions ---
query = QueryType()
mutation = MutationType()

# --- Resolvers ---
@mutation.field("registerUser")
def resolve_register_user(_, info, username, password):
    conn = get_db_connection()
    try:
        conn.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hash_password(password)))
        conn.commit()
        user_data = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        return {"success": True, "message": "Registration successful!", "user": dict(user_data)}
    except sqlite3.IntegrityError:
        return {"success": False, "message": "Username already exists."}
    finally:
        conn.close()

@mutation.field("loginUser")
def resolve_login_user(_, info, username, password):
    conn = get_db_connection()
    user_data = conn.execute("SELECT * FROM users WHERE username = ? AND password_hash = ?", (username, hash_password(password))).fetchone()
    conn.close()
    if user_data:
        return {"success": True, "message": "Login successful!", "user": dict(user_data)}
    return {"success": False, "message": "Invalid username or password."}

@query.field("getUserDashboard")
def resolve_get_user_dashboard(_, info, userId):
    conn = get_db_connection()
    plans_cursor = conn.execute("SELECT * FROM diet_plans WHERE user_id = ? ORDER BY created_at DESC", (userId,))
    past_plans = []
    for row in plans_cursor.fetchall():
        plan_dict = dict(row)
        plan_dict['generated_plan'] = {
            'diet': json.loads(plan_dict['generated_plan_json']),
            'exercises': json.loads(plan_dict['exercise_plan_json']),
            'shoppingList': json.loads(plan_dict['shopping_list_json'])
        }
        past_plans.append(plan_dict)
    progress_cursor = conn.execute("SELECT weight_kg, log_date FROM user_progress WHERE user_id = ? ORDER BY log_date ASC", (userId,))
    progress_history = [dict(row) for row in progress_cursor.fetchall()]
    conn.close()
    return {"pastPlans": past_plans, "progressHistory": progress_history}

@mutation.field("logWeight")
def resolve_log_weight(_, info, userId, weight, date):
    conn = get_db_connection()
    try:
        conn.execute("INSERT OR REPLACE INTO user_progress (user_id, weight_kg, log_date) VALUES (?, ?, ?)", (userId, weight, date))
        conn.commit()
        return {"success": True, "message": "Weight logged successfully!"}
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        conn.close()

@mutation.field("generateDietPlan")
def resolve_generate_diet_plan(_, info, userId, weight, height, activityLevel, includeCheatMeal, dietaryPreference, allergies):
    if not openai.api_key:
         return {"success": False, "message": "OpenAI API key is not configured. Please check your .env file."}
    try:
        height_in_meters = height / 100
        bmi = round(weight / (height_in_meters * height_in_meters), 1)
        system_prompt = """
        You are an expert nutritionist and fitness coach specializing in South Indian cuisine. 
        Your task is to generate a comprehensive 7-day health plan.
        You MUST return a single, valid JSON object and nothing else. The JSON object must have three top-level keys: "diet", "exercises", and "shoppingList".
        The structure MUST be as follows:
        { "diet": [ { "day": "Monday", "daily_calories": integer, "meals": [ { "name": "Breakfast" | "Lunch" | "Snack" | "Dinner", "dish": "Dish Name", "quantity": "Serving size, e.g., '1 cup' or '2 rotis'", "nutrition": { "calories": integer, "protein_g": integer, "carbs_g": integer, "fat_g": integer } } ] } ], "exercises": [ { "day": "Monday", "activity": "Suggested activity, e.g., '30-minute brisk walk'" } ], "shoppingList": [ { "category": "e.g., Vegetables", "items": ["item1", "item2"] } ] }
        Do not include any text, explanations, or markdown formatting outside of this single JSON object.
        """
        allergies_text = f"The user is allergic to the following and these ingredients must be completely avoided: {', '.join(allergies)}." if allergies else "The user has no listed allergies."
        user_prompt = f"""
        Please generate a comprehensive 7-day health plan based on the following user details:
        - User BMI: {bmi}
        - Activity Level: '{activityLevel}'
        - Dietary Preference: '{dietaryPreference}'
        - Allergies: {allergies_text}
        - Include a cheat meal this week: {'Yes' if includeCheatMeal else 'No'}

        CRITICAL INSTRUCTION: All suggested dishes in the diet plan MUST be authentic and traditional dishes from the Andhra or Telangana regions of India. Do not include generic or North Indian dishes.

        Ensure the plan is balanced, varied, and appropriate for the user's profile.
        """
        completion = openai.chat.completions.create(model="gpt-3.5-turbo-1106", response_format={"type": "json_object"}, messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}])
        response_data = json.loads(completion.choices[0].message.content)
        if 'diet' not in response_data or 'exercises' not in response_data or 'shoppingList' not in response_data:
            raise KeyError("AI response is missing required keys.")
        diet_plan_json = json.dumps(response_data['diet'])
        exercise_plan_json = json.dumps(response_data['exercises'])
        shopping_list_json = json.dumps(response_data['shoppingList'])
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO diet_plans (user_id, weight_kg, height_cm, activity_level, dietary_preference, include_cheat_meal, bmi, generated_plan_json, exercise_plan_json, shopping_list_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (userId, weight, height, activityLevel, dietaryPreference, includeCheatMeal, bmi, diet_plan_json, exercise_plan_json, shopping_list_json)
        )
        new_plan_id = cursor.lastrowid
        conn.commit()
        new_plan_row = conn.execute("SELECT * FROM diet_plans WHERE id = ?", (new_plan_id,)).fetchone()
        conn.close()
        plan_dict = dict(new_plan_row)
        plan_dict['generated_plan'] = response_data
        return {"success": True, "message": "Comprehensive plan generated!", "dietPlan": plan_dict}
    except Exception as e:
        print(f"--- ERROR in generateDietPlan ---")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Details: {e}")
        print(f"---------------------------------")
        return {"success": False, "message": f"A server error occurred. Please check the backend logs for details."}

@mutation.field("swapMeal")
def resolve_swap_meal(_, info, mealName, dishToSwap, dietaryPreference):
    if not openai.api_key: return None
    try:
        system_prompt = f"""
        You are an expert nutritionist. Your task is to suggest an alternative for a single meal.
        You MUST return a single JSON object for the meal, with no other text.
        The required structure is: 
        {{
            "name": "{mealName}", 
            "dish": "New Dish Name", 
            "quantity": "New quantity", 
            "nutrition": {{ "calories": integer, "protein_g": integer, "carbs_g": integer, "fat_g": integer }}
        }}
        """
        user_prompt = f"""
        Suggest a different but nutritionally similar dish to replace '{dishToSwap}' for '{mealName}'.
        The new dish must be strictly '{dietaryPreference}'.
        CRITICAL INSTRUCTION: The new dish MUST be an authentic and traditional dish from the Andhra or Telangana regions of India.
        """
        completion = openai.chat.completions.create(
            model="gpt-3.5-turbo-1106", 
            response_format={"type": "json_object"}, 
            messages=[
                {"role": "system", "content": system_prompt}, 
                {"role": "user", "content": user_prompt}
            ]
        )
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        print(f"An unexpected error occurred during swap: {e}")
        return None

@mutation.field("getRecipe")
def resolve_get_recipe(_, info, dishName):
    if not openai.api_key: return "API key not configured."
    try:
        system_prompt = "You are a chef. Provide a simple, easy-to-follow recipe for the given dish. Return the recipe as a single string."
        user_prompt = f"What is the recipe for '{dishName}'?"
        completion = openai.chat.completions.create(model="gpt-3.5-turbo", messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}])
        return completion.choices[0].message.content
    except Exception as e:
        print(f"An unexpected error during recipe fetch: {e}")
        return "Sorry, I couldn't fetch the recipe at this time."

# --- Flask App Setup ---
app = Flask(__name__)
schema = make_executable_schema(type_defs, query, mutation)
explorer = ExplorerGraphiQL()

@app.route("/graphql", methods=["GET"])
def graphql_playground():
    return explorer.html(None), 200

@app.route("/graphql", methods=["POST"])
def graphql_server():
    data = request.get_json()
    success, result = graphql_sync(schema, data, context_value=request, debug=app.debug)
    status_code = 200 if success else 400
    return jsonify(result), status_code

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5001)
