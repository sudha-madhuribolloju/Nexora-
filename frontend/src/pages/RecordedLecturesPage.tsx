import React from "react";
import { ModuleRecordedLectures } from "../components/ModuleRecordedLectures";

interface RecordedLecturesPageProps {
  userRole?: string | null;
  userId?: string | null;
}

export const RecordedLecturesPage: React.FC<RecordedLecturesPageProps> = ({
  userRole = "Student",
  userId = "",
}) => {
  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <ModuleRecordedLectures userRole={userRole} userId={userId} />
    </div>
  );
};

export default RecordedLecturesPage;
