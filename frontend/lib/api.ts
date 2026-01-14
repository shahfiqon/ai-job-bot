import type {
  Job,
  JobDetail,
  JobStatus,
  SavedJob,
  SavedJobCheckResponse,
  SavedJobListResponse,
} from "@/types/job";
import type {
  BlockedCompany,
  BlockedCompanyListResponse,
} from "@/types/blocked-company";
import type {
  TailoredResume,
  TailoredResumeListResponse,
} from "@/types/tailored-resume";
import type { ResumeResponse, ResumeUpdate } from "@/types/user";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const AUTH_TOKEN_KEY = "auth_token";

/**
 * Get the auth token from localStorage
 */
function getAuthToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  return localStorage.getItem(AUTH_TOKEN_KEY);
}

/**
 * Get headers with auth token if available
 */
function getAuthHeaders(): HeadersInit {
  const token = getAuthToken();
  const headers: HeadersInit = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

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
    headers: getAuthHeaders(),
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
  // Applicants count filters
  min_applicants_count?: number;
  max_applicants_count?: number;
  // Date posted filters
  date_posted_from?: string; // ISO date string (YYYY-MM-DD)
  date_posted_to?: string; // ISO date string (YYYY-MM-DD)
  // DSPy-parsed filters
  is_python_main?: boolean;
  contract_feasible?: boolean;
  relocate_required?: boolean;
  accepts_non_us?: boolean;
  screening_required?: boolean;
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
    if (filters.min_applicants_count !== undefined) {
      searchParams.append("min_applicants_count", String(filters.min_applicants_count));
    }
    if (filters.max_applicants_count !== undefined) {
      searchParams.append("max_applicants_count", String(filters.max_applicants_count));
    }
    if (filters.date_posted_from) {
      searchParams.append("date_posted_from", filters.date_posted_from);
    }
    if (filters.date_posted_to) {
      searchParams.append("date_posted_to", filters.date_posted_to);
    }
    // DSPy-parsed filters
    if (filters.is_python_main !== undefined) {
      searchParams.append("is_python_main", String(filters.is_python_main));
    }
    if (filters.contract_feasible !== undefined) {
      searchParams.append("contract_feasible", String(filters.contract_feasible));
    }
    if (filters.relocate_required !== undefined) {
      searchParams.append("relocate_required", String(filters.relocate_required));
    }
    if (filters.accepts_non_us !== undefined) {
      searchParams.append("accepts_non_us", String(filters.accepts_non_us));
    }
    if (filters.screening_required !== undefined) {
      searchParams.append("screening_required", String(filters.screening_required));
    }
  }

  const url = `${API_BASE_URL}/api/jobs?${searchParams.toString()}`;

  const response = await fetch(url, {
    next: { revalidate: 60 },
    headers: getAuthHeaders(),
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

/**
 * Save a job for the current user
 */
export async function saveJob(jobId: number, status: JobStatus = "saved"): Promise<SavedJob> {
  const response = await fetch(`${API_BASE_URL}/api/saved-jobs`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({
      job_id: jobId,
      status,
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to save job" }));
    throw new ApiError(
      error.detail || "Failed to save job",
      response.status,
      response
    );
  }

  const data = await response.json();
  return data;
}

/**
 * Get saved jobs for the current user
 */
export async function getSavedJobs(
  page: number = 1,
  pageSize: number = 20,
  status?: JobStatus
): Promise<SavedJobListResponse> {
  const searchParams = new URLSearchParams();
  searchParams.append("page", String(page));
  searchParams.append("page_size", String(pageSize));
  if (status) {
    searchParams.append("status", status);
  }

  const url = `${API_BASE_URL}/api/saved-jobs?${searchParams.toString()}`;

  const response = await fetch(url, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new ApiError(
      `Failed to fetch saved jobs: ${response.statusText}`,
      response.status,
      response
    );
  }

  const data = await response.json();
  return data;
}

/**
 * Update a saved job's status and/or notes
 */
export async function updateSavedJobStatus(
  savedJobId: number,
  status?: JobStatus,
  notes?: string | null
): Promise<SavedJob> {
  const body: { status?: JobStatus; notes?: string | null } = {};
  if (status !== undefined) {
    body.status = status;
  }
  if (notes !== undefined) {
    body.notes = notes;
  }

  const response = await fetch(`${API_BASE_URL}/api/saved-jobs/${savedJobId}`, {
    method: "PATCH",
    headers: getAuthHeaders(),
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to update saved job" }));
    throw new ApiError(
      error.detail || "Failed to update saved job",
      response.status,
      response
    );
  }

  const data = await response.json();
  return data;
}

/**
 * Delete a saved job
 */
export async function deleteSavedJob(savedJobId: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/saved-jobs/${savedJobId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to delete saved job" }));
    throw new ApiError(
      error.detail || "Failed to delete saved job",
      response.status,
      response
    );
  }
}

/**
 * Check if a job is saved by the current user
 */
export async function checkJobSaved(jobId: number): Promise<SavedJobCheckResponse> {
  const response = await fetch(`${API_BASE_URL}/api/saved-jobs/jobs/${jobId}/saved`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new ApiError(
      `Failed to check saved job: ${response.statusText}`,
      response.status,
      response
    );
  }

  const data = await response.json();
  return data;
}

/**
 * Block a company for the current user
 */
export async function blockCompany(companyId: number): Promise<BlockedCompany> {
  const response = await fetch(`${API_BASE_URL}/api/blocked-companies`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({
      company_id: companyId,
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to block company" }));
    throw new ApiError(
      error.detail || "Failed to block company",
      response.status,
      response
    );
  }

  const data = await response.json();
  return data;
}

/**
 * Unblock a company for the current user
 */
export async function unblockCompany(companyId: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/blocked-companies/${companyId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to unblock company" }));
    throw new ApiError(
      error.detail || "Failed to unblock company",
      response.status,
      response
    );
  }
}

/**
 * Get blocked companies for the current user
 */
export async function fetchBlockedCompanies(
  page: number = 1,
  pageSize: number = 20
): Promise<BlockedCompanyListResponse> {
  const searchParams = new URLSearchParams();
  searchParams.append("page", String(page));
  searchParams.append("page_size", String(pageSize));

  const url = `${API_BASE_URL}/api/blocked-companies?${searchParams.toString()}`;

  const response = await fetch(url, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new ApiError(
      `Failed to fetch blocked companies: ${response.statusText}`,
      response.status,
      response
    );
  }

  const data = await response.json();
  return data;
}

/**
 * Fetch resume JSON for the current user
 */
export async function fetchResume(): Promise<ResumeResponse> {
  const response = await fetch(`${API_BASE_URL}/api/profile/resume`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new ApiError(
      `Failed to fetch resume: ${response.statusText}`,
      response.status,
      response
    );
  }

  const data = await response.json();
  return data;
}

/**
 * Update resume JSON for the current user
 */
export async function updateResume(resumeJson: string | null): Promise<ResumeResponse> {
  const response = await fetch(`${API_BASE_URL}/api/profile/resume`, {
    method: "PUT",
    headers: getAuthHeaders(),
    body: JSON.stringify({
      resume_json: resumeJson,
    } as ResumeUpdate),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to update resume" }));
    throw new ApiError(
      error.detail || "Failed to update resume",
      response.status,
      response
    );
  }

  const data = await response.json();
  return data;
}

/**
 * Generate a tailored resume for a specific job
 */
export async function generateTailoredResume(jobId: number): Promise<TailoredResume> {
  const response = await fetch(`${API_BASE_URL}/api/tailored-resumes/generate/${jobId}`, {
    method: "POST",
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to generate tailored resume" }));
    throw new ApiError(
      error.detail || "Failed to generate tailored resume",
      response.status,
      response
    );
  }

  const data = await response.json();
  return data;
}

/**
 * Get tailored resume for a specific job
 */
export async function getTailoredResume(jobId: number): Promise<TailoredResume> {
  const response = await fetch(`${API_BASE_URL}/api/tailored-resumes/${jobId}`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    if (response.status === 404) {
      throw new ApiError(
        "Tailored resume not found for this job",
        response.status,
        response
      );
    }
    throw new ApiError(
      `Failed to fetch tailored resume: ${response.statusText}`,
      response.status,
      response
    );
  }

  const data = await response.json();
  return data;
}

/**
 * List all tailored resumes for the current user
 */
export async function listTailoredResumes(
  page: number = 1,
  pageSize: number = 20
): Promise<TailoredResumeListResponse> {
  const searchParams = new URLSearchParams();
  searchParams.append("page", String(page));
  searchParams.append("page_size", String(pageSize));

  const url = `${API_BASE_URL}/api/tailored-resumes?${searchParams.toString()}`;

  const response = await fetch(url, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new ApiError(
      `Failed to fetch tailored resumes: ${response.statusText}`,
      response.status,
      response
    );
  }

  const data = await response.json();
  return data;
}

/**
 * Update tailored resume for a specific job
 */
export async function updateTailoredResume(
  jobId: number,
  tailoredResumeJson: string
): Promise<TailoredResume> {
  const response = await fetch(`${API_BASE_URL}/api/tailored-resumes/${jobId}`, {
    method: "PUT",
    headers: getAuthHeaders(),
    body: JSON.stringify({
      tailored_resume_json: tailoredResumeJson,
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to update tailored resume" }));
    throw new ApiError(
      error.detail || "Failed to update tailored resume",
      response.status,
      response
    );
  }

  const data = await response.json();
  return data;
}

/**
 * Generate PDF for a tailored resume
 */
export async function generateTailoredResumePDF(jobId: number): Promise<TailoredResume> {
  const response = await fetch(`${API_BASE_URL}/api/tailored-resumes/${jobId}/generate-pdf`, {
    method: "POST",
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to generate PDF" }));
    throw new ApiError(
      error.detail || "Failed to generate PDF",
      response.status,
      response
    );
  }

  const data = await response.json();
  return data;
}

/**
 * Download PDF for a tailored resume
 */
export async function downloadTailoredResumePDF(jobId: number): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}/api/tailored-resumes/${jobId}/download`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to download PDF" }));
    throw new ApiError(
      error.detail || "Failed to download PDF",
      response.status,
      response
    );
  }

  const blob = await response.blob();
  return blob;
}

/**
 * Mark all unseen jobs as seen for the current user
 */
export async function markAllJobsAsSeen(): Promise<{ message: string; jobs_marked: number }> {
  const response = await fetch(`${API_BASE_URL}/api/seen-jobs/mark-all-as-seen`, {
    method: "POST",
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to mark jobs as seen" }));
    throw new ApiError(
      error.detail || "Failed to mark jobs as seen",
      response.status,
      response
    );
  }

  const data = await response.json();
  return data;
}

