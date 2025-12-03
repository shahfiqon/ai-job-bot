"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Ban, Building2, ArrowLeft } from "lucide-react";
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
  fetchBlockedCompanies,
  unblockCompany,
} from "@/lib/api";
import { formatDateRelative, formatDateAbsolute } from "@/lib/utils";
import type { BlockedCompany } from "@/types/blocked-company";

export default function BlockedCompaniesPage() {
  const [blockedCompanies, setBlockedCompanies] = useState<BlockedCompany[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [unblockingIds, setUnblockingIds] = useState<Set<number>>(new Set());

  useEffect(() => {
    const loadBlockedCompanies = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchBlockedCompanies(page, pageSize);
        setBlockedCompanies(data.blocked_companies);
        setTotal(data.total);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "An unexpected error occurred while loading blocked companies."
        );
      } finally {
        setLoading(false);
      }
    };

    loadBlockedCompanies();
  }, [page, pageSize]);

  const handleUnblock = async (companyId: number, companyName: string) => {
    if (!confirm(`Are you sure you want to unblock ${companyName}? Jobs from this company will appear in your search results again.`)) {
      return;
    }
    setUnblockingIds((prev) => new Set(prev).add(companyId));
    try {
      await unblockCompany(companyId);
      // Reload the list
      const data = await fetchBlockedCompanies(page, pageSize);
      setBlockedCompanies(data.blocked_companies);
      setTotal(data.total);
    } catch (err) {
      console.error("Failed to unblock company:", err);
      alert(err instanceof Error ? err.message : "Failed to unblock company");
    } finally {
      setUnblockingIds((prev) => {
        const next = new Set(prev);
        next.delete(companyId);
        return next;
      });
    }
  };

  if (loading && blockedCompanies.length === 0) {
    return (
      <AuthGuard>
        <PageLayout>
          <div className="container mx-auto py-10">
            <div className="text-center">
              <div className="mb-4 inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent align-[-0.125em] motion-reduce:animate-[spin_1.5s_linear_infinite]" />
              <p className="text-muted-foreground">Loading blocked companies...</p>
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
          <div className="container mx-auto py-10">
            <Card className="mx-auto max-w-xl">
              <CardHeader>
                <CardTitle>Failed to load blocked companies</CardTitle>
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
        <div className="container mx-auto py-10">
          <Button
            asChild
            variant="ghost"
            className="mb-6 w-fit px-0 text-muted-foreground hover:text-foreground"
          >
            <Link href="/" className="inline-flex items-center gap-2">
              <ArrowLeft className="h-4 w-4" />
              Back to Jobs
            </Link>
          </Button>

          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Ban className="h-5 w-5" />
                <CardTitle>Blocked Companies</CardTitle>
              </div>
              <CardDescription>
                Companies you've blocked will not appear in your job search results.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {blockedCompanies.length === 0 ? (
                <div className="rounded-lg border bg-card p-8 text-center text-muted-foreground">
                  <Ban className="mx-auto mb-4 h-12 w-12 opacity-50" />
                  <p className="text-lg font-medium">No blocked companies</p>
                  <p className="mt-2 text-sm">
                    You haven't blocked any companies yet. Block companies from job cards or job detail pages.
                  </p>
                </div>
              ) : (
                <>
                  <div className="mb-4 text-sm text-muted-foreground">
                    Showing {blockedCompanies.length} of {total.toLocaleString()}{" "}
                    {total === 1 ? "blocked company" : "blocked companies"}
                  </div>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Company</TableHead>
                        <TableHead className="hidden md:table-cell">Industry</TableHead>
                        <TableHead className="hidden lg:table-cell">Blocked Date</TableHead>
                        <TableHead className="w-[120px]">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {blockedCompanies.map((blockedCompany) => {
                        const company = blockedCompany.company;
                        const blockedDate = new Date(blockedCompany.created_at);
                        const blockedRelative = formatDateRelative(blockedDate);
                        const blockedAbsolute = formatDateAbsolute(blockedDate);

                        return (
                          <TableRow key={blockedCompany.id}>
                            <TableCell>
                              <div className="space-y-1">
                                <div className="flex items-center gap-2">
                                  <Building2 className="h-4 w-4 text-muted-foreground" />
                                  <span className="font-semibold">{company.name}</span>
                                </div>
                                {company.description && (
                                  <p className="text-sm text-muted-foreground line-clamp-2">
                                    {company.description}
                                  </p>
                                )}
                                {company.website && (
                                  <a
                                    href={company.website}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="text-xs text-primary hover:underline"
                                  >
                                    {company.website}
                                  </a>
                                )}
                              </div>
                            </TableCell>
                            <TableCell className="hidden md:table-cell">
                              {company.industry ? (
                                <Badge variant="outline">{company.industry}</Badge>
                              ) : (
                                <span className="text-muted-foreground">—</span>
                              )}
                            </TableCell>
                            <TableCell className="hidden lg:table-cell text-sm text-muted-foreground">
                              <div className="flex flex-col">
                                <span>{blockedRelative}</span>
                                <span className="text-xs opacity-75">{blockedAbsolute}</span>
                              </div>
                            </TableCell>
                            <TableCell>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleUnblock(company.id, company.name)}
                                disabled={unblockingIds.has(company.id)}
                              >
                                {unblockingIds.has(company.id) ? "Unblocking..." : "Unblock"}
                              </Button>
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
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
            </CardContent>
          </Card>
        </div>
      </PageLayout>
    </AuthGuard>
  );
}









