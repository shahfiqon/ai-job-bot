import JobsListWithFilters from "@/components/jobs-list-with-filters";
import PageLayout from "@/components/page-layout";

export default async function HomePage() {
  return (
    <PageLayout>
      <div className="container mx-auto py-8">
        <div className="mb-6">
          <h1 className="text-3xl font-bold">Job Opportunities</h1>
          <p className="mt-2 text-muted-foreground">
            Browse and track job opportunities tailored for you.
          </p>
        </div>
        <JobsListWithFilters />
      </div>
    </PageLayout>
  );
}
