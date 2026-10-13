# Campus-Bot 

CampusMind
A full-stack AI chatbot and voice assistant platform designed to modernize campus web portals. CampusMind leverages a hybrid Retrieval-Augmented Generation (RAG) architecture to provide contextual, real-time assistance, integrating voice capabilities and location-aware services for students and faculty.

🌟 Core Features
Real-Time Voice Assistant: Streams audio interactions seamlessly between the client and server using WebSockets for a natural conversational experience.

Hybrid RAG Architecture: Combines vector-based search and keyword retrieval to accurately surface campus policies, schedules, and academic information.

Geospatial Intelligence: Utilizes PostGIS to handle campus location queries, intelligent routing, and spatial data tasks.

Feedback Logging: Captures and stores user interactions to continually evaluate and improve response quality.

🛠️ Tech Stack
Frontend: React.js, Next.js

Backend: FastAPI

Database: PostgreSQL with PostGIS extensions

Infrastructure & Deployment: Docker, Git

🚀 Getting Started
Prerequisites
Node.js & npm (for the frontend)

Python 3.10+ (for the backend)

PostgreSQL with PostGIS enabled

Installation
1. Clone the repository:

Bash
git clone https://github.com/sanjaykumar7539/Campus-Bot.git
cd Campus-Bot
2. Backend Setup (FastAPI):

Bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
pip install -r requirements.txt
3. Frontend Setup (Next.js):

Bash
cd frontend
npm install
Running the Application
Start the backend server:

Bash
# Inside the backend directory with your virtual environment activated
uvicorn main:app --reload
Start the frontend development server:

Bash
# Inside the frontend directory
npm run dev
📄 License
This project is licensed under the Apache 2.0 License - see the LICENSE file for details.
