"use client";

import { useState, useEffect } from "react";
import { Save } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import PageLayout from "@/components/page-layout";
import AuthGuard from "@/components/auth-guard";
import { ApiError, fetchResume, updateResume } from "@/lib/api";

export default function ProfilePage() {
  const [resumeJson, setResumeJson] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [jsonError, setJsonError] = useState<string | null>(null);

  useEffect(() => {
    const loadResume = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchResume();
        setResumeJson(data.resume_json || "");
      } catch (err) {
        setError(
          err instanceof ApiError
            ? err.message
            : "An unexpected error occurred while loading resume."
        );
      } finally {
        setLoading(false);
      }
    };

    loadResume();
  }, []);

  const validateJson = (jsonString: string): boolean => {
    if (!jsonString.trim()) {
      setJsonError(null);
      return true; // Empty is valid (will be stored as null)
    }
    try {
      JSON.parse(jsonString);
      setJsonError(null);
      return true;
    } catch (e) {
      setJsonError(
        e instanceof Error ? `Invalid JSON: ${e.message}` : "Invalid JSON format"
      );
      return false;
    }
  };

  const handleJsonChange = (value: string) => {
    setResumeJson(value);
    setSuccess(false);
    validateJson(value);
  };

  const handleSave = async () => {
    if (!validateJson(resumeJson)) {
      return;
    }

    setSaving(true);
    setError(null);
    setSuccess(false);

    try {
      const jsonToSave = resumeJson.trim() || null;
      await updateResume(jsonToSave);
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "An unexpected error occurred while saving resume."
      );
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <AuthGuard>
        <PageLayout>
          <div className="container mx-auto py-8">
            <div className="flex items-center justify-center p-8">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
                <p className="text-muted-foreground">Loading resume...</p>
              </div>
            </div>
          </div>
        </PageLayout>
      </AuthGuard>
    );
  }

  return (
    <AuthGuard>
      <PageLayout>
        <div className="container mx-auto py-8 max-w-4xl">
          <div className="mb-6">
            <h1 className="text-3xl font-bold">Profile</h1>
            <p className="mt-2 text-muted-foreground">
              Manage your resume content in JSON format.
            </p>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Resume JSON</CardTitle>
              <CardDescription>
                Enter or update your resume content in JSON format. The JSON will be validated before saving.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {error && (
                <div className="p-3 rounded-md bg-destructive/10 text-destructive text-sm">
                  {error}
                </div>
              )}

              {success && (
                <div className="p-3 rounded-md bg-green-500/10 text-green-600 dark:text-green-400 text-sm">
                  Resume saved successfully!
                </div>
              )}

              {jsonError && (
                <div className="p-3 rounded-md bg-destructive/10 text-destructive text-sm">
                  {jsonError}
                </div>
              )}

              <div className="space-y-2">
                <label htmlFor="resume-json" className="text-sm font-medium">
                  Resume JSON Content
                </label>
                <textarea
                  id="resume-json"
                  value={resumeJson}
                  onChange={(e) => handleJsonChange(e.target.value)}
                  className="w-full min-h-[400px] p-4 border rounded-md font-mono text-sm bg-background resize-y"
                  placeholder='Enter your resume in JSON format, e.g. {"basics": {"name": "John Doe", ...}}'
                />
                <p className="text-xs text-muted-foreground">
                  Tip: Use a JSON formatter/validator tool to ensure your JSON is properly formatted.
                </p>
              </div>

              <div className="flex justify-end">
                <Button
                  onClick={handleSave}
                  disabled={saving || !!jsonError}
                  className="min-w-[100px]"
                >
                  {saving ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Saving...
                    </>
                  ) : (
                    <>
                      <Save className="h-4 w-4 mr-2" />
                      Save
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </PageLayout>
    </AuthGuard>
  );
}


