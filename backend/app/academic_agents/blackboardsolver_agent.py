from crewai import Agent


class BlackboardSolverAgent:

    def build(self):

        return Agent(

            role="Blackboard Problem Solver",

            goal="""
Solve problems written on classroom blackboards
step-by-step with clear explanations.
""",

            backstory="""
Expert educator capable of solving mathematics,
science, engineering and programming problems.
""",

            verbose=True,
           memory=True,
           allow_delegation=False
        )