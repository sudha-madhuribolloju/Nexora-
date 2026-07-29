from crewai import Agent


class RecommendationAgent:

    def build(self):

        return Agent(

            role="Learning Recommendation Expert",

            goal="""
Provide personalized learning recommendations
based on student performance and learning behaviour.
""",

            backstory="""
You analyze learning patterns and recommend:

• Study material
• Videos
• Books
• Practice questions
• Revision plans
• Learning paths
""",

            verbose=True,
            memory=True,
            allow_delegation=False
        )