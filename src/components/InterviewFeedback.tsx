
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface InterviewFeedbackProps {
  feedback: string;
  onStartNewInterview: () => void;
}

export const InterviewFeedback = ({ feedback, onStartNewInterview }: InterviewFeedbackProps) => {
  // Format feedback with some basic HTML styling
  const formatFeedback = (feedbackText: string) => {
    // Replace line breaks with <br> tags and maintain formatting
    return feedbackText
      .replace(/\n\n/g, '<br><br>')
      .replace(/\n/g, '<br>')
      .replace(/(\d+\. |\* )/g, '<br>$1')
      .replace(/^(.*?:)/gm, '<strong>$1</strong>');
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Interview Feedback</CardTitle>
      </CardHeader>
      <CardContent>
        <div 
          className="bg-gray-50 p-6 rounded-md border border-gray-200 prose max-w-none"
          dangerouslySetInnerHTML={{ __html: formatFeedback(feedback) }}
        />
      </CardContent>
      <CardFooter>
        <Button onClick={onStartNewInterview} className="w-full">
          Start New Interview
        </Button>
      </CardFooter>
    </Card>
  );
};
