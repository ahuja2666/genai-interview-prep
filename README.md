
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

### WebSocket Events

#### Client -> Server Events:

1. **start_interview**
   ```json
   {
     "session_id": "unique_session_id",
     "job_description": "Full job description text...",
     "resume": "Full resume text..."
   }
   ```

2. **submit_answer**
   ```json
   {
     "session_id": "unique_session_id",
     "answer": "User's answer to the question"
   }
   ```

#### Server -> Client Events:

1. **interview_started**
   ```json
   {
     "message": "Interview started successfully",
     "question": "First interview question...",
     "question_number": 1
   }
   ```

2. **next_question**
   ```json
   {
     "question": "Next interview question...",
     "question_number": 2
   }
   ```

3. **interview_complete**
   ```json
   {
     "message": "Interview completed",
     "feedback": {
       "detailed_feedback": "Comprehensive feedback text..."
     }
   }
   ```

4. **error**
   ```json
   {
     "message": "Error message"
   }
   ```

## Integration with Frontend

To integrate with a frontend application:

1. Connect to the WebSocket server:
   ```javascript
   const socket = io("http://localhost:5000");
   
   socket.on("connect", () => {
     console.log("Connected to server");
   });
   ```

2. Start an interview:
   ```javascript
   socket.emit("start_interview", {
     session_id: "unique_session_id", // Generate a unique ID for the session
     job_description: jobDescriptionText,
     resume: resumeText
   });
   ```

3. Listen for the first question:
   ```javascript
   socket.on("interview_started", (data) => {
     console.log(`Question ${data.question_number}: ${data.question}`);
     // Display the question to the user and capture their response
   });
   ```

4. Submit the user's answer:
   ```javascript
   socket.emit("submit_answer", {
     session_id: "unique_session_id",
     answer: userAnswer
   });
   ```

5. Listen for the next question:
   ```javascript
   socket.on("next_question", (data) => {
     console.log(`Question ${data.question_number}: ${data.question}`);
     // Display the new question to the user
   });
   ```

6. Handle interview completion:
   ```javascript
   socket.on("interview_complete", (data) => {
     console.log("Interview complete!");
     console.log("Feedback:", data.feedback);
     // Display the feedback to the user
   });
   ```

7. Handle errors:
   ```javascript
   socket.on("error", (data) => {
     console.error("Error:", data.message);
     // Display error to the user
   });
   ```

## Frontend TTS/STT Integration

For a more immersive experience, you can integrate Text-to-Speech (TTS) and Speech-to-Text (STT) in your frontend:

- Use the Web Speech API for browser-based TTS/STT
- Or integrate with services like Google Cloud Speech-to-Text, Amazon Polly, etc.

Example with Web Speech API:

```javascript
// Text to Speech
function speakQuestion(question) {
  const speech = new SpeechSynthesisUtterance(question);
  window.speechSynthesis.speak(speech);
}

// Speech to Text
function listenForAnswer() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const recognition = new SpeechRecognition();
  
  recognition.onresult = (event) => {
    const answer = event.results[0][0].transcript;
    // Submit the answer to the server
    socket.emit("submit_answer", {
      session_id: "unique_session_id",
      answer: answer
    });
  };
  
  recognition.start();
}
```

## License

MIT
