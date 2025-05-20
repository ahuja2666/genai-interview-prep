
# AI Interview Simulator

An AI-powered interview simulator that conducts personalized interviews based on job descriptions and resumes.

## Features

- Real-time interview simulation using WebSockets
- Personalized questions based on job description and resume
- Comprehensive feedback at the end of the interview
- Easy integration with frontend applications

## Setup

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file based on `.env.example` and add your OpenAI API key
   ```
   cp .env.example .env
   # Edit the .env file to add your OpenAI API key
   ```
4. Run the application:
   ```
   python app.py
   ```

## API Usage

### WebSocket Connection

Connect to the WebSocket endpoint with a unique client ID:
```
ws://localhost:8000/ws/{client_id}
```

### WebSocket Messages

Messages use a standardized format:
```json
{
  "event": "event_name",
  "data": {
    // Event-specific data
  }
}
```

#### Client -> Server Events:

1. **start_interview**
   ```json
   {
     "event": "start_interview",
     "data": {
       "job_description": "Full job description text...",
       "resume": "Full resume text..."
     }
   }
   ```

2. **submit_answer**
   ```json
   {
     "event": "submit_answer",
     "data": {
       "answer": "User's answer to the question"
     }
   }
   ```

#### Server -> Client Events:

1. **interview_started**
   ```json
   {
     "event": "interview_started",
     "data": {
       "message": "Interview started successfully",
       "question": "First interview question...",
       "question_number": 1
     }
   }
   ```

2. **next_question**
   ```json
   {
     "event": "next_question",
     "data": {
       "question": "Next interview question...",
       "question_number": 2
     }
   }
   ```

3. **interview_complete**
   ```json
   {
     "event": "interview_complete",
     "data": {
       "message": "Interview completed",
       "feedback": {
         "detailed_feedback": "Comprehensive feedback text..."
       }
     }
   }
   ```

4. **error**
   ```json
   {
     "event": "error",
     "data": {
       "message": "Error message"
     }
   }
   ```

## Integration with Frontend

See the `example_client.html` file for a complete working example of how to integrate with a frontend application.

## Frontend TTS/STT Integration

For a more immersive experience, the example client includes Text-to-Speech (TTS) and Speech-to-Text (STT) using the Web Speech API.

## License

MIT
