from crewai import Crew, Process

from app.agents.academic_agents.notes_agent import NotesAgent
from app.agents.academic_agents.assignment_agent import AssignmentAgent
from app.agents.academic_agents.blackboardsolver_agent import BlackboardSolverAgent
from app.agents.academic_agents.PDFTutor_agent import PDFTutorAgent

from app.tasks.academic_tasks.notes_task import NotesTask
from app.tasks.academic_tasks.assignment_task import AssignmentTask
from app.tasks.academic_tasks.blackboardsolver_task import BlackboardSolverTask
from app.tasks.academic_tasks.PDFTutor_task import PDFTutorTask


class AcademicCrew:

    def build():

        return Crew(

            agents=[
                NotesAgent().build(),
                AssignmentAgent().build(),
                BlackboardSolverAgent().build(),
                PDFTutorAgent().build()
            ],

            tasks=[
                NotesTask().build(),
                AssignmentTask().build(),
                BlackboardSolverTask().build(),
                PDFTutorTask().build()
            ],

            process=Process.sequential,

            verbose=True
        )