from crewai import Task
from app.agents.academic_agents.blackboardsolver_agent import BlackboardSolverAgent


class BlackboardSolverTask:

    def build(self):

        return Task(

            description="""
Solve the classroom problem.

Provide:

• Step-by-step solution
• Formula explanation
• Final answer
• Alternative approach
""",

            expected_output="""
Detailed solved explanation.
""",

            agent=BlackboardSolverAgent().build()
        )