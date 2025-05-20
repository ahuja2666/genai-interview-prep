
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { toast } from "@/hooks/use-toast";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertTriangle, Loader2 } from "lucide-react";

interface InterviewFormProps {
  onStartInterview: (jobDescription: string, resume: string) => void;
  isConnected: boolean;
}

export const InterviewForm = ({ onStartInterview, isConnected }: InterviewFormProps) => {
  const [jobDescription, setJobDescription] = useState("");
  const [resume, setResume] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleStartInterview = async () => {
    if (!jobDescription.trim()) {
      toast({
        title: "Job description required",
        description: "Please enter a job description",
        variant: "destructive",
      });
      return;
    }

    if (!resume.trim()) {
      toast({
        title: "Resume required",
        description: "Please enter your resume",
        variant: "destructive",
      });
      return;
    }

    if (!isConnected) {
      toast({
        title: "Not connected to server",
        description: "Please wait for the connection to be established",
        variant: "destructive",
      });
      return;
    }

    setIsSubmitting(true);
    try {
      onStartInterview(jobDescription, resume);
    } catch (error) {
      toast({
        title: "Error starting interview",
        description: "An error occurred while starting the interview",
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Start a New Interview</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {!isConnected && (
          <Alert variant="destructive" className="mb-4">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              Not connected to server. Please wait for connection to be established or refresh the page.
            </AlertDescription>
          </Alert>
        )}
        <div className="space-y-2">
          <Label htmlFor="job-description">Job Description</Label>
          <Textarea
            id="job-description"
            placeholder="Paste the job description here..."
            rows={5}
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            disabled={isSubmitting}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="resume">Your Resume</Label>
          <Textarea
            id="resume"
            placeholder="Paste your resume here..."
            rows={5}
            value={resume}
            onChange={(e) => setResume(e.target.value)}
            disabled={isSubmitting}
          />
        </div>
      </CardContent>
      <CardFooter>
        <Button 
          onClick={handleStartInterview} 
          disabled={!isConnected || isSubmitting}
          className="w-full"
        >
          {isSubmitting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" /> 
              Starting Interview...
            </>
          ) : (
            'Start Interview'
          )}
        </Button>
      </CardFooter>
    </Card>
  );
};
