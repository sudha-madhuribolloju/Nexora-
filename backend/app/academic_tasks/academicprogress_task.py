from crewai import Task
from app.agents.academic_agents.academicprogress_agent import AcademicProgressAgent


class AcademicProgressTask:

    def build(self):

        return Task(

            description="""
Analyze a student's academic performance.

Evaluate:

• Attendance
• Quiz Scores
• Assignment Scores
• Weak Subjects
• Strong Subjects
• Learning Trend

Generate personalized recommendations.
""",

            expected_output="""
A detailed academic progress report.
""",

            agent=AcademicProgressAgent().build()
        )