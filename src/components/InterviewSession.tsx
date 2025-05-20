
import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Mic, MicOff, Volume2, VolumeX } from "lucide-react";
import { toast } from "@/hooks/use-toast";

interface InterviewSessionProps {
  currentQuestion: string;
  questionNumber: number;
  onSubmitAnswer: (answer: string) => void;
}

export const InterviewSession = ({
  currentQuestion,
  questionNumber,
  onSubmitAnswer,
}: InterviewSessionProps) => {
  const [answer, setAnswer] = useState("");
  const [isListening, setIsListening] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const recognitionRef = useRef<any>(null);

  // Text-to-speech function
  const speakText = (text: string) => {
    if ('speechSynthesis' in window && !isMuted) {
      const utterance = new SpeechSynthesisUtterance(text);
      window.speechSynthesis.cancel(); // Stop any current speech
      window.speechSynthesis.speak(utterance);
    } else if (!('speechSynthesis' in window)) {
      toast({
        title: "Text-to-Speech not supported",
        description: "Your browser does not support text-to-speech",
        variant: "destructive",
      });
    }
  };

  // Start or stop speech recognition
  const toggleListening = () => {
    if (isListening) {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      setIsListening(false);
      return;
    }

    if (!('SpeechRecognition' in window) && !('webkitSpeechRecognition' in window)) {
      toast({
        title: "Speech recognition not supported",
        description: "Your browser does not support speech recognition",
        variant: "destructive",
      });
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    
    recognition.onresult = (event) => {
      const speechResult = event.results[0][0].transcript;
      setAnswer((prev) => prev + " " + speechResult);
    };
    
    recognition.onend = () => {
      setIsListening(false);
    };
    
    recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
      setIsListening(false);
      toast({
        title: "Speech recognition error",
        description: "Error recognizing speech. Please try again.",
        variant: "destructive",
      });
    };
    
    recognition.start();
    recognitionRef.current = recognition;
    setIsListening(true);
  };

  // Toggle mute for text-to-speech
  const toggleMute = () => {
    setIsMuted(!isMuted);
    if (!isMuted) {
      window.speechSynthesis.cancel(); // Stop any current speech if muting
    }
  };

  // Speak the question when it changes
  useEffect(() => {
    if (currentQuestion && !isMuted) {
      speakText(currentQuestion);
    }
  }, [currentQuestion, isMuted]);

  // Clean up
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      window.speechSynthesis.cancel();
    };
  }, []);

  const handleSubmitAnswer = () => {
    if (!answer.trim()) {
      toast({
        title: "Answer required",
        description: "Please provide an answer",
        variant: "destructive",
      });
      return;
    }
    
    onSubmitAnswer(answer);
    setAnswer("");
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex justify-between items-center">
          <span>Question {questionNumber} of 20</span>
          <div className="flex gap-2">
            <Button 
              variant="outline" 
              size="icon" 
              onClick={toggleMute}
              title={isMuted ? "Unmute" : "Mute"}
            >
              {isMuted ? <VolumeX size={20} /> : <Volume2 size={20} />}
            </Button>
            <Button 
              variant="outline" 
              size="icon" 
              onClick={() => speakText(currentQuestion)}
              disabled={isMuted}
              title="Speak question"
            >
              <Volume2 size={20} />
            </Button>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="bg-gray-50 p-4 rounded-md border border-gray-200">
          <p className="text-lg">{currentQuestion}</p>
        </div>
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <label htmlFor="answer" className="text-sm font-medium">
              Your Answer
            </label>
            <Button 
              variant={isListening ? "destructive" : "outline"} 
              size="sm" 
              onClick={toggleListening}
              className="flex items-center gap-1"
            >
              {isListening ? <MicOff size={16} /> : <Mic size={16} />}
              {isListening ? "Stop Listening" : "Start Listening"}
            </Button>
          </div>
          <Textarea
            id="answer"
            placeholder="Type your answer here..."
            rows={4}
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
          />
        </div>
      </CardContent>
      <CardFooter>
        <Button 
          onClick={handleSubmitAnswer} 
          className="w-full"
        >
          Submit Answer
        </Button>
      </CardFooter>
    </Card>
  );
};
