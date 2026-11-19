import { fetchWithSession } from "@/lib/auth";

export type TeacherLessonBooking = {
  id: string;
  student_id: string;
  student_name: string;
  student_email: string;
  offer_title: string;
  status: string;
  starts_at: string;
  ends_at: string;
  meeting_url: string | null;
  created_at: string;
};

export async function getTeacherLessons(): Promise<TeacherLessonBooking[]> {
  try {
    const response = await fetchWithSession("/teacher/lessons");
    if (!response.ok) return [];
    return (await response.json()) as TeacherLessonBooking[];
  } catch {
    return [];
  }
}
