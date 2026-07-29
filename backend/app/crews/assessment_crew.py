from crewai import Crew, Process

from app.agents.quiz import QuizAgent
from app.agents.academic_agents.exampreparation_agent import ExamPreparationAgent
from app.agents.academic_agents.academicprogress_agent import AcademicProgressAgent

from app.tasks.quiz_task import QuizTask
from app.tasks.academic_tasks.exampreparation_task import ExamPreparationTask
from app.tasks.academic_tasks.academicprogress_task import AcademicProgressTask


class AssessmentCrew:

    def build():

        return Crew(

            agents=[
                QuizAgent().build(),
                ExamPreparationAgent().build(),
                AcademicProgressAgent().build()
            ],

            tasks=[
                QuizTask().build(),
                ExamPreparationTask().build(),
                AcademicProgressTask().build()
            ],

            process=Process.sequential,

            verbose=True
        )