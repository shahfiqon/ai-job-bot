import Link from "next/link"
import { FileQuestion } from "lucide-react"

import PageLayout from "@/components/page-layout"
import { Button } from "@/components/ui/button"

export default function NotFound() {
  return (
    <PageLayout>
      <div className="container flex min-h-[60vh] flex-col items-center justify-center text-center">
        <FileQuestion className="mb-6 h-24 w-24 text-muted-foreground" />
        <h1 className="mb-2 text-3xl font-bold">Job Not Found</h1>
        <p className="mb-6 max-w-md text-muted-foreground">
          The job you&apos;re looking for doesn&apos;t exist or has been removed.
        </p>
        <Button asChild>
          <Link href="/">Back to Jobs</Link>
        </Button>
      </div>
    </PageLayout>
  )
}
