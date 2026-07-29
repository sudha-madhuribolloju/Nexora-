from crewai import Crew, Process

from app.agents.platform_agents.admin_agent import AdminAgent
from app.agents.platform_agents.notification_agent import NotificationAgent
from app.agents.platform_agents.sessionmanager_agent import SessionManagerAgent
from app.agents.platform_agents.transcriptprocessing_agent import TranscriptProcessingAgent
from app.agents.platform_agents.voicerecognition_agent import VoiceRecognitionAgent

from app.tasks.platform_tasks.admin_task import AdminTask
from app.tasks.platform_tasks.notification_task import NotificationTask
from app.tasks.platform_tasks.sessionmanager_task import SessionManagerTask
from app.tasks.platform_tasks.transcriptprocessing_task import TranscriptProcessingTask
from app.tasks.platform_tasks.voicerecognition_task import VoiceRecognitionTask


class PlatformCrew:

    def build():

        return Crew(

            agents=[
                AdminAgent().build(),
                NotificationAgent().build(),
                SessionManagerAgent().build(),
                TranscriptProcessingAgent().build(),
                VoiceRecognitionAgent().build()
            ],

            tasks=[
                AdminTask().build(),
                NotificationTask().build(),
                SessionManagerTask().build(),
                TranscriptProcessingTask().build(),
                VoiceRecognitionTask().build()
            ],

            process=Process.sequential,

            verbose=True
        )