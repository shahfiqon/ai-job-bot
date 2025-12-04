export interface TailoredResume {
  id: number;
  user_id: number;
  job_id: number;
  tailored_resume_json: string;
  pdf_path: string | null;
  pdf_generated: boolean;
  created_at: string;
  updated_at: string;
}

export interface TailoredResumeListItem {
  id: number;
  user_id: number;
  job_id: number;
  tailored_resume_json: string;
  pdf_path: string | null;
  pdf_generated: boolean;
  created_at: string;
  updated_at: string;
  job_title: string | null;
  company_name: string | null;
}

export interface TailoredResumeListResponse {
  tailored_resumes: TailoredResumeListItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

