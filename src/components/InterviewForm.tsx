
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { toast } from "@/hooks/use-toast";

interface InterviewFormProps {
  onStartInterview: (jobDescription: string, resume: string) => void;
  isConnected: boolean;
}

export const InterviewForm = ({ onStartInterview, isConnected }: InterviewFormProps) => {
  const [jobDescription, setJobDescription] = useState("");
  const [resume, setResume] = useState("");

  const handleStartInterview = () => {
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

    onStartInterview(jobDescription, resume);
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Start a New Interview</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="job-description">Job Description</Label>
          <Textarea
            id="job-description"
            placeholder="Paste the job description here..."
            rows={5}
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
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
          />
        </div>
      </CardContent>
      <CardFooter>
        <Button 
          onClick={handleStartInterview} 
          disabled={!isConnected}
          className="w-full"
        >
          Start Interview
        </Button>
      </CardFooter>
    </Card>
  );
};
