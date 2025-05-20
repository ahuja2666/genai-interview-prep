
import os
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from interview_agent import InterviewAgent
import uvicorn
from typing import Dict, Any

# Load environment variables
load_dotenv()

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Dictionary to store active interview sessions
interview_sessions = {}

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
    
    async def send_personal_message(self, message: Dict[str, Any], client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)

manager = ConnectionManager()

@app.get("/")
async def index():
    return {"status": "API is running"}

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_json()
            
            event = data.get("event")
            payload = data.get("data", {})
            
            if event == "start_interview":
                await handle_start_interview(client_id, payload)
            elif event == "submit_answer":
                await handle_submit_answer(client_id, payload)
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        # Clean up any interview sessions
        if client_id in interview_sessions:
            del interview_sessions[client_id]

async def handle_start_interview(client_id: str, data: Dict[str, Any]):
    """
    Start a new interview session
    data: {
        "job_description": "...",
        "resume": "..."
    }
    """
    job_description = data.get('job_description', '')
    resume = data.get('resume', '')
    
    # Create a new interview agent
    interview_agent = InterviewAgent(
        job_description=job_description,
        resume=resume
    )
    
    # Store the interview agent in the sessions dictionary
    interview_sessions[client_id] = interview_agent
    
    # Initialize the interview
    first_question = interview_agent.start_interview()
    
    # Send the first question to the client
    await manager.send_personal_message({
        "event": "interview_started",
        "data": {
            'message': 'Interview started successfully',
            'question': first_question,
            'question_number': 1
        }
    }, client_id)

async def handle_submit_answer(client_id: str, data: Dict[str, Any]):
    """
    Process user's answer and get the next question
    data: {
        "answer": "User's answer to the question"
    }
    """
    answer = data.get('answer', '')
    
    if client_id not in interview_sessions:
        await manager.send_personal_message({
            "event": "error",
            "data": {'message': 'Invalid session or session expired'}
        }, client_id)
        return
    
    interview_agent = interview_sessions[client_id]
    
    # Process the answer and get the next question
    response = interview_agent.process_answer(answer)
    
    if response.get('interview_complete', False):
        # If the interview is complete, send the feedback
        feedback = interview_agent.generate_feedback()
        await manager.send_personal_message({
            "event": "interview_complete",
            "data": {
                'message': 'Interview completed',
                'feedback': feedback
            }
        }, client_id)
        
        # Clean up the session
        del interview_sessions[client_id]
    else:
        # Send the next question
        await manager.send_personal_message({
            "event": "next_question",
            "data": {
                'question': response.get('next_question', ''),
                'question_number': response.get('question_number', 0)
            }
        }, client_id)

if __name__ == '__main__':
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
