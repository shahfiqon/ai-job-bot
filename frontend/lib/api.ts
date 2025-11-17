import type { Job, JobDetail } from "@/types/job";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  statusCode: number;
  response?: Response;

  constructor(message: string, statusCode: number, response?: Response) {
    super(message);
    this.name = "ApiError";
    this.statusCode = statusCode;
    this.response = response;
  }
}

/**
 * Fetch a job by its ID from the API
 */
export async function fetchJobById(id: number): Promise<JobDetail> {
  const response = await fetch(`${API_BASE_URL}/api/jobs/${id}`, {
    next: { revalidate: 60 }, // Cache for 60 seconds
  });

  if (!response.ok) {
    throw new ApiError(
      `Failed to fetch job: ${response.statusText}`,
      response.status,
      response
    );
  }

  const data = await response.json();
  return data;
}

export interface JobFilters {
  search?: string;
  location?: string;
  job_type?: string[];
  is_remote?: boolean;
  page?: number;
  page_size?: number;
  // LLM-parsed filters
  job_categories?: string[];
  technologies?: string[];
  required_skills?: string[];
  work_arrangement?: string;
  min_years_experience?: number;
  independent_contractor_friendly?: boolean;
  has_own_products?: boolean;
  is_recruiting_company?: boolean;
  min_employee_size?: number;
  max_employee_size?: number;
}

/**
 * Fetch jobs with optional filters
 */
export async function fetchJobs(
  page: number = 1,
  pageSize: number = 20,
  filters?: JobFilters
): Promise<{ jobs: Job[]; total: number; page: number; page_size: number; total_pages: number }> {
  const searchParams = new URLSearchParams();

  // Pagination
  searchParams.append("page", String(page));
  searchParams.append("page_size", String(pageSize));

  // Apply filters if provided
  if (filters) {
    if (filters.search) searchParams.append("search", filters.search);
    if (filters.location) searchParams.append("location", filters.location);
    if (filters.job_type?.length) {
      filters.job_type.forEach((type) => searchParams.append("job_type", type));
    }
    if (filters.is_remote !== undefined) {
      searchParams.append("is_remote", String(filters.is_remote));
    }
    
    // LLM-parsed filters
    if (filters.job_categories?.length) {
      searchParams.append("job_categories", filters.job_categories.join(","));
    }
    if (filters.technologies?.length) {
      searchParams.append("technologies", filters.technologies.join(","));
    }
    if (filters.required_skills?.length) {
      searchParams.append("required_skills", filters.required_skills.join(","));
    }
    if (filters.work_arrangement) {
      searchParams.append("work_arrangement", filters.work_arrangement);
    }
    if (filters.min_years_experience !== undefined) {
      searchParams.append("min_years_experience", String(filters.min_years_experience));
    }
    if (filters.independent_contractor_friendly !== undefined) {
      searchParams.append("independent_contractor_friendly", String(filters.independent_contractor_friendly));
    }
    if (filters.has_own_products !== undefined) {
      searchParams.append("has_own_products", String(filters.has_own_products));
    }
    if (filters.is_recruiting_company !== undefined) {
      searchParams.append("is_recruiting_company", String(filters.is_recruiting_company));
    }
    if (filters.min_employee_size !== undefined) {
      searchParams.append("min_employee_size", String(filters.min_employee_size));
    }
    if (filters.max_employee_size !== undefined) {
      searchParams.append("max_employee_size", String(filters.max_employee_size));
    }
  }

  const url = `${API_BASE_URL}/api/jobs?${searchParams.toString()}`;

  const response = await fetch(url, {
    next: { revalidate: 60 },
  });

  if (!response.ok) {
    throw new ApiError(
      `Failed to fetch jobs: ${response.statusText}`,
      response.status,
      response
    );
  }

  const data = await response.json();
  return data;
}

