from crewai import Crew, Process

from app.agents.analytics import AnalyticsAgent
from app.agents.platform_agents.recommendation_agent import RecommendationAgent

from app.tasks.analytics_task import AnalyticsTask
from app.tasks.platform_tasks.recommendation_task import RecommendationTask


class AnalyticsCrew:

    def build():

        return Crew(

            agents=[
                AnalyticsAgent().build(),
                RecommendationAgent().build()
            ],

            tasks=[
                AnalyticsTask().build(),
                RecommendationTask().build()
            ],

            process=Process.sequential,

            verbose=True
        )