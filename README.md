**AI Health Companion
Welcome to the AI Health Companion, a full-stack web application designed to provide users with personalized 7-day diet and exercise plans. Powered by OpenAI, this application calculates a user's BMI and generates a comprehensive health plan tailored to their activity level, dietary preferences, and allergies, with a focus on authentic Andhra and Telangana cuisine.**

## ✨ Features
User Authentication: Secure user registration and login system.

Personalized Dashboard: A central hub for each user to track their progress and view their history.

AI-Powered Plan Generation: Creates a complete 7-day plan that includes:

Diet Plan: Detailed meal suggestions for breakfast, lunch, dinner, and snacks, complete with quantities and nutritional information.

Exercise Plan: A complementary weekly exercise routine.

Shopping List: An automatically generated, categorized grocery list.

Interactive Meal Options:

Swap Meals: Don't like a suggestion? Swap it for a nutritionally similar alternative.

View Recipes: Get cooking instructions for any dish in your plan.

Progress Tracking: Log your weight daily and visualize your progress over time with an interactive chart.

Enhanced Preferences: Customize your plan based on:

Dietary Choice (Vegetarian / Non-Vegetarian)

Common Allergies (Nuts, Gluten, etc.)

Dockerized Environment: The entire application is containerized using Docker and Docker Compose for easy setup and deployment.

**🛠️ Tech Stack**
Frontend: Streamlit

Backend: Python, Flask, Ariadne (for GraphQL)

Database: SQLite
AI: OpenAI GPT-3.5 Turbo

Containerization: Docker & Docker Compose

**🚀 Getting Started**
Follow these instructions to get the application running on your local machine.

**Prerequisites**
Docker: Make sure you have Docker installed and running on your system.

Docker Compose: This is typically included with Docker Desktop.

OpenAI API Key: You must have an API key from OpenAI.

Setup & Installation
Clone the Repository (or download the files):
Get all the project files into a single folder on your computer.

Create the Environment File:
In the root of the project folder, create a file named .env and add your OpenAI API key to it like this:

OPENAI_API_KEY="your_actual_openai_api_key_goes_here"

**Build and Run with Docker Compose:**
Open a terminal in the project's root directory and run the following command:

docker-compose up --build

This command will build the Docker images for the frontend and backend, create the necessary containers, and start the application.

**Access the Application:**
Once the containers are running, open your web browser and navigate to:
http://localhost:8501

You should now see the login page for the AI Health Companion.

Stopping the Application
To stop the application, press Ctrl + C in the terminal where Docker Compose is running. To remove the containers, run:

docker-compose down

**☁️ Deployment**
This application is ready to be deployed to a cloud server. Here are the general steps for a production launch:

Choose a Cloud Provider:
Select a cloud provider that supports Docker containers, such as DigitalOcean, AWS, or Google Cloud. A simple Virtual Private Server (VPS) is a great starting point.

**Set Up the Server**:

Provision a new server (e.g., an Ubuntu Droplet on DigitalOcean).

Install Docker and Docker Compose on the server.

**Transfer Project Files**:

Use Git to clone your repository onto the server. This is the recommended method as it makes updates easy.

Alternatively, you can use scp to securely copy your project files.

**Configure Environment Variables:**

On the server, create the .env file just as you did locally. Do not commit your .env file to Git. For production, it's even better to use the cloud provider's secret management service.

R**un the Application:**

Navigate to your project directory on the server and run the application in detached mode:

docker-compose up --build -d

The -d flag runs the containers in the background.

Configure DNS (Optional):

Point a domain name to your server's IP address so users can access your app at a friendly URL instead of an IP address.

**📁 File Structure**
.
├── data/                     # Persisted database is stored here
├── .env                      # Stores the secret API key (you must create this)
├── .gitignore                # Specifies files for Git to ignore
├── backend_server.py         # The Flask/GraphQL backend server
├── database_setup.py         # (Legacy) Script to initialize the database schema
├── Dockerfile.backend        # Docker instructions for the backend
├── Dockerfile.frontend       # Docker instructions for the frontend
├── docker-compose.yml        # Orchestrates the frontend and backend services
├── README.md                 # This file
├── requirements.txt          # Python libraries required for the project
├── startup.sh                # Ensures DB is ready before starting the backend
└── streamlit_app.py          # The Streamlit frontend application
