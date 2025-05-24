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
  const [interviewState, setInterviewState] = useState<
    "setup" | "interview" | "feedback"
  >("setup");
  const [socketConnected, setSocketConnected] = useState(false);
  const { toast } = useToast();
  const [isListening, setIsListening] = useState(false);

  // Ref to track if initial stream setup is complete
  const initialSetupCompleteRef = useRef(false);
  const finalTranscriptRef = useRef("");
  const silenceTimeoutRef = useRef<number | null>(null);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const {
    connect,
    disconnect,
    startInterview,
    submitAnswer,
    currentQuestion,
    questionNumber,
    feedback,
    isConnected,
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
    onInterviewComplete: () => setInterviewState("feedback"),
  });

  const listenSpeech = (silenceThresholdMs = 5000) => {
    // don’t start listening if we’re currently speaking
    if (isSpeaking) {
      console.warn("Cannot start listening while speaking");
      return;
    }

    // browser support check
    const SpeechRecognition =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      toast({
        title: "Speech Recognition not supported",
        description: "Your browser does not support speech recognition",
        variant: "destructive",
      });
      return;
    }

    // reuse instance if already created
    let recognition = recognitionRef.current;
    if (!recognition) {
      recognition = new SpeechRecognition();
      recognition.lang = "en-US";
      recognition.interimResults = true; // get partial results
      recognition.maxAlternatives = 1;
      recognition.continuous = true;
      recognitionRef.current = recognition;
    }

    recognition.onstart = () => {
      setIsListening(true);
      finalTranscriptRef.current = "";
      silenceTimeoutRef.current = window.setTimeout(
        () => recognition!.stop(),
        silenceThresholdMs
      );
      console.log("🔴 Listening started");
    };

    recognition.onresult = (event) => {
      if (silenceTimeoutRef.current) {
        clearTimeout(silenceTimeoutRef.current);
      }
      let interim = "";
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        const res = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscriptRef.current += res;
        } else {
          interim += res;
        }
      }
      console.log("ℹ️ Interim:", interim);
      silenceTimeoutRef.current = window.setTimeout(
        () => recognition!.stop(),
        silenceThresholdMs
      );
    };

    recognition.onend = () => {
      setIsListening(false);
      console.log("🛑 Listening stopped", finalTranscriptRef.current);
      if (silenceTimeoutRef.current) {
        clearTimeout(silenceTimeoutRef.current);
        silenceTimeoutRef.current = null;
      }
      submitAnswer(finalTranscriptRef.current);
      // If you want continuous listening, you could call recognition.start() again here
    };

    recognition.onerror = (err) => {
      setIsListening(false);
      if (silenceTimeoutRef.current) {
        clearTimeout(silenceTimeoutRef.current);
        silenceTimeoutRef.current = null;
      }
      submitAnswer(finalTranscriptRef.current);
      console.error("Speech recognition error:", err.error);
    };

    // kick it off
    recognition.start();
  };

  // Only clean up on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  const handleStartNewInterview = () => {
    setInterviewState("setup");
  };

  useEffect(() => {
    listenSpeech();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center py-8 px-4">
      <header className="w-full max-w-3xl mb-8">
        <h1 className="text-3xl font-bold text-center text-gray-800">
          AI Interview Simulator
        </h1>
        <p className="text-center text-gray-600 mt-2">
          Practice your interview skills with an AI interviewer
        </p>
        <div className="mt-2 flex justify-center items-center gap-2">
          <span
            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
              isConnected
                ? "bg-green-100 text-green-800"
                : "bg-red-100 text-red-800"
            }`}
          >
            {isConnected ? "Connected" : "Disconnected"}
          </span>
          {!isConnected && (
            <Button variant="outline" size="sm" onClick={connect}>
              Connect
            </Button>
          )}
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
