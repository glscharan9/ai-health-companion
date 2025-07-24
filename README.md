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
