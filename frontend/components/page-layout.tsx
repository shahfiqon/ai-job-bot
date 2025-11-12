'use client';

import Link from "next/link";
import { Briefcase } from "lucide-react";

type PageLayoutProps = {
  children: React.ReactNode;
};

const PageLayout = ({ children }: PageLayoutProps) => {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-50 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/75">
        <div className="container flex flex-col gap-4 py-4 sm:flex-row sm:items-center sm:justify-between">
          <Link href="/" className="flex items-center gap-2 font-semibold">
            <Briefcase className="h-6 w-6 text-primary" />
            <span>Job Apply Assistant</span>
          </Link>
          <nav className="text-sm text-muted-foreground">
            <span>Insights coming soon</span>
          </nav>
        </div>
      </header>

      <main className="flex-1">{children}</main>

      <footer className="border-t">
        <div className="container py-6 text-center text-sm text-muted-foreground">
          © 2025 Job Apply Assistant. All rights reserved.
        </div>
      </footer>
    </div>
  );
};

export default PageLayout;
