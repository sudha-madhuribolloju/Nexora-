from crewai import Task
from app.agents.platform_agents.recommendation_agent import RecommendationAgent


class RecommendationTask:

    def build(self):

        return Task(

            description="""
Analyze learning behaviour.

Recommend:

• Books
• Videos
• Practice Exercises
• Weak Topics
• Daily Study Plan
""",

            expected_output="Personalized learning recommendations.",

            agent=RecommendationAgent().build()
        )