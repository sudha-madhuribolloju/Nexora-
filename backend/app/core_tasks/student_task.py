from crewai import Task
from app.agents.student_agent import StudentAgent


class StudentTask:

    def build(self):

        student = StudentAgent().build()

        return Task(

            description="""
Participate in today's lecture.

Responsibilities:

• Listen carefully
• Ask intelligent questions
• Answer teacher questions
• Take notes
• Identify confusing topics
""",

            expected_output="""
Student participation report including:

- Notes
- Questions
- Answers
- Learning Progress
""",

            agent=student
        )