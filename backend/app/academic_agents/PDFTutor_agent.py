from crewai import Agent


class PDFTutorAgent:

    def build(self):

        return Agent(

            role="PDF Learning Tutor",

            goal="""
Teach students using uploaded PDFs
and answer questions accurately.
""",

            backstory="""
Specialist in extracting knowledge
from textbooks,
research papers,
lecture notes,
and PDFs.
""",

            verbose=True,
           memory=True,
           allow_delegation=False
        )