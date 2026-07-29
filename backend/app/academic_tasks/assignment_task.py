from crewai import Task
from app.agents.academic_agents.assignment_agent import AssignmentAgent


class AssignmentTask:

    def build(self):

        return Task(

            description="""
Analyze the assignment.

Provide:

• Solution approach
• Important concepts
• Reference material
• Common mistakes
""",

            expected_output="""
Assignment guidance report.
""",

            agent=AssignmentAgent().build()
        )