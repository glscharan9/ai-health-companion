# streamlit_app.py
# This version includes a complete visual overhaul with custom CSS for a vibrant UI.

import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime

# --- Configuration ---
GRAPHQL_API_URL = "https://your-live-backend-url.com/graphql"
# --- Custom CSS for Vibrant UI ---
def local_css():
    st.markdown("""
        <style>
            /* --- Main Background --- */
            .stApp {
                background-image: linear-gradient(to top right, #ff7e5f, #feb47b);
                background-attachment: fixed;
                background-size: cover;
            }

            /* --- Main Content Area --- */
            [data-testid="stAppViewContainer"] > .main {
                background-color: rgba(255, 255, 255, 0.8);
                backdrop-filter: blur(10px);
                padding: 2rem;
                border-radius: 20px;
                margin: 1rem;
            }

            /* --- Sidebar --- */
            [data-testid="stSidebar"] {
                background-color: rgba(255, 255, 255, 0.7);
                backdrop-filter: blur(5px);
                border-right: 1px solid rgba(255, 255, 255, 0.2);
            }
            
            /* --- Buttons --- */
            .stButton > button {
                background-image: linear-gradient(to right, #ff6a00 0%, #ee0979 100%);
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 10px;
                font-weight: bold;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px 0 rgba(252, 109, 69, 0.75);
            }
            .stButton > button:hover {
                background-position: right center;
                box-shadow: 0 8px 25px 0 rgba(252, 109, 69, 0.9);
                transform: translateY(-2px);
            }
            .stButton > button:active {
                transform: translateY(1px);
            }

            /* --- Form Submit Button --- */
            .stForm [data-testid="stFormSubmitButton"] button {
                background-image: linear-gradient(to right, #1d976c 0%, #93f9b9 100%);
                box-shadow: 0 4px 15px 0 rgba(29, 151, 108, 0.75);
            }
             .stForm [data-testid="stFormSubmitButton"] button:hover {
                box-shadow: 0 8px 25px 0 rgba(29, 151, 108, 0.9);
             }

            /* --- Containers & Expanders --- */
            [data-testid="stExpander"], [data-testid="stContainer"] {
                border-radius: 15px;
                border: 1px solid rgba(0,0,0,0.1);
                box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            }
            
            /* --- Headers and Titles --- */
            h1, h2, h3 {
                color: #D35400; /* A deep orange color */
            }

        </style>
    """, unsafe_allow_html=True)


# --- GraphQL Helper ---
def graphql_request(query, variables=None):
    """A simple helper to send GraphQL requests."""
    try:
        response = requests.post(GRAPHQL_API_URL, json={'query': query, 'variables': variables or {}})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Network Error: Could not connect to the backend. Is it running? Details: {e}")
        return None

# --- Reusable Component to Display a Plan ---
def display_plan_details(plan_data, dietary_preference):
    """A reusable function to display the full details of any plan."""
    st.info(f"Showing details for plan generated on {datetime.fromisoformat(plan_data['created_at']).strftime('%B %d, %Y at %I:%M %p')}")
    
    diet_tab, exercise_tab, shopping_tab = st.tabs(["🥗 Diet Plan", "🏃‍♂️ Exercise Plan", "🛒 Shopping List"])

    with diet_tab:
        plan_session_key = f"diet_plan_{plan_data['id']}"
        if plan_session_key not in st.session_state:
            st.session_state[plan_session_key] = plan_data['generated_plan']['diet']

        if not st.session_state[plan_session_key]:
            st.warning("No diet plan was generated for this entry.")
            return
            
        for day_index, day in enumerate(st.session_state[plan_session_key]):
            with st.container(border=True):
                st.markdown(f"**{day['day']}** ({day.get('daily_calories', 0):,} kcal)")
                for meal_index, meal in enumerate(day['meals']):
                    col1, col2, col3 = st.columns([4, 1, 1])
                    with col1:
                        st.markdown(f"**{meal['name']}:** {meal['dish']} - *({meal['quantity']})*")
                        st.caption(f"🔥 {meal['nutrition']['calories']} kcal | 💪 {meal['nutrition']['protein_g']}g P | 🍞 {meal['nutrition']['carbs_g']}g C | 🥑 {meal['nutrition']['fat_g']}g F")
                    with col2:
                        if st.button("Swap", key=f"swap_{plan_data['id']}_{day_index}_{meal_index}"):
                            with st.spinner("Finding a replacement..."):
                                swap_query = "mutation Swap($m: String!, $d: String!, $p: String!) { swapMeal(mealName: $m, dishToSwap: $d, dietaryPreference: $p) { name dish quantity nutrition { calories protein_g carbs_g fat_g } } }"
                                new_meal = graphql_request(swap_query, {"m": meal['name'], "d": meal['dish'], "p": dietary_preference})
                                if new_meal and new_meal.get('data') and new_meal['data'].get('swapMeal'):
                                    st.session_state[plan_session_key][day_index]['meals'][meal_index] = new_meal['data']['swapMeal']
                                    st.rerun()
                                else:
                                    st.error("Could not swap meal.")
                    with col3:
                        if st.button("Recipe", key=f"recipe_{plan_data['id']}_{day_index}_{meal_index}"):
                            with st.spinner(f"Getting recipe for {meal['dish']}..."):
                                recipe_query = "mutation GetRecipe($dish: String!) { getRecipe(dishName: $dish) }"
                                recipe_result = graphql_request(recipe_query, {"dish": meal['dish']})
                                if recipe_result and recipe_result.get('data') and recipe_result['data'].get('getRecipe'):
                                    st.info(f"**Recipe for {meal['dish']}**\n\n" + recipe_result['data']['getRecipe'])
                                else:
                                    st.error("Could not fetch recipe.")

    with exercise_tab:
        if not plan_data['generated_plan']['exercises']:
            st.warning("No exercise plan was generated for this entry.")
            return
        for exercise in plan_data['generated_plan']['exercises']:
            st.markdown(f"**{exercise['day']}:** {exercise['activity']}")

    with shopping_tab:
        if not plan_data['generated_plan']['shoppingList']:
            st.warning("No shopping list was generated for this entry.")
            return
        for category in plan_data['generated_plan']['shoppingList']:
            st.markdown(f"##### {category['category']}")
            for item in category['items']:
                st.markdown(f"- {item}")

# --- Page 1: Login & Registration ---
def login_page():
    st.header("Welcome to your AI Health Companion")
    
    login_tab, register_tab = st.tabs(["Login", "Register"])

    with login_tab:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            if submitted:
                query = """
                    mutation LoginUser($username: String!, $password: String!) {
                        loginUser(username: $username, password: $password) {
                            success message user { id username }
                        }
                    }
                """
                result = graphql_request(query, {"username": username, "password": password})
                if result and result.get('data') and result['data']['loginUser']['success']:
                    st.session_state.logged_in = True
                    st.session_state.user = result['data']['loginUser']['user']
                    st.session_state.page = "dashboard"
                    st.rerun()
                else:
                    message = "Login failed."
                    if result and result.get('data'):
                        message = result['data']['loginUser']['message']
                    st.error(message)

    with register_tab:
        with st.form("register_form"):
            username = st.text_input("Choose a Username")
            password = st.text_input("Choose a Password", type="password")
            submitted = st.form_submit_button("Register")
            if submitted:
                query = """
                    mutation RegisterUser($username: String!, $password: String!) {
                        registerUser(username: $username, password: $password) {
                            success message user { id username }
                        }
                    }
                """
                result = graphql_request(query, {"username": username, "password": password})
                if result and result.get('data') and result['data']['registerUser']['success']:
                    st.success("Registration successful! Please login.")
                else:
                    message = "Registration failed."
                    if result and result.get('data'):
                        message = result['data']['registerUser']['message']
                    st.error(message)

# --- Page 2: User Dashboard (History & Progress) ---
def dashboard_page():
    st.title(f"Welcome, {st.session_state.user['username']}!")

    query = """
        query GetUserDashboard($userId: ID!) {
            getUserDashboard(userId: $userId) {
                progressHistory { weight_kg log_date }
                pastPlans { 
                    id created_at weight_kg bmi dietary_preference
                    generated_plan { 
                        diet { day daily_calories meals { name dish quantity nutrition { calories protein_g carbs_g fat_g } } }
                        exercises { day activity }
                        shoppingList { category items }
                    } 
                }
            }
        }
    """
    result = graphql_request(query, {"userId": st.session_state.user['id']})

    if not result or not result.get('data') or not result['data'].get('getUserDashboard'):
        st.warning("Could not load your dashboard data.")
        return

    dashboard_data = result['data']['getUserDashboard']
    progress_history = dashboard_data.get('progressHistory', [])
    past_plans = dashboard_data.get('pastPlans', [])

    # --- Progress Tracking Section ---
    st.header("Your Progress")
    with st.container(border=True):
        col1, col2 = st.columns([1, 2])
        with col1:
            with st.form("log_weight_form"):
                st.markdown("##### Log Today's Weight")
                weight = st.number_input("Weight (kg)", min_value=30.0, value=70.0, step=0.1, format="%.1f")
                log_date = st.date_input("Date", datetime.today())
                submitted = st.form_submit_button("Log Weight")
                if submitted:
                    log_query = "mutation LogWeight($userId: ID!, $weight: Float!, $date: Date!) { logWeight(userId: $userId, weight: $weight, date: $date) { success message } }"
                    log_result = graphql_request(log_query, {"userId": st.session_state.user['id'], "weight": weight, "date": str(log_date)})
                    if log_result and log_result['data']['logWeight']['success']:
                        st.success("Weight logged!")
                        st.session_state.viewing_plan_id = None
                        st.rerun()
                    else:
                        st.error("Failed to log weight.")

        with col2:
            if progress_history:
                df = pd.DataFrame(progress_history)
                df['log_date'] = pd.to_datetime(df['log_date'])
                df = df.set_index('log_date')
                st.line_chart(df, y="weight_kg", color="#ff6a00")
            else:
                st.info("Log your weight to see your progress chart here!")

    st.divider()

    # --- History Section ---
    st.header("Your Past Plans")
    if not past_plans:
        st.info("You haven't generated any plans yet. Go to the Planner to create one!")
    else:
        for plan in past_plans:
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    plan_date = datetime.fromisoformat(plan['created_at']).strftime('%B %d, %Y')
                    st.subheader(f"Plan from {plan_date}")
                    st.caption(f"Generated with weight: {plan['weight_kg']} kg | BMI: {plan['bmi']} | Preference: {plan['dietary_preference']}")
                with col2:
                    st.write("") # Spacer
                    if st.button("View Details", key=f"view_{plan['id']}"):
                        st.session_state.viewing_plan_id = plan['id']
                        
    st.divider()
    
    # --- Detailed Plan Viewer ---
    if 'viewing_plan_id' in st.session_state and st.session_state.viewing_plan_id:
        selected_plan = next((p for p in past_plans if p['id'] == st.session_state.viewing_plan_id), None)
        if selected_plan:
            with st.container(border=True):
                st.header("Viewing Past Plan")
                display_plan_details(selected_plan, selected_plan['dietary_preference']) 
                if st.button("Close Details"):
                    st.session_state.viewing_plan_id = None
                    st.rerun()

# --- Page 3: The Main Planner ---
def planner_page():
    st.title("Generate a New Health Plan")

    with st.form("diet_form"):
        st.subheader("1. Your Details")
        col1, col2 = st.columns(2)
        with col1:
            weight = st.number_input("Current Weight (kg)", min_value=30.0, value=70.0, step=0.5)
        with col2:
            height = st.number_input("Height (cm)", min_value=100.0, value=175.0, step=0.5)

        st.subheader("2. Your Preferences")
        dietary_preference = st.radio("Dietary Preference", ("Vegetarian", "Non-Vegetarian"), horizontal=True)
        allergies = st.multiselect("Any Allergies?", ["Nuts", "Gluten", "Lactose", "Shellfish"])
        
        st.subheader("3. Your Activity")
        activity_level = st.selectbox("Daily Activity Level", ("Sedentary", "Lightly Active", "Moderately Active", "Very Active"), index=2)
        include_cheat_meal = st.checkbox("Include a cheat meal this week?")
        
        submitted = st.form_submit_button("✨ Generate My Plan")

    if submitted:
        for key in list(st.session_state.keys()):
            if key.startswith("diet_plan_"):
                del st.session_state[key]
        with st.spinner("Your personal AI chef and trainer are crafting the perfect plan..."):
            query = """
                mutation GeneratePlan($userId: ID!, $weight: Float!, $height: Float!, $activityLevel: String!, $includeCheatMeal: Boolean!, $dietaryPreference: String!, $allergies: [String!]) {
                    generateDietPlan(userId: $userId, weight: $weight, height: $height, activityLevel: $activityLevel, includeCheatMeal: $includeCheatMeal, dietaryPreference: $dietaryPreference, allergies: $allergies) {
                        success message dietPlan { id created_at bmi dietary_preference generated_plan {
                            diet { day daily_calories meals { name dish quantity nutrition { calories protein_g carbs_g fat_g } } }
                            exercises { day activity }
                            shoppingList { category items }
                        }}
                    }
                }
            """
            variables = {
                "userId": st.session_state.user['id'], "weight": weight, "height": height, 
                "activityLevel": activity_level, "includeCheatMeal": include_cheat_meal,
                "dietaryPreference": dietary_preference, "allergies": allergies
            }
            result = graphql_request(query, variables)
            if result and result.get('data') and result['data']['generateDietPlan']['success']:
                st.session_state.generated_plan = result['data']['generateDietPlan']['dietPlan']
                st.session_state.viewing_plan_id = None
            else:
                st.error("Failed to generate plan.")
                st.session_state.generated_plan = None

    # --- Display Newly Generated Plan ---
    if 'generated_plan' in st.session_state and st.session_state.generated_plan:
        plan_data = st.session_state.generated_plan
        st.header("Your New Plan is Ready!")

        bmi = plan_data['bmi']
        bmi_category = ""
        if bmi < 18.5: bmi_category = "Underweight"
        elif 18.5 <= bmi < 25: bmi_category = "Normal weight"
        elif 25 <= bmi < 30: bmi_category = "Overweight"
        else: bmi_category = "Obesity"
        st.metric(label="Your Calculated BMI for this Plan", value=f"{bmi}", delta=bmi_category)
        st.divider()
        
        display_plan_details(plan_data, plan_data['dietary_preference'])


# --- Main App Router ---
def main():
    st.set_page_config(page_title="AI Health Companion", layout="wide")
    local_css() # Apply custom styles

    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.user = None
        st.session_state.page = "login"
        st.session_state.generated_plan = None
        st.session_state.viewing_plan_id = None

    if st.session_state.logged_in:
        with st.sidebar:
            st.header(f"👤 {st.session_state.user['username']}")
            if st.button("My Dashboard"):
                st.session_state.page = "dashboard"
                st.session_state.generated_plan = None
                st.rerun()
            if st.button("New Health Plan"):
                st.session_state.page = "planner"
                st.rerun()
            if st.button("Logout"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

    if not st.session_state.logged_in:
        login_page()
    elif st.session_state.page == "dashboard":
        dashboard_page()
    elif st.session_state.page == "planner":
        planner_page()

if __name__ == "__main__":
    main()
