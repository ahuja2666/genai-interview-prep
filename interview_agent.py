
import os
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain.memory import ConversationBufferMemory
from langchain_core.runnables import RunnablePassthrough
import langchain
from operator import itemgetter
from langchain_core.exceptions import OutputParserException

# Load environment variables
load_dotenv()

class InterviewAgent:
    def __init__(self, job_description: str, resume: str, max_questions: int = 20):
        """
        Initialize the interview agent
        
        Args:
            job_description (str): The job description text
            resume (str): The resume text
            max_questions (int): Maximum number of questions to ask (default: 20)
        """
        self.job_description = job_description
        self.resume = resume
        self.max_questions = max_questions
        self.current_question_number = 0
        self.conversation_history = []
        self.answers = []
        
        # Initialize the LLM
        self.llm = ChatOpenAI(
            temperature=0.5,
            model="gpt-4o",
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Initialize the memory
        self.memory = ConversationBufferMemory(
            return_messages=True,
            output_key="output",
            input_key="input"
        )
    
    def start_interview(self) -> str:
        """Start the interview and get the first question"""
        # System message that explains the task
        system_prompt = f"""
        You are an expert AI interviewer. Your task is to conduct a job interview based on the provided job description and the candidate's resume.
        
        JOB DESCRIPTION:
        {self.job_description}
        
        CANDIDATE'S RESUME:
        {self.resume}
        
        Your goal is to ask relevant technical and behavioral questions that assess the candidate's fit for the role described in the job description.
        Carefully analyze the resume and job description to identify the key skills, experiences, and qualifications that should be evaluated.
        
        For this first question, introduce yourself briefly as an AI interviewer and ask a relevant opening question based on the candidate's background.
        The question should be specific to their experience or the job requirements.
        """
        
        response = self.llm.invoke([SystemMessage(content=system_prompt)])
        first_question = response.content
        
        # Store the first question in conversation history
        self.conversation_history.append(SystemMessage(content=system_prompt))
        self.conversation_history.append(AIMessage(content=first_question))
        
        self.current_question_number = 1
        
        return first_question
    
    def process_answer(self, answer: str) -> Dict[str, Any]:
        """
        Process the user's answer and generate the next question
        
        Args:
            answer (str): User's answer to the previous question
            
        Returns:
            Dict with next question or completion status
        """
        # Add user's answer to conversation history
        self.conversation_history.append(HumanMessage(content=answer))
        self.answers.append(answer)
        
        # Check if we've reached the maximum number of questions
        if self.current_question_number >= self.max_questions:
            return {
                "interview_complete": True
            }
        
        # Generate the next question
        system_prompt = f"""
        Continue the job interview based on the conversation so far. Your task is to ask the next most relevant question.
        
        JOB DESCRIPTION:
        {self.job_description}
        
        CANDIDATE'S RESUME:
        {self.resume}
        
        You should:
        1. Consider the candidate's previous answers
        2. Avoid repeating questions that have already been asked
        3. Focus on areas that haven't been covered but are important for the role
        4. Ask a mix of technical, behavioral, and situational questions
        5. Be conversational but professional
        
        This is question #{self.current_question_number + 1} out of {self.max_questions}.
        """
        
        # Create a messages list with conversation history
        messages = [SystemMessage(content=system_prompt)] + self.conversation_history
        
        # Generate the next question
        response = self.llm.invoke(messages)
        next_question = response.content
        
        # Add the question to conversation history
        self.conversation_history.append(AIMessage(content=next_question))
        
        # Increment question counter
        self.current_question_number += 1
        
        return {
            "interview_complete": False,
            "next_question": next_question,
            "question_number": self.current_question_number
        }
    
    def generate_feedback(self) -> Dict[str, Any]:
        """
        Generate comprehensive feedback based on the interview
        
        Returns:
            Dict with feedback components
        """
        system_prompt = f"""
        As an expert AI interviewer, provide comprehensive feedback on the candidate's interview performance.
        
        JOB DESCRIPTION:
        {self.job_description}
        
        CANDIDATE'S RESUME:
        {self.resume}
        
        Based on the interview conversation, generate detailed feedback with the following sections:
        1. Overall Assessment: Provide a general evaluation of the candidate's performance
        2. Strengths: Identify 3-5 key strengths demonstrated during the interview
        3. Areas for Improvement: Suggest 2-4 areas where the candidate could improve
        4. Technical Skills Assessment: Evaluate the technical skills relevant to the job
        5. Communication Skills: Assess how well the candidate communicated their ideas
        6. Job Fit: Analyze how well the candidate's background aligns with the job requirements
        7. Recommendations: Provide specific recommendations for the candidate to improve their interview performance
        
        Format the feedback in a structured way with clear headings and bullet points where appropriate.
        Be honest but constructive, and provide actionable advice.
        """
        
        # Create a messages list with conversation history
        messages = [SystemMessage(content=system_prompt)] + self.conversation_history
        
        # Generate the feedback
        response = self.llm.invoke(messages)
        feedback = response.content
        
        return {
            "detailed_feedback": feedback
        }
