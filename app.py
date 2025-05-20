
import os
import json
from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from dotenv import load_dotenv
from interview_agent import InterviewAgent

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Dictionary to store active interview sessions
interview_sessions = {}

@app.route('/')
def index():
    return jsonify({"status": "API is running"})

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')
    # Clean up any interview sessions if needed

@socketio.on('start_interview')
def handle_start_interview(data):
    """
    Start a new interview session
    data: {
        "session_id": "unique_session_id",
        "job_description": "...",
        "resume": "..."
    }
    """
    session_id = data.get('session_id')
    job_description = data.get('job_description', '')
    resume = data.get('resume', '')
    
    if not session_id:
        emit('error', {'message': 'Session ID is required'})
        return
    
    # Create a new interview agent
    interview_agent = InterviewAgent(
        job_description=job_description,
        resume=resume
    )
    
    # Store the interview agent in the sessions dictionary
    interview_sessions[session_id] = interview_agent
    
    # Initialize the interview
    first_question = interview_agent.start_interview()
    
    # Send the first question to the client
    emit('interview_started', {
        'message': 'Interview started successfully',
        'question': first_question,
        'question_number': 1
    })

@socketio.on('submit_answer')
def handle_submit_answer(data):
    """
    Process user's answer and get the next question
    data: {
        "session_id": "unique_session_id",
        "answer": "User's answer to the question"
    }
    """
    session_id = data.get('session_id')
    answer = data.get('answer', '')
    
    if not session_id or session_id not in interview_sessions:
        emit('error', {'message': 'Invalid session or session expired'})
        return
    
    interview_agent = interview_sessions[session_id]
    
    # Process the answer and get the next question
    response = interview_agent.process_answer(answer)
    
    if response.get('interview_complete', False):
        # If the interview is complete, send the feedback
        feedback = interview_agent.generate_feedback()
        emit('interview_complete', {
            'message': 'Interview completed',
            'feedback': feedback
        })
        
        # Clean up the session
        del interview_sessions[session_id]
    else:
        # Send the next question
        emit('next_question', {
            'question': response.get('next_question', ''),
            'question_number': response.get('question_number', 0)
        })

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
