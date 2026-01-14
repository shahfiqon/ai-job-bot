"use client";

import { useState, useEffect } from "react";
import JobsTable from "@/components/jobs-table";
import JobFiltersComponent from "@/components/job-filters";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { blockCompany, fetchJobs, markAllJobsAsSeen, type JobFilters } from "@/lib/api";
import type { Job } from "@/types/job";

export default function JobsListWithFilters() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [markingAsSeen, setMarkingAsSeen] = useState(false);
  const [filters, setFilters] = useState<JobFilters>({
    relocate_required: false, // Default: exclude jobs that require relocation
  });

  useEffect(() => {
    const loadJobs = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchJobs(page, 20, filters);
        setJobs(data.jobs);
        setTotal(data.total);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "An unexpected error occurred while loading jobs."
        );
      } finally {
        setLoading(false);
      }
    };

    loadJobs();
  }, [page, filters]);

  const handleFiltersChange = (newFilters: JobFilters) => {
    setFilters(newFilters);
    setPage(1); // Reset to first page when filters change
  };

  const handleClearFilters = () => {
    setFilters({
      relocate_required: false, // Always keep relocate_required at false to exclude relocate-required jobs
    });
    setPage(1);
  };

  const handleJobBlocked = (jobId: number) => {
    // Optimistically remove the job from the list
    setJobs((prevJobs) => prevJobs.filter((job) => job.id !== jobId));
    setTotal((prevTotal) => Math.max(0, prevTotal - 1));
  };

  const handleMarkAllAsSeen = async () => {
    setMarkingAsSeen(true);
    setError(null);
    try {
      const result = await markAllJobsAsSeen();
      // Reload jobs list - it will now be empty since all jobs are marked as seen
      const data = await fetchJobs(page, 20, filters);
      setJobs(data.jobs);
      setTotal(data.total);
      // Show success message (you could use a toast library here)
      alert(`Successfully marked ${result.jobs_marked} jobs as seen.`);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to mark jobs as seen."
      );
    } finally {
      setMarkingAsSeen(false);
    }
  };

  if (loading && jobs.length === 0) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading jobs...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Card className="mx-auto max-w-xl">
        <CardHeader>
          <CardTitle>Failed to load jobs</CardTitle>
          <CardDescription>{error}</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-3">
          <Button onClick={() => window.location.reload()}>Try again</Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div>
      <JobFiltersComponent
        filters={filters}
        onFiltersChange={handleFiltersChange}
        onClearFilters={handleClearFilters}
      />
      <div className="mb-4 flex items-center justify-between">
        <div className="text-sm text-muted-foreground">
          {loading ? (
            "Loading..."
          ) : (
            <>
              Showing <span className="font-semibold text-foreground">{jobs.length}</span> of{" "}
              <span className="font-semibold text-foreground">{total.toLocaleString()}</span>{" "}
              {total === 1 ? "job" : "jobs"}
            </>
          )}
        </div>
        <Button
          onClick={handleMarkAllAsSeen}
          disabled={markingAsSeen || loading || total === 0}
          variant="outline"
        >
          {markingAsSeen ? "Marking..." : "Mark all as seen"}
        </Button>
      </div>
      <JobsTable jobs={jobs} onJobBlocked={handleJobBlocked} />
      {total > 20 && (
        <div className="flex justify-center gap-2 mt-6">
          <Button
            variant="outline"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1 || loading}
          >
            Previous
          </Button>
          <div className="flex items-center px-4">
            Page {page} of {Math.ceil(total / 20)}
          </div>
          <Button
            variant="outline"
            onClick={() => setPage((p) => p + 1)}
            disabled={page >= Math.ceil(total / 20) || loading}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  );
}

