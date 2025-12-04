"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Briefcase, DollarSign, MapPin, Trash2, FileText, Download, Loader2, Eye, X, Save, FileDown } from "lucide-react";
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
import { Textarea } from "@/components/ui/textarea";
import PageLayout from "@/components/page-layout";
import AuthGuard from "@/components/auth-guard";
import {
  ApiError,
  deleteSavedJob,
  generateTailoredResume,
  getSavedJobs,
  getTailoredResume,
  updateSavedJobStatus,
  updateTailoredResume,
  generateTailoredResumePDF,
  downloadTailoredResumePDF,
} from "@/lib/api";
import {
  formatCurrency,
  formatDateRelative,
  formatDateAbsolute,
} from "@/lib/utils";
import type { JobStatus, SavedJob } from "@/types/job";
import type { TailoredResume } from "@/types/tailored-resume";

export default function SavedJobsPage() {
  const [savedJobs, setSavedJobs] = useState<SavedJob[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<JobStatus | "all">("all");
  const [updatingIds, setUpdatingIds] = useState<Set<number>>(new Set());
  const [generatingResumeIds, setGeneratingResumeIds] = useState<Set<number>>(new Set());
  const [tailoredResumeJobIds, setTailoredResumeJobIds] = useState<Set<number>>(new Set());
  const [viewingResumeJobId, setViewingResumeJobId] = useState<number | null>(null);
  const [resumeJsonContent, setResumeJsonContent] = useState<string>("");
  const [savingResume, setSavingResume] = useState(false);
  const [generatingPdfIds, setGeneratingPdfIds] = useState<Set<number>>(new Set());
  const [pdfGeneratedJobIds, setPdfGeneratedJobIds] = useState<Set<number>>(new Set());

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
        
        // Check which jobs have tailored resumes and PDFs
        const jobIds = data.saved_jobs.map((sj) => sj.job.id);
        const existingResumeIds = new Set<number>();
        const existingPdfIds = new Set<number>();
        await Promise.all(
          jobIds.map(async (jobId) => {
            try {
              const tailoredResume = await getTailoredResume(jobId);
              existingResumeIds.add(jobId);
              if (tailoredResume.pdf_generated) {
                existingPdfIds.add(jobId);
              }
            } catch (err) {
              // Resume doesn't exist for this job, ignore
            }
          })
        );
        setTailoredResumeJobIds(existingResumeIds);
        setPdfGeneratedJobIds(existingPdfIds);
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

  const handleGenerateResume = async (jobId: number) => {
    setGeneratingResumeIds((prev) => new Set(prev).add(jobId));
    try {
      await generateTailoredResume(jobId);
      setTailoredResumeJobIds((prev) => new Set(prev).add(jobId));
      alert("Tailored resume generated successfully!");
    } catch (err) {
      console.error("Failed to generate tailored resume:", err);
      const errorMessage =
        err instanceof ApiError
          ? err.message
          : err instanceof Error
          ? err.message
          : "Failed to generate tailored resume";
      alert(errorMessage);
    } finally {
      setGeneratingResumeIds((prev) => {
        const next = new Set(prev);
        next.delete(jobId);
        return next;
      });
    }
  };

  const handleDownloadResume = async (jobId: number, jobTitle: string) => {
    try {
      const tailoredResume = await getTailoredResume(jobId);
      const resumeData = JSON.parse(tailoredResume.tailored_resume_json);
      
      // Create a blob and download
      const blob = new Blob([JSON.stringify(resumeData, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `resume_${jobTitle.replace(/[^a-z0-9]/gi, "_").toLowerCase()}_${jobId}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Failed to download tailored resume:", err);
      alert(
        err instanceof Error
          ? err.message
          : "Failed to download tailored resume"
      );
    }
  };

  const handleViewResume = async (jobId: number) => {
    try {
      const tailoredResume = await getTailoredResume(jobId);
      // Format JSON with proper indentation
      const parsed = JSON.parse(tailoredResume.tailored_resume_json);
      setResumeJsonContent(JSON.stringify(parsed, null, 2));
      setViewingResumeJobId(jobId);
    } catch (err) {
      console.error("Failed to load tailored resume:", err);
      alert(
        err instanceof Error
          ? err.message
          : "Failed to load tailored resume"
      );
    }
  };

  const handleCloseResumeView = () => {
    setViewingResumeJobId(null);
    setResumeJsonContent("");
  };

  const handleSaveResume = async () => {
    if (!viewingResumeJobId) return;
    
    // Validate JSON
    try {
      JSON.parse(resumeJsonContent);
    } catch (err) {
      alert("Invalid JSON format. Please check your input.");
      return;
    }

    setSavingResume(true);
    try {
      await updateTailoredResume(viewingResumeJobId, resumeJsonContent);
      // Clear PDF status since resume was updated
      setPdfGeneratedJobIds((prev) => {
        const next = new Set(prev);
        next.delete(viewingResumeJobId);
        return next;
      });
      alert("Resume updated successfully!");
      handleCloseResumeView();
    } catch (err) {
      console.error("Failed to save tailored resume:", err);
      alert(
        err instanceof Error
          ? err.message
          : "Failed to save tailored resume"
      );
    } finally {
      setSavingResume(false);
    }
  };

  const handleGenerateAndDownloadPDF = async (jobId: number, jobTitle: string) => {
    setGeneratingPdfIds((prev) => new Set(prev).add(jobId));
    try {
      // First, check if tailored resume exists, generate it if it doesn't
      let tailoredResume: TailoredResume;
      try {
        tailoredResume = await getTailoredResume(jobId);
      } catch (err) {
        // If tailored resume doesn't exist, generate it first
        if (err instanceof ApiError && err.statusCode === 404) {
          tailoredResume = await generateTailoredResume(jobId);
          setTailoredResumeJobIds((prev) => new Set(prev).add(jobId));
        } else {
          throw err;
        }
      }
      
      // Generate PDF if it doesn't exist
      if (!tailoredResume.pdf_generated) {
        tailoredResume = await generateTailoredResumePDF(jobId);
        setPdfGeneratedJobIds((prev) => new Set(prev).add(jobId));
      }

      // Download the PDF
      const blob = await downloadTailoredResumePDF(jobId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      const safeTitle = jobTitle.replace(/[^a-z0-9]/gi, "_").toLowerCase();
      a.download = `resume_${safeTitle}_job_${jobId}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Failed to generate/download PDF:", err);
      alert(
        err instanceof Error
          ? err.message
          : "Failed to generate or download PDF"
      );
    } finally {
      setGeneratingPdfIds((prev) => {
        const next = new Set(prev);
        next.delete(jobId);
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
                      <TableHead className="w-[180px]">Resume</TableHead>
                      <TableHead className="w-[100px]">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {savedJobs.map((savedJob) => {
                      const job = savedJob.job;
                      const locationLabel = formatLocation(job);
                      const isUpdating = updatingIds.has(savedJob.id);
                      const isGenerating = generatingResumeIds.has(job.id);
                      const hasTailoredResume = tailoredResumeJobIds.has(job.id);

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
                            <div className="flex items-center gap-2">
                              {hasTailoredResume ? (
                                <>
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => handleViewResume(job.id)}
                                    disabled={isGenerating || generatingPdfIds.has(job.id)}
                                    className="flex items-center gap-2"
                                  >
                                    <Eye className="h-4 w-4" />
                                    <span className="hidden sm:inline">View</span>
                                  </Button>
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => handleDownloadResume(job.id, job.title)}
                                    disabled={isGenerating || generatingPdfIds.has(job.id)}
                                    className="flex items-center gap-2"
                                  >
                                    <Download className="h-4 w-4" />
                                    <span className="hidden sm:inline">JSON</span>
                                  </Button>
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => handleGenerateAndDownloadPDF(job.id, job.title)}
                                    disabled={isGenerating || generatingPdfIds.has(job.id)}
                                    className="flex items-center gap-2"
                                  >
                                    {generatingPdfIds.has(job.id) ? (
                                      <>
                                        <Loader2 className="h-4 w-4 animate-spin" />
                                        <span className="hidden sm:inline">Generating...</span>
                                      </>
                                    ) : (
                                      <>
                                        <FileDown className="h-4 w-4" />
                                        <span className="hidden sm:inline">PDF</span>
                                      </>
                                    )}
                                  </Button>
                                </>
                              ) : (
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => handleGenerateResume(job.id)}
                                  disabled={isGenerating}
                                  className="flex items-center gap-2"
                                >
                                  {isGenerating ? (
                                    <>
                                      <Loader2 className="h-4 w-4 animate-spin" />
                                      <span className="hidden sm:inline">Generating...</span>
                                    </>
                                  ) : (
                                    <>
                                      <FileText className="h-4 w-4" />
                                      <span className="hidden sm:inline">Generate</span>
                                    </>
                                  )}
                                </Button>
                              )}
                            </div>
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

          {/* Resume JSON View Modal */}
          {viewingResumeJobId && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
              <Card className="w-full max-w-4xl max-h-[90vh] m-4 flex flex-col">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
                  <div>
                    <CardTitle>Tailored Resume JSON</CardTitle>
                    <CardDescription>
                      Edit the resume JSON content below
                    </CardDescription>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={handleCloseResumeView}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </CardHeader>
                <CardContent className="flex-1 overflow-hidden flex flex-col">
                  <Textarea
                    value={resumeJsonContent}
                    onChange={(e) => setResumeJsonContent(e.target.value)}
                    className="flex-1 font-mono text-sm resize-none"
                    placeholder="Resume JSON content will appear here..."
                  />
                </CardContent>
                <div className="p-6 pt-0 flex justify-end gap-2">
                  <Button
                    variant="outline"
                    onClick={handleCloseResumeView}
                    disabled={savingResume}
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={handleSaveResume}
                    disabled={savingResume}
                    className="flex items-center gap-2"
                  >
                    {savingResume ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Saving...
                      </>
                    ) : (
                      <>
                        <Save className="h-4 w-4" />
                        Save
                      </>
                    )}
                  </Button>
                </div>
              </Card>
            </div>
          )}
        </div>
      </PageLayout>
    </AuthGuard>
  );
}

