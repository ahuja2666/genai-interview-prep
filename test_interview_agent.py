
"""
Test script for the InterviewAgent class.
This script allows you to test the interview agent without running the web server.
"""

from interview_agent import InterviewAgent
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_interview():
    """Run a test interview"""
    job_description = """
    Senior Python Developer
    
    We are seeking a skilled Senior Python Developer with at least 5 years of experience to join our growing team. 
    The ideal candidate will have deep knowledge of Python, Flask or Django, and experience with machine learning libraries.
    
    Responsibilities:
    - Design, build and maintain efficient, reusable, and reliable Python code
    - Integrate user-facing elements with server-side logic
    - Implement security and data protection measures
    - Develop and maintain machine learning models
    - Work with data scientists to implement algorithms
    
    Requirements:
    - 5+ years of Python development experience
    - Proficient in one or more Python frameworks (Flask, Django)
    - Experience with machine learning libraries (scikit-learn, TensorFlow, PyTorch)
    - Knowledge of database technologies (SQL, NoSQL)
    - Experience with version control (Git)
    - Good understanding of RESTful APIs
    - Familiarity with frontend technologies (HTML, CSS, JavaScript)
    """
    
    resume = """
    Jane Smith
    Senior Software Engineer
    
    Professional Summary:
    Experienced Python developer with 6 years of experience building web applications and machine learning solutions.
    Skilled in Flask, Django, and various ML libraries.
    
    Experience:
    
    ABC Tech (2020-Present)
    Senior Python Developer
    - Developed and maintained multiple Flask applications for financial data analysis
    - Implemented machine learning models for predictive analytics using scikit-learn
    - Optimized database queries resulting in 40% performance improvement
    - Mentored junior developers and conducted code reviews
    
    XYZ Solutions (2018-2020)
    Python Developer
    - Built RESTful APIs using Django REST framework
    - Developed data pipelines for processing large datasets
    - Implemented automated testing for critical components
    
    Skills:
    - Programming Languages: Python (expert), JavaScript, SQL
    - Frameworks: Flask, Django, FastAPI
    - ML Libraries: scikit-learn, TensorFlow, PyTorch
    - Databases: PostgreSQL, MongoDB
    - Tools: Git, Docker, CI/CD
    
    Education:
    Bachelor of Science in Computer Science, University of Technology (2018)
    """
    
    # Create the interview agent
    agent = InterviewAgent(
        job_description=job_description,
        resume=resume,
        max_questions=3  # Using 3 for testing purposes
    )
    
    # Start the interview
    first_question = agent.start_interview()
    print(f"Question 1: {first_question}\n")
    
    # Simulate answers
    answers = [
        "I have been using Python professionally for 6 years now, primarily working with Flask for web applications and scikit-learn for machine learning models. At ABC Tech, I've built several Flask applications that analyze financial data and make predictions using ML algorithms.",
        "One of the most challenging projects I worked on was building a real-time fraud detection system. The challenge was processing transactions quickly while maintaining high accuracy. I solved this by implementing a two-stage approach: a fast rule-based filter followed by a more complex ML model only for suspicious transactions.",
        "Yes, I have experience with both SQL and NoSQL databases. I've worked extensively with PostgreSQL for relational data and MongoDB for document storage. At ABC Tech, I optimized several complex SQL queries that improved our application performance by 40%."
    ]
    
    # Process each answer
    for i, answer in enumerate(answers):
        print(f"User Answer {i+1}: {answer}\n")
        response = agent.process_answer(answer)
        
        if response.get("interview_complete", False):
            print("Interview complete!\n")
            break
        else:
            print(f"Question {response['question_number']}: {response['next_question']}\n")
    
    # Generate feedback
    feedback = agent.generate_feedback()
    print("Interview Feedback:")
    print(feedback["detailed_feedback"])

if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set. Please create a .env file with your API key.")
    else:
        test_interview()
