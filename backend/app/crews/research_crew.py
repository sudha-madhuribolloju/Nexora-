from crewai import Crew, Process

from app.agents.research_agent import ResearchAgent

from app.tasks.research_task import ResearchTask


class ResearchCrew:

    def build():

        return Crew(

            agents=[
                ResearchAgent().build()
            ],

            tasks=[
                ResearchTask().build()
            ],

            process=Process.sequential,

            verbose=True
        )