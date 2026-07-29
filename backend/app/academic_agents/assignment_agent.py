from crewai import Agent


class AssignmentAgent:

    def build(self):

        return Agent(

            role="Assignment Assistant",

            goal="Help students complete assignments correctly.",

            backstory="""
You assist students by explaining assignment questions,
providing hints, checking answers,
and ensuring originality.
""",

            verbose=True,
            memory=True,
            allow_delegation=False
        )