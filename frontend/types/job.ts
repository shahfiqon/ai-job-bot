export type JobType =
  | "Full-time"
  | "Part-time"
  | "Contract"
  | "Internship"
  | "Temporary";

export type CompensationInterval = "yearly" | "monthly" | "weekly" | "hourly";

export type JobLevel =
  | "Entry"
  | "Mid"
  | "Senior"
  | "Lead"
  | "Principal"
  | "Director";

export type JobStatus = "saved" | "applied" | "interview" | "declined";

export interface Job {
  id: number;
  job_url: string | null;
  job_url_direct: string | null;
  title: string;
  company_name: string | null;
  company_id: number | null;
  description: string | null;
  company_url: string | null;
  company_url_direct: string | null;
  location_city: string | null;
  location_state: string | null;
  location_country: string | null;
  compensation_min: number | null;
  compensation_max: number | null;
  compensation_currency: string | null;
  compensation_interval: CompensationInterval | null;
  job_type: JobType[] | null;
  date_posted: Date | null;
  is_remote: boolean | null;
  listing_type: string | null;
  job_level: JobLevel | null;
  job_function: string | null;
  company_industry: string | null;
  company_headquarters: string | null;
  company_employees_count: string | null;
  applicants_count: number | null;
  // Company employee size fields (from Company model)
  company_size_min: number | null;
  company_size_max: number | null;
  company_size_on_linkedin: number | null;
  emails: string[] | null;
  
  // LLM-parsed fields from job description
  required_skills: string[] | null;
  preferred_skills: string[] | null;
  required_years_experience: number | null;
  required_education: string | null;
  preferred_education: string | null;
  responsibilities: string[] | null;
  benefits: string[] | null;
  work_arrangement: string | null;
  team_size: string | null;
  technologies: string[] | null;
  culture_keywords: string[] | null;
  summary: string | null;
  job_categories: string[] | null;
  independent_contractor_friendly: boolean | null;
  parsed_salary_currency: string | null;
  parsed_salary_min: number | null;
  parsed_salary_max: number | null;
  compensation_basis: string | null;
  location_restrictions: string[] | null;
  exclusive_location_requirement: boolean | null;
  
  // DSPy-parsed fields from job description
  is_python_main: boolean | null;
  contract_feasible: boolean | null;
  relocate_required: boolean | null;
  specific_locations: string[] | null;
  accepts_non_us: boolean | null;
  screening_required: boolean | null;
  
  created_at: Date;
  updated_at: Date;
}

export interface Company {
  id: number;
  linkedin_url: string;
  linkedin_internal_id: string | null;
  name: string;
  description: string | null;
  has_own_products: boolean | null;
  is_recruiting_company: boolean | null;
  website: string | null;
  industry: string | null;
  company_size_min: number | null;
  company_size_max: number | null;
  company_size_on_linkedin: number | null;
  hq_country: string | null;
  hq_city: string | null;
  hq_state: string | null;
  hq_postal_code: string | null;
  company_type: string | null;
  founded_year: number | null;
  tagline: string | null;
  universal_name_id: string | null;
  profile_pic_url: string | null;
  background_cover_image_url: string | null;
  specialities: string[] | null;
  locations: Array<Record<string, unknown>> | null;
  created_at: Date;
  updated_at: Date;
}

export interface JobDetail extends Job {
  company: Company | null;
}

export interface SavedJob {
  id: number;
  user_id: number;
  job_id: number;
  status: JobStatus;
  notes: string | null;
  created_at: Date;
  updated_at: Date;
  job: JobDetail;
}

export interface SavedJobListResponse {
  saved_jobs: SavedJob[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface SavedJobCheckResponse {
  is_saved: boolean;
  saved_job_id: number | null;
  status: JobStatus | null;
}
