import os
import json
import asyncio
import base64
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from interview_agent import InterviewAgent
import uvicorn
from typing import Dict, Any, Set
import time
from PyPDF2 import PdfReader
from io import BytesIO

# Load environment variables
load_dotenv()

app = FastAPI()

# Get the port from environment variable (Railway sets this)
PORT = int(os.getenv("PORT", 8000))

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dictionary to store active interview sessions
interview_sessions = {}

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_locks: Dict[str, asyncio.Lock] = {}
        self.connection_status: Dict[str, bool] = {}
        self.global_lock = asyncio.Lock()  # Add global lock for connection management
    
    async def connect(self, websocket: WebSocket, client_id: str):
        try:
            print(f"Attempting to connect client {client_id}")
            
            # Use global lock for connection management
            async with self.global_lock:
                # Create a lock for this client if it doesn't exist
                if client_id not in self.connection_locks:
                    print(f"Creating new connection lock for client {client_id}")
                    self.connection_locks[client_id] = asyncio.Lock()
                
                # Check if there's an existing connection
                if client_id in self.active_connections:
                    print(f"Found existing connection for client {client_id}, cleaning up")
                    try:
                        # Try to close the existing connection gracefully
                        await self.active_connections[client_id].close()
                    except Exception as e:
                        print(f"Error closing existing connection for client {client_id}: {str(e)}")
                    self.disconnect(client_id)
                
                print(f"Accepting WebSocket connection for client {client_id}")
                # Accept the connection
                await websocket.accept()
                
                # Store the connection
                self.active_connections[client_id] = websocket
                self.connection_status[client_id] = True
                
                print(f"Connection established for client {client_id}")
                
                # Send initial connection success message
                print(f"Sending connection confirmation to client {client_id}")
                await self.send_personal_message({
                    "event": "connection_established",
                    "data": {"client_id": client_id}
                }, client_id)
                
        except Exception as e:
            print(f"Error during connection for client {client_id}: {str(e)}")
            self.disconnect(client_id)
            raise HTTPException(status_code=500, detail="Failed to establish connection")
    
    def disconnect(self, client_id: str):
        print(f"Disconnecting client {client_id}")
        self.connection_status[client_id] = False
        if client_id in self.active_connections:
            print(f"Removing active connection for client {client_id}")
            del self.active_connections[client_id]
        if client_id in self.connection_locks:
            print(f"Removing connection lock for client {client_id}")
            del self.connection_locks[client_id]
        print(f"Connection cleanup completed for client {client_id}")
    
    async def send_personal_message(self, message: Dict[str, Any], client_id: str):
        if not self.connection_status.get(client_id, False):
            print(f"Connection not active for client {client_id}")
            return False
            
        if client_id not in self.active_connections:
            print(f"No active connection for client {client_id}")
            return False
            
        if client_id not in self.connection_locks:
            print(f"No connection lock for client {client_id}")
            return False
            
        try:
            async with self.connection_locks[client_id]:
                if client_id in self.active_connections and self.connection_status.get(client_id, False):
                    print(f"Sending message to client {client_id}: {message}")
                    await self.active_connections[client_id].send_json(message)
                    return True
                else:
                    print(f"Connection not ready for client {client_id}")
                    return False
        except Exception as e:
            print(f"Error sending message to client {client_id}: {str(e)}")
            self.disconnect(client_id)
            return False

manager = ConnectionManager()

@app.get("/")
async def index():
    return {"status": "API is running"}

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    try:
        print(f"WebSocket endpoint called for client {client_id}")
        await manager.connect(websocket, client_id)
        
        while manager.connection_status.get(client_id, False):
            try:
                print(f"Waiting for message from client {client_id}")
                # Handle JSON messages
                message = await websocket.receive_text()
                
                try:
                    data = json.loads(message)
                    event = data.get("event")
                    payload = data.get("data", {})
                    
                    print(f"Received message from client {client_id}: {event} : {payload}")
                    
                    if event == "start_interview":
                        await handle_start_interview(client_id, payload)
                    elif event == "submit_answer":
                        await handle_submit_answer(client_id, payload)
                except json.JSONDecodeError:
                    print(f"Received invalid JSON from client {client_id}")
                    continue
                    
            except WebSocketDisconnect:
                print(f"WebSocket disconnected for client {client_id}")
                break
            except Exception as e:
                print(f"Error processing message for client {client_id}: {str(e)}")
                await manager.send_personal_message({
                    "event": "error",
                    "data": {'message': 'An error occurred while processing your request'}
                }, client_id)
    except Exception as e:
        print(f"Error in websocket connection for client {client_id}: {str(e)}")
    finally:
        print(f"Cleaning up WebSocket connection for client {client_id}")
        manager.disconnect(client_id)
        if client_id in interview_sessions:
            del interview_sessions[client_id]
        print(f"WebSocket connection cleanup completed for client {client_id}")

async def handle_start_interview(client_id: str, data: Dict[str, Any]):
    """
    Start a new interview session
    data: {
        "job_description": "...",
        "resume": "base64 encoded resume string"
    }
    """
    job_description = data.get('job_description', '')
    resume_base64 = data.get('resume', '')
    
    print("Received resume data:", resume_base64[:100] + "..." if len(resume_base64) > 100 else resume_base64)
    
    # Decode base64 resume to string
    try:
        if not resume_base64:
            raise ValueError("Empty resume data received")
            
        # Remove data URL prefix if present
        if resume_base64.startswith('data:'):
            resume_base64 = resume_base64.split(',')[1]
            
        # Check if the string is properly padded
        padding = len(resume_base64) % 4
        if padding:
            resume_base64 += '=' * (4 - padding)
            
        print("Attempting to decode base64 resume...")
        # Decode base64 to bytes
        pdf_bytes = base64.b64decode(resume_base64)
        
        # Read PDF content
        pdf_file = BytesIO(pdf_bytes)
        pdf_reader = PdfReader(pdf_file)
        
        # Extract text from all pages
        resume_text = ""
        for page in pdf_reader.pages:
            resume_text += page.extract_text() + "\n"
            
        print("Successfully decoded resume")
    except Exception as e:
        print(f"Error decoding resume: {str(e)}")
        print(f"Resume data type: {type(resume_base64)}")
        print(f"Resume data length: {len(resume_base64)}")
        await manager.send_personal_message({
            "event": "error",
            "data": {'message': f'Invalid resume format: {str(e)}. Please provide a valid PDF resume.'}
        }, client_id)
        return
    
    # Create a new interview agent
    interview_agent = InterviewAgent(
        job_description=job_description,
        resume=resume_text
    )
    
    # Store the interview agent in the sessions dictionary
    interview_sessions[client_id] = interview_agent
    
    # Initialize the interview
    response = interview_agent.start_interview()
    
    # Get the audio data from the response
    audio_data = next((v for k, v in response.items() if k != "question_number"), None)
    
    # Send only the audio data to the client
    await manager.send_personal_message({
        "event": "interview_started",
        "data": {
            'message': 'Interview started successfully',
            'question': audio_data,
            'question_number': response['question_number']
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
        # Get the closing message and audio
        closing_message = next((k for k in response.keys() if k != "question_number" and k != "interview_complete"), None)
        closing_audio = response[closing_message] if closing_message else None
        
        if closing_message and closing_audio:
            # First send the closing message
            await manager.send_personal_message({
                "event": "interview_closing",
                "data": {
                    'message': 'Interview closing',
                    'question': closing_audio,
                    'question_number': response['question_number']
                }
            }, client_id)
            
            # Wait a bit to let the closing message play
            await asyncio.sleep(5)
        
        # Then send the feedback
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
        # Get the question and audio data from the response
        question = next((k for k in response.keys() if k != "question_number" and k != "interview_complete"), None)
        audio_data = response[question] if question else None
        
        if not question or not audio_data:
            await manager.send_personal_message({
                "event": "error",
                "data": {'message': 'Error generating next question'}
            }, client_id)
            return
            
        # Send the next question
        await manager.send_personal_message({
            "event": "next_question",
            "data": {
                'question': audio_data,  # Send the audio data
                'question_number': response['question_number']
            }
        }, client_id)

if __name__ == '__main__':
    uvicorn.run("app:app", host="0.0.0.0", port=PORT, reload=False)  # Set reload to False in production
