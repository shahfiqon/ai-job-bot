import JobsTable from "@/components/jobs-table";
import PageLayout from "@/components/page-layout";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { fetchJobs } from "@/lib/api";

export default async function HomePage() {
  try {
    const { jobs } = await fetchJobs(1, 20);

    return (
      <PageLayout>
        <div className="container mx-auto py-8">
          <div className="mb-6">
            <h1 className="text-3xl font-bold">Job Opportunities</h1>
            <p className="mt-2 text-muted-foreground">
              Browse and track job opportunities tailored for you.
            </p>
          </div>
          <JobsTable jobs={jobs} />
        </div>
      </PageLayout>
    );
  } catch (error) {
    const message =
      error instanceof Error
        ? error.message
        : "An unexpected error occurred while loading jobs.";

    return (
      <PageLayout>
        <div className="container mx-auto py-8">
          <Card className="mx-auto max-w-xl">
            <CardHeader>
              <CardTitle>Failed to load jobs</CardTitle>
              <CardDescription>{message}</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-wrap gap-3">
              <Button asChild>
                <a href="/">Try again</a>
              </Button>
            </CardContent>
          </Card>
        </div>
      </PageLayout>
    );
  }
}
