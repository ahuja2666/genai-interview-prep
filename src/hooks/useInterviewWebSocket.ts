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
    // Don't try to connect if we already have a socket
    if (socketRef.current) {
      return;
    }

    try {
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const host =
        process.env.NODE_ENV === "production"
          ? window.location.host
          : "localhost:8000";
      const wsUrl = `${protocol}//${host}/ws/${clientIdRef.current}`;

      console.log(`Connecting to WebSocket at: ${wsUrl}`);

      const socket = new WebSocket(wsUrl);

      socket.onopen = () => {
        console.log("Connected to server");
        setIsConnected(true);
        onConnect?.();
      };

      socket.onclose = (event) => {
        console.log("Disconnected from server", event.code, event.reason);
        setIsConnected(false);
        onDisconnect?.();
      };

      socket.onerror = (error) => {
        console.error("WebSocket error:", error);
        onError?.(
          "Failed to connect to server. Please ensure the server is running."
        );
      };

      socket.onmessage = (event) => {
        try {
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
        } catch (error) {
          console.error("Error parsing message:", error);
        }
      };

      socketRef.current = socket;
    } catch (error) {
      console.error("Error creating WebSocket:", error);
      onError?.("Failed to create WebSocket connection");
    }
  }, [
    onConnect,
    onDisconnect,
    onError,
    onInterviewStarted,
    onInterviewComplete,
  ]);

  const disconnect = useCallback(() => {
    if (socketRef.current) {
      socketRef.current.close(1000, "Normal closure");
      socketRef.current = null;
    }
    setIsConnected(false);
  }, []);

  const sendMessage = useCallback(
    (eventType: string, data: unknown) => {
      if (
        socketRef.current &&
        socketRef.current.readyState === WebSocket.OPEN
      ) {
        socketRef.current.send(
          JSON.stringify({
            event: eventType,
            data: data,
          })
        );
      } else {
        console.error("WebSocket is not connected");
        onError?.("Not connected to server");
      }
    },
    [onError]
  );

  const startInterview = useCallback(
    (jobDescription: string, resume: string) => {
      if (isConnected) {
        sendMessage("start_interview", {
          job_description: jobDescription,
          resume: resume,
        });
      } else {
        onError?.("Not connected to server");
      }
    },
    [sendMessage, isConnected, onError]
  );

  const submitAnswer = useCallback(
    (answer: string) => {
      if (isConnected) {
        sendMessage("submit_answer", {
          answer: answer,
        });
      } else {
        onError?.("Not connected to server");
      }
    },
    [sendMessage, isConnected, onError]
  );

  // Only clean up on unmount
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
