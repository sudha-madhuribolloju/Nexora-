from crewai import Task
from app.agents.academic_agents.PDFTutor_agent import PDFTutorAgent


class PDFTutorTask:

    def build(self):

        return Task(

            description="""
Study the uploaded PDF.

Generate:

• Summary
• Chapter-wise explanation
• Important concepts
• FAQs
• Quiz questions
""",

            expected_output="""
Complete PDF learning report.
""",

            agent=PDFTutorAgent().build()
        )