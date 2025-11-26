import type { Company } from "./job";

export interface BlockedCompany {
  id: number;
  user_id: number;
  company_id: number;
  created_at: Date;
  company: Company;
}

export interface BlockedCompanyListResponse {
  blocked_companies: BlockedCompany[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}






