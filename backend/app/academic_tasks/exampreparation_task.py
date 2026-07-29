from crewai import Task
from app.agents.academic_agents.exampreparation_agent import ExamPreparationAgent


class ExamPreparationTask:

    def build(self):

        return Task(

            description="""
Create an exam preparation plan.

Include:

• Important topics
• Revision schedule
• Practice questions
• Mock test recommendations
""",

            expected_output="""
Personalized exam preparation guide.
""",

            agent=ExamPreparationAgent().build()
        )