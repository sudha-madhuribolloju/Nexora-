from crewai import Agent


class ExamPreparationAgent:

    def build(self):

        return Agent(

            role="Exam Preparation Coach",

            goal="""
Prepare students for examinations through
revision plans and mock tests.
""",

            backstory="""
Expert in exam strategies,
revision planning,
memory techniques,
and question prediction.
""",

            verbose=True,
           memory=True,
           allow_delegation=False
        )