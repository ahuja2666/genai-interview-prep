
import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/ui/card";
import { Mic, MicOff, Volume2, VolumeX } from "lucide-react";
import { InterviewForm } from "@/components/InterviewForm";
import { InterviewFeedback } from "@/components/InterviewFeedback";
import { useToast } from "@/hooks/use-toast";
import { InterviewSession } from "@/components/InterviewSession";
import { useInterviewWebSocket } from "@/hooks/useInterviewWebSocket";

const Index = () => {
  const [interviewState, setInterviewState] = useState<"setup" | "interview" | "feedback">("setup");
  const [socketConnected, setSocketConnected] = useState(false);
  const { toast } = useToast();
  
  const {
    connect,
    disconnect,
    startInterview,
    submitAnswer,
    currentQuestion,
    questionNumber,
    feedback,
    isConnected
  } = useInterviewWebSocket({
    onConnect: () => {
      setSocketConnected(true);
      toast({
        title: "Connected to server",
        description: "You can now start the interview",
      });
    },
    onDisconnect: () => {
      setSocketConnected(false);
      toast({
        title: "Disconnected from server",
        variant: "destructive",
        description: "Connection to server lost",
      });
    },
    onInterviewStarted: () => setInterviewState("interview"),
    onInterviewComplete: () => setInterviewState("feedback")
  });

  // Connect to WebSocket when component mounts
  useEffect(() => {
    connect();
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  const handleStartNewInterview = () => {
    setInterviewState("setup");
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center py-8 px-4">
      <header className="w-full max-w-3xl mb-8">
        <h1 className="text-3xl font-bold text-center text-gray-800">AI Interview Simulator</h1>
        <p className="text-center text-gray-600 mt-2">
          Practice your interview skills with an AI interviewer
        </p>
        <div className="mt-2 flex justify-center">
          <span 
            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
              isConnected 
                ? "bg-green-100 text-green-800" 
                : "bg-red-100 text-red-800"
            }`}
          >
            {isConnected ? "Connected" : "Disconnected"}
          </span>
        </div>
      </header>

      <main className="w-full max-w-3xl flex-grow">
        {interviewState === "setup" && (
          <InterviewForm 
            onStartInterview={startInterview} 
            isConnected={isConnected}
          />
        )}
        
        {interviewState === "interview" && (
          <InterviewSession 
            currentQuestion={currentQuestion}
            questionNumber={questionNumber}
            onSubmitAnswer={submitAnswer}
          />
        )}
        
        {interviewState === "feedback" && (
          <InterviewFeedback 
            feedback={feedback}
            onStartNewInterview={handleStartNewInterview}
          />
        )}
      </main>

      <footer className="w-full max-w-3xl mt-8 text-center text-sm text-gray-500">
        &copy; {new Date().getFullYear()} AI Interview Simulator
      </footer>
    </div>
  );
};

export default Index;
