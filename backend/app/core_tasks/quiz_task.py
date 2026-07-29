from crewai import Task
from app.agents.quiz import QuizAgent


class QuizTask:

    def build(self):

        quiz = QuizAgent().build()

        return Task(

            description="""
Generate a classroom quiz from today's lecture.

Include:

• 10 MCQs
• 5 True/False
• 5 Short Answer
• Answers
• Explanations
""",

            expected_output="""
A complete quiz with answers,
difficulty level and marks.
""",

            agent=quiz
        )