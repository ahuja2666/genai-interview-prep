
import { useState, useCallback, useRef, useEffect } from "react";

// Generate a unique client ID
const generateClientId = () => {
  return `client_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
};

type InterviewWebSocketProps = {
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: string) => void;
  onInterviewStarted?: () => void;
  onInterviewComplete?: () => void;
};

export const useInterviewWebSocket = ({
  onConnect,
  onDisconnect,
  onError,
  onInterviewStarted,
  onInterviewComplete,
}: InterviewWebSocketProps) => {
  const [isConnected, setIsConnected] = useState(false);
  const [currentQuestion, setCurrentQuestion] = useState("");
  const [questionNumber, setQuestionNumber] = useState(0);
  const [feedback, setFeedback] = useState("");
  const socketRef = useRef<WebSocket | null>(null);
  const clientIdRef = useRef<string>(generateClientId());

  const connect = useCallback(() => {
    // Close existing socket if it exists
    if (socketRef.current) {
      socketRef.current.close();
    }

    // Create new WebSocket connection
    const socket = new WebSocket(`ws://localhost:8000/ws/${clientIdRef.current}`);

    socket.onopen = () => {
      console.log("Connected to server");
      setIsConnected(true);
      onConnect?.();
    };

    socket.onclose = () => {
      console.log("Disconnected from server");
      setIsConnected(false);
      onDisconnect?.();
    };

    socket.onerror = (error) => {
      console.error("WebSocket error:", error);
      onError?.("Error connecting to server");
    };

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      const eventType = data.event;
      const payload = data.data;

      console.log("Received event:", eventType, payload);

      switch (eventType) {
        case "interview_started":
          setCurrentQuestion(payload.question);
          setQuestionNumber(payload.question_number);
          onInterviewStarted?.();
          break;

        case "next_question":
          setCurrentQuestion(payload.question);
          setQuestionNumber(payload.question_number);
          break;

        case "interview_complete":
          setFeedback(payload.feedback.detailed_feedback);
          onInterviewComplete?.();
          break;

        case "error":
          console.error("Error:", payload.message);
          onError?.(payload.message);
          break;
      }
    };

    socketRef.current = socket;
  }, [onConnect, onDisconnect, onError, onInterviewStarted, onInterviewComplete]);

  const disconnect = useCallback(() => {
    if (socketRef.current) {
      socketRef.current.close();
      socketRef.current = null;
    }
  }, []);

  const sendMessage = useCallback((eventType: string, data: any) => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(
        JSON.stringify({
          event: eventType,
          data: data,
        })
      );
    } else {
      console.error("WebSocket is not connected");
      onError?.("Server connection lost. Please refresh the page.");
    }
  }, [onError]);

  const startInterview = useCallback(
    (jobDescription: string, resume: string) => {
      sendMessage("start_interview", {
        job_description: jobDescription,
        resume: resume,
      });
    },
    [sendMessage]
  );

  const submitAnswer = useCallback(
    (answer: string) => {
      sendMessage("submit_answer", {
        answer: answer,
      });
    },
    [sendMessage]
  );

  // Clean up WebSocket connection on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    connect,
    disconnect,
    startInterview,
    submitAnswer,
    isConnected,
    currentQuestion,
    questionNumber,
    feedback,
  };
};
