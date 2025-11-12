import PageLayout from "@/components/page-layout";

export default function Loading() {
  return (
    <PageLayout>
      <div className="flex min-h-[60vh] items-center justify-center">
        <p className="text-muted-foreground">Loading jobs...</p>
      </div>
    </PageLayout>
  );
}

