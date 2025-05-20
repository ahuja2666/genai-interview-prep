
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
  const reconnectAttemptsRef = useRef<number>(0);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const maxReconnectAttempts = 5;

  const connect = useCallback(() => {
    // Close existing socket if it exists
    if (socketRef.current) {
      socketRef.current.close();
    }

    // Reset reconnect timeout if exists
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    try {
      // Instead of hardcoding localhost, detect the current environment
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = process.env.NODE_ENV === 'production' ? window.location.host : 'localhost:8000';
      const wsUrl = `${protocol}//${host}/ws/${clientIdRef.current}`;
      
      console.log(`Connecting to WebSocket at: ${wsUrl}`);
      
      // Create new WebSocket connection
      const socket = new WebSocket(wsUrl);

      socket.onopen = () => {
        console.log("Connected to server");
        setIsConnected(true);
        reconnectAttemptsRef.current = 0; // Reset reconnect attempts on successful connection
        onConnect?.();
      };

      socket.onclose = (event) => {
        console.log("Disconnected from server", event.code, event.reason);
        setIsConnected(false);
        
        // Only try to reconnect if it wasn't a normal closure
        if (event.code !== 1000) {
          handleReconnect();
        } else {
          onDisconnect?.();
        }
      };

      socket.onerror = (error) => {
        console.error("WebSocket error:", error);
        // Don't call onError here, as onclose will be called next and will handle reconnection
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
      handleReconnect();
    }
  }, [onConnect, onDisconnect, onError, onInterviewStarted, onInterviewComplete]);

  const handleReconnect = useCallback(() => {
    if (reconnectAttemptsRef.current < maxReconnectAttempts) {
      reconnectAttemptsRef.current += 1;
      
      // Exponential backoff: wait longer with each reconnection attempt
      const delay = Math.min(1000 * (2 ** reconnectAttemptsRef.current), 30000);
      
      console.log(`Attempting to reconnect in ${delay}ms (attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts})`);
      
      // Clean up any existing timeout
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      
      // Set a new timeout for reconnection
      reconnectTimeoutRef.current = setTimeout(() => {
        connect();
      }, delay);
      
      onDisconnect?.();
    } else {
      console.error(`Failed to reconnect after ${maxReconnectAttempts} attempts`);
      onError?.(`Unable to connect to server after ${maxReconnectAttempts} attempts. Please refresh the page.`);
    }
  }, [connect, onDisconnect, onError]);

  const disconnect = useCallback(() => {
    // Clear any reconnection timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    // Close the WebSocket connection if it exists
    if (socketRef.current) {
      socketRef.current.close(1000, "Normal closure"); // Use 1000 for normal closure
      socketRef.current = null;
    }
    
    setIsConnected(false);
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
      
      // Try to reconnect if socket is closed unexpectedly
      if (!socketRef.current || socketRef.current.readyState === WebSocket.CLOSED) {
        connect();
      }
      
      onError?.("Connection to server lost. Attempting to reconnect...");
    }
  }, [onError, connect]);

  const startInterview = useCallback(
    (jobDescription: string, resume: string) => {
      // Only attempt to start interview if connected
      if (isConnected) {
        sendMessage("start_interview", {
          job_description: jobDescription,
          resume: resume,
        });
      } else {
        onError?.("Not connected to server. Please wait for connection to be established.");
        connect(); // Try to connect if not already connected
      }
    },
    [sendMessage, isConnected, onError, connect]
  );

  const submitAnswer = useCallback(
    (answer: string) => {
      // Only attempt to submit answer if connected
      if (isConnected) {
        sendMessage("submit_answer", {
          answer: answer,
        });
      } else {
        onError?.("Not connected to server. Please wait for connection to be established.");
        connect(); // Try to connect if not already connected
      }
    },
    [sendMessage, isConnected, onError, connect]
  );

  // Clean up WebSocket connection and timeouts on unmount
  useEffect(() => {
    connect();
    
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

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
