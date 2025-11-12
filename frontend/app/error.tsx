"use client";

import { useEffect } from "react";
import { AlertCircle } from "lucide-react";

import PageLayout from "@/components/page-layout";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

type ErrorProps = {
  error: Error & { digest?: string };
  reset: () => void;
};

export default function Error({ error, reset }: ErrorProps) {
  useEffect(() => {
    console.error("Error loading jobs:", error);
  }, [error]);

  return (
    <PageLayout>
      <div className="container flex min-h-[60vh] items-center justify-center">
        <Card className="w-full max-w-xl text-center">
          <CardHeader className="items-center gap-3">
            <AlertCircle className="h-10 w-10 text-destructive" />
            <CardTitle>Failed to load jobs</CardTitle>
            <CardDescription>
              {error.message ||
                "An unexpected error occurred while loading jobs."}
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-wrap justify-center gap-3">
            <Button onClick={reset}>Try again</Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                window.location.href = "/";
              }}
            >
              Refresh page
            </Button>
          </CardContent>
        </Card>
      </div>
    </PageLayout>
  );
}

