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
  emails: string[] | null;
  created_at: Date;
  updated_at: Date;
}

export interface Company {
  id: number;
  linkedin_url: string;
  linkedin_internal_id: string | null;
  name: string;
  description: string | null;
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
