"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Briefcase, DollarSign, MapPin, Trash2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import PageLayout from "@/components/page-layout";
import AuthGuard from "@/components/auth-guard";
import {
  ApiError,
  deleteSavedJob,
  getSavedJobs,
  updateSavedJobStatus,
} from "@/lib/api";
import {
  formatCurrency,
  formatDateRelative,
  formatDateAbsolute,
} from "@/lib/utils";
import type { JobStatus, SavedJob } from "@/types/job";

export default function SavedJobsPage() {
  const [savedJobs, setSavedJobs] = useState<SavedJob[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<JobStatus | "all">("all");
  const [updatingIds, setUpdatingIds] = useState<Set<number>>(new Set());

  useEffect(() => {
    const loadSavedJobs = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await getSavedJobs(
          page,
          pageSize,
          statusFilter === "all" ? undefined : statusFilter
        );
        setSavedJobs(data.saved_jobs);
        setTotal(data.total);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "An unexpected error occurred while loading saved jobs."
        );
      } finally {
        setLoading(false);
      }
    };

    loadSavedJobs();
  }, [page, pageSize, statusFilter]);

  const handleStatusChange = async (savedJobId: number, newStatus: JobStatus) => {
    setUpdatingIds((prev) => new Set(prev).add(savedJobId));
    try {
      await updateSavedJobStatus(savedJobId, newStatus);
      // Reload the list
      const data = await getSavedJobs(
        page,
        pageSize,
        statusFilter === "all" ? undefined : statusFilter
      );
      setSavedJobs(data.saved_jobs);
      setTotal(data.total);
    } catch (err) {
      console.error("Failed to update status:", err);
      alert(err instanceof Error ? err.message : "Failed to update status");
    } finally {
      setUpdatingIds((prev) => {
        const next = new Set(prev);
        next.delete(savedJobId);
        return next;
      });
    }
  };

  const handleDelete = async (savedJobId: number) => {
    if (!confirm("Are you sure you want to remove this saved job?")) {
      return;
    }
    setUpdatingIds((prev) => new Set(prev).add(savedJobId));
    try {
      await deleteSavedJob(savedJobId);
      // Reload the list
      const data = await getSavedJobs(
        page,
        pageSize,
        statusFilter === "all" ? undefined : statusFilter
      );
      setSavedJobs(data.saved_jobs);
      setTotal(data.total);
    } catch (err) {
      console.error("Failed to delete saved job:", err);
      alert(err instanceof Error ? err.message : "Failed to delete saved job");
    } finally {
      setUpdatingIds((prev) => {
        const next = new Set(prev);
        next.delete(savedJobId);
        return next;
      });
    }
  };

  const getStatusColor = (status: JobStatus) => {
    switch (status) {
      case "saved":
        return "secondary";
      case "applied":
        return "default";
      case "interview":
        return "default";
      case "declined":
        return "destructive";
      default:
        return "secondary";
    }
  };

  const formatLocation = (job: SavedJob["job"]) => {
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

  const formatCompensation = (job: SavedJob["job"]) => {
    if (
      job.compensation_min === null &&
      job.compensation_max === null
    ) {
      return "Not specified";
    }

    const currency = job.compensation_currency ?? "USD";
    const minFormatted = job.compensation_min
      ? formatCurrency(job.compensation_min, currency)
      : null;
    const maxFormatted = job.compensation_max
      ? formatCurrency(job.compensation_max, currency)
      : null;

    let range = minFormatted ?? maxFormatted ?? "Not specified";

    if (minFormatted && maxFormatted) {
      range = `${minFormatted} - ${maxFormatted}`;
    }

    const interval = job.compensation_interval?.toLowerCase();
    const intervalLabel =
      interval === "yearly"
        ? "per year"
        : interval === "monthly"
        ? "per month"
        : interval === "weekly"
        ? "per week"
        : interval === "hourly"
        ? "per hour"
        : "";

    return intervalLabel ? `${range} ${intervalLabel}` : range;
  };

  if (loading && savedJobs.length === 0) {
    return (
      <AuthGuard>
        <PageLayout>
          <div className="container mx-auto py-8">
            <div className="flex items-center justify-center p-8">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
                <p className="text-muted-foreground">Loading saved jobs...</p>
              </div>
            </div>
          </div>
        </PageLayout>
      </AuthGuard>
    );
  }

  if (error) {
    return (
      <AuthGuard>
        <PageLayout>
          <div className="container mx-auto py-8">
            <Card className="mx-auto max-w-xl">
              <CardHeader>
                <CardTitle>Failed to load saved jobs</CardTitle>
                <CardDescription>{error}</CardDescription>
              </CardHeader>
              <CardContent className="flex flex-wrap gap-3">
                <Button onClick={() => window.location.reload()}>Try again</Button>
              </CardContent>
            </Card>
          </div>
        </PageLayout>
      </AuthGuard>
    );
  }

  return (
    <AuthGuard>
      <PageLayout>
        <div className="container mx-auto py-8">
          <div className="mb-6">
            <h1 className="text-3xl font-bold">Saved Jobs</h1>
            <p className="mt-2 text-muted-foreground">
              Manage your saved jobs and track your application status.
            </p>
          </div>

          <div className="mb-6 flex items-center gap-4">
            <div className="flex items-center gap-2">
              <label htmlFor="status-filter" className="text-sm font-medium">
                Filter by status:
              </label>
              <Select
                value={statusFilter}
                onValueChange={(value) => {
                  setStatusFilter(value as JobStatus | "all");
                  setPage(1);
                }}
              >
                <SelectTrigger id="status-filter" className="w-[140px]">
                  <SelectValue placeholder="All statuses" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All statuses</SelectItem>
                  <SelectItem value="saved">Saved</SelectItem>
                  <SelectItem value="applied">Applied</SelectItem>
                  <SelectItem value="interview">Interview</SelectItem>
                  <SelectItem value="declined">Declined</SelectItem>
                </SelectContent>
              </Select>
            </div>
            {total > 0 && (
              <span className="text-sm text-muted-foreground">
                {total} {total === 1 ? "job" : "jobs"} found
              </span>
            )}
          </div>

          {savedJobs.length === 0 ? (
            <Card>
              <CardContent className="p-8 text-center text-muted-foreground">
                {statusFilter === "all"
                  ? "You haven't saved any jobs yet."
                  : `No jobs with status "${statusFilter}" found.`}
                <div className="mt-4">
                  <Button asChild>
                    <Link href="/">Browse Jobs</Link>
                  </Button>
                </div>
              </CardContent>
            </Card>
          ) : (
            <>
              <div className="rounded-lg border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-[280px]">Job Title</TableHead>
                      <TableHead className="hidden md:table-cell">Location</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="hidden lg:table-cell">Salary</TableHead>
                      <TableHead>Saved</TableHead>
                      <TableHead className="w-[100px]">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {savedJobs.map((savedJob) => {
                      const job = savedJob.job;
                      const locationLabel = formatLocation(job);
                      const isUpdating = updatingIds.has(savedJob.id);

                      return (
                        <TableRow key={savedJob.id}>
                          <TableCell className="space-y-2">
                            <div className="space-y-1">
                              <Link
                                href={`/jobs/${job.id}`}
                                className="text-base font-semibold text-foreground transition-colors hover:text-primary block"
                              >
                                {job.title}
                              </Link>
                              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                <Briefcase className="h-4 w-4" />
                                <span>{job.company_name ?? "Confidential company"}</span>
                              </div>
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
                            </div>
                          </TableCell>
                          <TableCell>
                            <Select
                              value={savedJob.status}
                              onValueChange={(value) =>
                                handleStatusChange(savedJob.id, value as JobStatus)
                              }
                              disabled={isUpdating}
                            >
                              <SelectTrigger className="w-[120px]">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="saved">Saved</SelectItem>
                                <SelectItem value="applied">Applied</SelectItem>
                                <SelectItem value="interview">Interview</SelectItem>
                                <SelectItem value="declined">Declined</SelectItem>
                              </SelectContent>
                            </Select>
                          </TableCell>
                          <TableCell className="hidden text-sm text-muted-foreground lg:table-cell">
                            <div className="flex items-center gap-2">
                              <DollarSign className="h-4 w-4" />
                              <span>{formatCompensation(job)}</span>
                            </div>
                          </TableCell>
                          <TableCell className="text-sm text-muted-foreground">
                            {savedJob.created_at ? (
                              <div className="flex flex-col">
                                <span>{formatDateRelative(new Date(savedJob.created_at))}</span>
                                <span className="text-xs opacity-75">
                                  {formatDateAbsolute(new Date(savedJob.created_at))}
                                </span>
                              </div>
                            ) : (
                              "—"
                            )}
                          </TableCell>
                          <TableCell>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDelete(savedJob.id)}
                              disabled={isUpdating}
                              className="text-destructive hover:text-destructive"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </div>

              {total > pageSize && (
                <div className="flex justify-center gap-2 mt-6">
                  <Button
                    variant="outline"
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1 || loading}
                  >
                    Previous
                  </Button>
                  <div className="flex items-center px-4">
                    Page {page} of {Math.ceil(total / pageSize)}
                  </div>
                  <Button
                    variant="outline"
                    onClick={() => setPage((p) => p + 1)}
                    disabled={page >= Math.ceil(total / pageSize) || loading}
                  >
                    Next
                  </Button>
                </div>
              )}
            </>
          )}
        </div>
      </PageLayout>
    </AuthGuard>
  );
}

