"use client";

import { useState } from "react";
import { Ban, Briefcase, DollarSign, MapPin } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { Job, JobType } from "@/types/job";
import { blockCompany } from "@/lib/api";
import { formatCurrency, formatDateRelative, formatDateAbsolute } from "@/lib/utils";

type JobsTableProps = {
  jobs: Job[];
  onJobBlocked?: (jobId: number) => void;
};

const JobsTable = ({ jobs, onJobBlocked }: JobsTableProps) => {
  const [blockingIds, setBlockingIds] = useState<Set<number>>(new Set());

  const handleBlockCompany = async (e: React.MouseEvent, job: Job) => {
    e.stopPropagation(); // Prevent row click
    
    if (!job.company_id) {
      alert("This job has no associated company to block.");
      return;
    }

    const companyName = job.company_name || "this company";
    if (!confirm(`Are you sure you want to block ${companyName}? All jobs from this company will be hidden from your search results.`)) {
      return;
    }

    setBlockingIds((prev) => new Set(prev).add(job.id));
    try {
      await blockCompany(job.company_id);
      // Optimistically remove job from list
      if (onJobBlocked) {
        onJobBlocked(job.id);
      }
    } catch (err) {
      console.error("Failed to block company:", err);
      alert(err instanceof Error ? err.message : "Failed to block company");
    } finally {
      setBlockingIds((prev) => {
        const next = new Set(prev);
        next.delete(job.id);
        return next;
      });
    }
  };

  if (!jobs?.length) {
    return (
      <div className="rounded-lg border bg-card p-8 text-center text-muted-foreground">
        No jobs found. Try adjusting your search criteria.
      </div>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="w-[280px]">Job Title</TableHead>
          <TableHead className="hidden md:table-cell">Location</TableHead>
          <TableHead>Type</TableHead>
          <TableHead className="hidden lg:table-cell">Salary</TableHead>
          <TableHead className="hidden md:table-cell">Applicants</TableHead>
          <TableHead>Posted</TableHead>
          <TableHead className="w-[80px]">Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {jobs.map((job) => {
          const locationLabel = formatLocation(job);

          return (
            <TableRow
              className="cursor-pointer"
              key={`${job.id}-${job.title}`}
              role="link"
              tabIndex={0}
              onClick={() => window.open(`/jobs/${job.id}`, "_blank", "noopener,noreferrer")}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  window.open(`/jobs/${job.id}`, "_blank", "noopener,noreferrer");
                }
              }}
            >
              <TableCell className="space-y-2">
                <div className="space-y-1">
                  <span className="text-base font-semibold text-foreground transition-colors hover:text-primary">
                    {job.title}
                  </span>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Briefcase className="h-4 w-4" />
                    <span>{job.company_name ?? "Confidential company"}</span>
                  </div>
                  {/* Display job categories and technologies */}
                  <div className="flex flex-wrap gap-1 mt-2">
                    {job.job_categories?.slice(0, 3).map((category) => (
                      <Badge key={category} variant="secondary" className="text-xs">
                        {category}
                      </Badge>
                    ))}
                    {job.technologies?.slice(0, 3).map((tech) => (
                      <Badge key={tech} variant="outline" className="text-xs">
                        {tech}
                      </Badge>
                    ))}
                  </div>
                  {job.work_arrangement && (
                    <div className="text-xs text-muted-foreground mt-1">
                      {job.work_arrangement}
                    </div>
                  )}
                </div>
              </TableCell>
              <TableCell className="hidden text-sm text-muted-foreground md:table-cell">
                <div className="flex flex-col gap-2">
                  {locationLabel ? (
                    <div className="flex items-center gap-2">
                      <MapPin className="h-4 w-4" />
                      <span>{locationLabel}</span>
                    </div>
                  ) : null}
                  {job.is_remote ? (
                    <Badge variant="secondary" className="w-fit">
                      Remote
                    </Badge>
                  ) : null}
                  {formatEmployeeSize(job) && (
                    <div className="text-xs text-muted-foreground">
                      {formatEmployeeSize(job)}
                    </div>
                  )}
                </div>
              </TableCell>
              <TableCell>
                <div className="flex flex-wrap items-center gap-1">
                  {job.job_type?.length ? (
                    job.job_type.map((type) => (
                      <Badge
                        key={`${job.id}-${type}`}
                        variant={getJobTypeBadgeVariant(type)}
                      >
                        {type}
                      </Badge>
                    ))
                  ) : (
                    <Badge variant="outline">N/A</Badge>
                  )}
                </div>
              </TableCell>
              <TableCell className="hidden text-sm text-muted-foreground lg:table-cell">
                <div className="flex items-center gap-2">
                  <DollarSign className="h-4 w-4" />
                  <span>{formatCompensation(job)}</span>
                </div>
              </TableCell>
              <TableCell className="hidden text-sm text-muted-foreground md:table-cell">
                {job.applicants_count !== null && job.applicants_count !== undefined ? (
                  <span>{formatNumber(job.applicants_count)}</span>
                ) : (
                  <span className="text-muted-foreground/50">—</span>
                )}
              </TableCell>
              <TableCell className="text-sm text-muted-foreground">
                {job.date_posted ? (
                  <div className="flex flex-col">
                    <span>{formatDateRelative(job.date_posted)}</span>
                    <span className="text-xs opacity-75">{formatDateAbsolute(job.date_posted)}</span>
                  </div>
                ) : (
                  "Not specified"
                )}
              </TableCell>
              <TableCell>
                {job.company_id && (
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={(e) => handleBlockCompany(e, job)}
                    disabled={blockingIds.has(job.id)}
                    title="Block company"
                    className="h-8 w-8"
                  >
                    <Ban className="h-4 w-4 text-destructive" />
                  </Button>
                )}
              </TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
};

const formatLocation = (job: Job) => {
  const parts = [job.location_city, job.location_state, job.location_country].filter(
    Boolean
  ) as string[];

  if (job.is_remote) {
    if (!parts.length) {
      return "";
    }

    return job.location_country ?? parts[parts.length - 1];
  }

  if (!parts.length) {
    return "Not specified";
  }

  return parts.join(", ");
};

const formatCompensation = (job: Job) => {
  if (
    job.compensation_min === null &&
    job.compensation_max === null
  ) {
    return "Not specified";
  }

  const currency = job.compensation_currency ?? "USD";
  const interval = job.compensation_interval?.toLowerCase();
  const shouldAbbreviate = interval !== "hourly";
  const minFormatted = formatCompValue(
    job.compensation_min,
    currency,
    shouldAbbreviate
  );
  const maxFormatted = formatCompValue(
    job.compensation_max,
    currency,
    shouldAbbreviate
  );

  let range = minFormatted ?? maxFormatted ?? "Not specified";

  if (minFormatted && maxFormatted) {
    range = `${minFormatted} - ${maxFormatted}`;
  }

  const intervalLabel = intervalDisplay[job.compensation_interval ?? ""] ?? "";

  return intervalLabel ? `${range}/${intervalLabel}` : range;
};

const formatCompValue = (
  amount: number | null | undefined,
  currency: string,
  abbreviate: boolean
) => {
  if (amount === null || amount === undefined || Number.isNaN(amount)) {
    return null;
  }

  if (!abbreviate || Math.abs(amount) < 1000) {
    return formatCurrency(amount, currency);
  }

  return abbreviateCurrencyValue(amount, currency);
};

const abbreviateCurrencyValue = (amount: number, currency: string) => {
  const absolute = Math.abs(amount);
  const baseValue = absolute / 1000;
  const formattedBase = Number.isInteger(baseValue)
    ? baseValue.toString()
    : baseValue.toFixed(1).replace(/\.0$/, "");
  const sampleValue = amount < 0 ? -1 : 1;

  try {
    const formatter = new Intl.NumberFormat("en-US", {
      style: "currency",
      currency,
      maximumFractionDigits: 0,
    });

    const parts = formatter.formatToParts(sampleValue);

    return parts
      .map((part) => {
        if (part.type === "integer") {
          return `${formattedBase}k`;
        }

        if (part.type === "minusSign") {
          return amount < 0 ? part.value : "";
        }

        return part.value;
      })
      .join("");
  } catch {
    const prefix = amount < 0 ? "-" : "";
    return `${prefix}$${formattedBase}k`;
  }
};

const intervalDisplay: Record<string, string> = {
  yearly: "year",
  monthly: "month",
  weekly: "week",
  hourly: "hour",
};

const getJobTypeBadgeVariant = (
  type: JobType | string
): "default" | "secondary" | "outline" | "destructive" => {
  switch (type) {
    case "Full-time":
      return "default";
    case "Part-time":
      return "secondary";
    case "Contract":
      return "outline";
    case "Internship":
      return "secondary";
    case "Temporary":
      return "destructive";
    default:
      return "outline";
  }
};

const formatEmployeeSize = (job: Job): string | null => {
  // Prefer company_size_on_linkedin, fallback to company_size_min/max
  if (job.company_size_on_linkedin !== null && job.company_size_on_linkedin !== undefined) {
    return formatNumber(job.company_size_on_linkedin) + " employees";
  }
  
  if (job.company_size_min !== null && job.company_size_max !== null) {
    if (job.company_size_min === job.company_size_max) {
      return formatNumber(job.company_size_min) + " employees";
    }
    return `${formatNumber(job.company_size_min)}-${formatNumber(job.company_size_max)} employees`;
  }
  
  if (job.company_size_min !== null) {
    return `${formatNumber(job.company_size_min)}+ employees`;
  }
  
  if (job.company_size_max !== null) {
    return `Up to ${formatNumber(job.company_size_max)} employees`;
  }
  
  return null;
};

const formatNumber = (num: number): string => {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1).replace(/\.0$/, "") + "M";
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1).replace(/\.0$/, "") + "k";
  }
  return num.toLocaleString();
};

export default JobsTable;
