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
import json
import base64
from openai import OpenAI

# Load environment variables
load_dotenv()

class InterviewAgent:
    def __init__(self, job_description: str, resume: str, max_questions: int = 10):
        """
        Initialize the interview agent
        
        Args:
            job_description (str): The job description text
            resume (str): The resume text
            max_questions (int): Maximum number of questions to ask (default: 10)
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
            model="gpt-4",
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Initialize OpenAI client for audio
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Initialize the memory
        self.memory = ConversationBufferMemory(
            return_messages=True,
            output_key="output",
            input_key="input"
        )
    
    def _generate_audio(self, text: str) -> str:
        """
        Generate audio from text using OpenAI's text-to-speech API
        
        Args:
            text (str): Text to convert to audio
            
        Returns:
            str: Base64 encoded audio data
        """
        try:
            response = self.openai_client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=text
            )
            
            # Convert audio to base64
            audio_data = response.content
            return base64.b64encode(audio_data).decode('utf-8')
        except Exception as e:
            print(f"Error generating audio: {str(e)}")
            return ""

    def start_interview(self) -> str:
        """Start the interview and get the first question"""
        # First, extract personal information from resume
        personal_info_prompt = f"""
        Extract the following personal information from the resume:
        1. Full name
        2. Years of experience
        3. Primary technical skills
        4. Current/last role
        5. Notable achievements (1-2)

        RESUME:
        {self.resume}

        Format the response as a JSON object:
        {{
            "name": "Full Name",
            "experience": "X years",
            "skills": ["skill1", "skill2", "skill3"],
            "current_role": "Role Title",
            "achievements": ["achievement1", "achievement2"]
        }}

        If any information is not available, use "Not specified" for that field.
        """
        
        personal_info_response = self.llm.invoke([SystemMessage(content=personal_info_prompt)])
        try:
            personal_info = json.loads(personal_info_response.content)
        except json.JSONDecodeError:
            personal_info = {
                "name": "Not specified",
                "experience": "Not specified",
                "skills": ["Not specified"],
                "current_role": "Not specified",
                "achievements": ["Not specified"]
            }
        
        # System message that explains the task
        system_prompt = f"""
        You are an expert AI interviewer specializing in technical interviews. Your task is to conduct a job interview based on the provided job description and the candidate's resume.
        
        JOB DESCRIPTION:
        {self.job_description}
        
        CANDIDATE'S INFORMATION:
        Name: {personal_info['name']}
        Experience: {personal_info['experience']}
        Current Role: {personal_info['current_role']}
        Key Skills: {', '.join(personal_info['skills'])}
        Notable Achievements: {', '.join(personal_info['achievements'])}
        
        First, analyze if the candidate's resume matches the job requirements. If there's a significant mismatch, respond with ONLY this message:
        "Hello {personal_info['name']}, I've reviewed your resume and the job requirements. Unfortunately, there seems to be a significant mismatch between your experience and the role's requirements. The position requires [specific requirements from JD] which are not reflected in your background. Would you like to proceed with the interview anyway?"

        If the resume is a good match, respond with ONLY this introduction:
        "Hello {personal_info['name']}, I'm your AI interviewer today. I see you have {personal_info['experience']} of experience, currently working as {personal_info['current_role']}. I'll be conducting a technical interview focused on [specific tech stack from JD]. I'm particularly interested in your experience with {', '.join(personal_info['skills'][:3])}."

        DO NOT include any questions in this response. The first question will be asked in the next interaction.
        """
        
        response = self.llm.invoke([SystemMessage(content=system_prompt)])
        introduction = response.content
        
        # Store the introduction in conversation history
        self.conversation_history.append(SystemMessage(content=system_prompt))
        self.conversation_history.append(AIMessage(content=introduction))
        
        # Generate the first question
        question_prompt = f"""
        Based on the job description and candidate's information, ask ONE specific technical question.
        
        JOB DESCRIPTION:
        {self.job_description}
        
        CANDIDATE'S INFORMATION:
        Name: {personal_info['name']}
        Experience: {personal_info['experience']}
        Current Role: {personal_info['current_role']}
        Key Skills: {', '.join(personal_info['skills'])}
        Notable Achievements: {', '.join(personal_info['achievements'])}

        The question should:
        1. Be specific to their experience and current role
        2. Reference their notable achievements if relevant
        3. Focus on their primary technical skills
        4. Be tailored to the job requirements

        Examples of good questions:
        - For senior roles: "Given your experience with [specific technology], could you walk me through a complex system you designed and the challenges you faced?"
        - For mid-level roles: "I see you've worked with [specific technology]. Can you describe a challenging feature you implemented and how you handled it?"
        - For junior roles: "Tell me about a project where you used [specific technology]. What was your role and what did you learn?"

        Respond with ONLY the question, no additional text or context.
        """
        
        question_response = self.llm.invoke([SystemMessage(content=question_prompt)])
        first_question = question_response.content
        
        # Store the first question in conversation history
        self.conversation_history.append(SystemMessage(content=question_prompt))
        self.conversation_history.append(AIMessage(content=first_question))
        
        self.current_question_number = 1
        
        # Generate audio for the question
        audio_data = self._generate_audio(first_question)
        
        # Return the question with audio as a single key-value pair
        return {
            first_question: audio_data,
            "question_number": self.current_question_number
        }
    
    def process_answer(self, answer: str) -> Dict[str, Any]:
        """
        Process the user's answer and generate the next question
        
        Args:
            answer (str): User's answer to the previous question
            
        Returns:
            Dict with next question or completion status
        """
        # First, analyze the answer
        analysis_prompt = f"""
        Analyze the candidate's answer to the previous question. Focus on:
        1. Technical depth of their response
        2. Specific examples provided
        3. Areas that need clarification
        4. Topics to explore further

        Previous Question: {self.conversation_history[-1].content}
        Candidate's Answer: {answer}

        Provide a brief analysis in this format:
        "Analysis: [2-3 sentences about the answer quality and areas to explore]"
        """
        
        analysis_response = self.llm.invoke([SystemMessage(content=analysis_prompt)])
        analysis = analysis_response.content
        
        # Add the answer and analysis to conversation history
        self.conversation_history.append(HumanMessage(content=answer))
        self.conversation_history.append(SystemMessage(content=analysis))
        self.answers.append(answer)
        
        # Check if we've reached the maximum number of questions
        if self.current_question_number >= self.max_questions:
            # Generate a closing message
            closing_prompt = f"""
            The interview is now complete. Generate a professional closing message that:
            1. Thanks the candidate for their time
            2. Acknowledges their participation
            3. Mentions that you'll provide detailed feedback
            4. Keeps it brief and professional

            JOB DESCRIPTION:
            {self.job_description}
            
            CANDIDATE'S RESUME:
            {self.resume}

            CONVERSATION HISTORY:
            {self.conversation_history}

            Respond with ONLY the closing message, no additional text.
            """
            
            closing_response = self.llm.invoke([SystemMessage(content=closing_prompt)])
            closing_message = closing_response.content
            
            # Generate audio for the closing message
            closing_audio = self._generate_audio(closing_message)
            
            return {
                "interview_complete": True,
                closing_message: closing_audio,
                "question_number": self.current_question_number
            }
        
        # Generate the next question based on the conversation
        question_prompt = f"""
        Based on the conversation so far, ask ONE specific technical question. The question should:
        1. Be directly related to the job requirements and candidate's experience
        2. Require specific technical knowledge and examples
        3. Build upon previous answers or explore new relevant areas
        4. Be challenging but fair

        JOB DESCRIPTION:
        {self.job_description}
        
        CANDIDATE'S RESUME:
        {self.resume}

        CONVERSATION HISTORY:
        {self.conversation_history}

        Question Guidelines:
        - For technical roles: Focus on specific technologies, architectures, and problem-solving
        - For senior positions: Include system design, scalability, and leadership aspects
        - For junior positions: Focus on fundamentals and learning ability
        - Always ask for specific examples and implementations

        Examples of good questions:
        - "Can you explain how you implemented [specific feature] in your last project? What challenges did you face?"
        - "How would you design a system to handle [specific requirement]? What components would you use and why?"
        - "Tell me about a time when you had to optimize [specific technology] performance. What was your approach?"

        This is question #{self.current_question_number + 1} out of {self.max_questions}.
        
        Respond with ONLY the question, no additional text or context.
        """
        
        # Generate the next question
        question_response = self.llm.invoke([SystemMessage(content=question_prompt)])
        next_question = question_response.content
        
        # Add the question to conversation history
        self.conversation_history.append(AIMessage(content=next_question))
        
        # Increment question counter
        self.current_question_number += 1
        
        # Generate audio for the question
        audio_data = self._generate_audio(next_question)
        
        return {
            "interview_complete": False,
            next_question: audio_data,
            "question_number": self.current_question_number
        }
    
    def generate_feedback(self) -> Dict[str, Any]:
        """
        Generate comprehensive feedback based on the interview
        
        Returns:
            Dict with feedback components including rating, detailed feedback, and key takeaways
        """
        system_prompt = f"""
        As an expert AI interviewer, provide comprehensive feedback on the candidate's interview performance.
        
        JOB DESCRIPTION:
        {self.job_description}
        
        CANDIDATE'S RESUME:
        {self.resume}
        
        CONVERSATION HISTORY:
        {self.conversation_history}
        
        Based on the interview conversation, generate feedback in the following format:
        
        1. First, assign a rating from 1-5 where:
           - 5: Exceptional candidate, exceeds all requirements
           - 4: Strong candidate, meets most requirements
           - 3: Good candidate, meets basic requirements
           - 2: Below average, needs significant improvement
           - 1: Poor performance, does not meet requirements
        
        2. Then provide a detailed feedback paragraph that covers:
           - Overall assessment of technical knowledge and problem-solving abilities
           - Communication skills and clarity of explanations
           - Specific technical areas of strength
           - Areas that need improvement
           - Final assessment of job fit
        
        3. Finally, provide 10 key takeaways as bullet points that summarize:
           - Technical strengths
           - Communication and soft skills
           - Areas for improvement
           - Growth potential
           - Team fit
        
        Format your response as a JSON object with these exact keys:
        {{
            "rating": <number between 1-5>,
            "feedback": "<detailed feedback text>",
            "keyTakeaways": [
                "<takeaway 1>",
                "<takeaway 2>",
                ...
                "<takeaway 10>"
            ]
        }}
        
        Be honest but constructive, and provide actionable advice. The feedback should be specific to the candidate's performance and relevant to the job requirements.
        
        IMPORTANT: Your response must be valid JSON. Do not include any text before or after the JSON object.
        """
        
        # Create a messages list with conversation history
        messages = [SystemMessage(content=system_prompt)] + self.conversation_history
        
        # Generate the feedback
        response = self.llm.invoke(messages)
        
        try:
            # Parse the response as JSON
            feedback_data = json.loads(response.content)
            
            # Validate the required fields
            required_fields = ["rating", "feedback", "keyTakeaways"]
            if not all(field in feedback_data for field in required_fields):
                raise ValueError("Missing required fields in feedback")
                
            # Validate rating is between 1 and 5
            if not isinstance(feedback_data["rating"], int) or not 1 <= feedback_data["rating"] <= 5:
                feedback_data["rating"] = 3  # Default to middle rating if invalid
                
            # Validate keyTakeaways is a list with 10 items
            if not isinstance(feedback_data["keyTakeaways"], list) or len(feedback_data["keyTakeaways"]) != 10:
                feedback_data["keyTakeaways"] = [
                    "Error in feedback generation",
                    "Manual review recommended",
                    "Please contact support if this persists"
                ] * 3 + ["Error in feedback generation"]
                
            return feedback_data
            
        except json.JSONDecodeError:
            # Fallback in case the response isn't valid JSON
            return {
                "rating": 3,
                "feedback": "Error generating structured feedback. Please review the interview manually.",
                "keyTakeaways": [
                    "Error in feedback generation",
                    "Manual review recommended",
                    "Please contact support if this persists"
                ] * 3 + ["Error in feedback generation"]
            }
