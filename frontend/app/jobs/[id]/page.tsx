"use client";

import type { Metadata } from "next"
import Link from "next/link"
import { notFound, useParams } from "next/navigation"
import { useEffect, useState } from "react"
import {
  ArrowLeft,
  MapPin,
  Briefcase,
  DollarSign,
  Calendar,
  Building2,
  Users,
  Globe,
  ExternalLink,
} from "lucide-react"

import PageLayout from "@/components/page-layout"
import AuthGuard from "@/components/auth-guard"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { ApiError, fetchJobById } from "@/lib/api"
import {
  formatCompanySize,
  formatCurrency,
  formatDateRelative,
  formatDateAbsolute,
  truncateText,
} from "@/lib/utils"
import type { Company, Job, JobDetail } from "@/types/job"

type JobPageProps = {
  params: {
    id: string
  }
}

const intervalCopy: Record<string, string> = {
  yearly: "per year",
  monthly: "per month",
  weekly: "per week",
  hourly: "per hour",
}

const getCompensationDisplay = (job: Job) => {
  const currency = job.compensation_currency ?? "USD"
  const min =
    typeof job.compensation_min === "number"
      ? formatCurrency(job.compensation_min, currency)
      : null
  const max =
    typeof job.compensation_max === "number"
      ? formatCurrency(job.compensation_max, currency)
      : null

  if (!min && !max) {
    return "Not specified"
  }

  const label = [min, max].filter(Boolean).join(" - ")
  const intervalLabel = job.compensation_interval
    ? intervalCopy[job.compensation_interval] ?? job.compensation_interval
    : null

  if (!intervalLabel) {
    return label
  }

  return `${label} ${intervalLabel}`
}

const buildLocation = (job: Job) => {
  const parts = [job.location_city, job.location_state, job.location_country]
    .filter((part): part is string => Boolean(part))
    .join(", ")

  return parts || "Location to be announced"
}

export default function JobDetailPage() {
  const params = useParams()
  const jobId = Number.parseInt(params.id as string, 10)

  const [job, setJob] = useState<JobDetail | null>(null)
  const [company, setCompany] = useState<Company | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (Number.isNaN(jobId)) {
      notFound()
      return
    }

    async function loadJob() {
      try {
        setIsLoading(true)
        const response = await fetchJobById(jobId)
        setJob(response)
        setCompany(response.company ?? null)
        setError(null)
      } catch (err) {
        if (err instanceof ApiError && err.statusCode === 404) {
          notFound()
          return
        }

        const message =
          err instanceof Error
            ? err.message
            : "An unexpected error occurred while loading this job."
        setError(message)
      } finally {
        setIsLoading(false)
      }
    }

    loadJob()
  }, [jobId])

  if (isLoading) {
    return (
      <AuthGuard>
        <PageLayout>
          <div className="container mx-auto py-10">
            <div className="text-center">
              <div className="mb-4 inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent align-[-0.125em] motion-reduce:animate-[spin_1.5s_linear_infinite]" />
              <p className="text-muted-foreground">Loading job details...</p>
            </div>
          </div>
        </PageLayout>
      </AuthGuard>
    )
  }

  if (error) {
    return (
      <AuthGuard>
        <PageLayout>
          <div className="container mx-auto py-10">
            <Card className="mx-auto max-w-xl">
              <CardHeader>
                <CardTitle>Failed to load job details</CardTitle>
                <CardDescription>{error}</CardDescription>
              </CardHeader>
              <CardContent className="flex flex-wrap gap-3">
                <Button asChild>
                  <Link href="/">Back to jobs</Link>
                </Button>
              </CardContent>
            </Card>
          </div>
        </PageLayout>
      </AuthGuard>
    )
  }

  if (!job) {
    notFound()
    return null
  }

  const location = buildLocation(job)
  const compensation = getCompensationDisplay(job)
  const postedRelative = job.date_posted ? formatDateRelative(job.date_posted) : null
  const postedAbsolute = job.date_posted ? formatDateAbsolute(job.date_posted) : null
  const posted = postedRelative && postedAbsolute 
    ? `${postedRelative} (${postedAbsolute})` 
    : postedRelative || postedAbsolute || "Not specified"

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
          <CardHeader className="space-y-3">
            <div className="space-y-2">
              <CardTitle className="text-3xl font-bold">
                {job.title}
              </CardTitle>
              {job.company_name ? (
                <CardDescription className="flex items-center gap-2 text-lg">
                  <Briefcase className="h-4 w-4" />
                  <span>{job.company_name}</span>
                </CardDescription>
              ) : null}
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <MapPin className="h-4 w-4" />
                  Location
                </div>
                <p className="text-base font-medium">{location}</p>
                {job.is_remote ? (
                  <Badge variant="secondary" className="w-fit">
                    Remote
                  </Badge>
                ) : null}
              </div>

              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Briefcase className="h-4 w-4" />
                  Job Type
                </div>
                <div className="flex flex-wrap gap-2">
                  {job.job_type?.length ? (
                    job.job_type.map((type) => (
                      <Badge key={type} variant="outline">
                        {type}
                      </Badge>
                    ))
                  ) : (
                    <span className="text-muted-foreground">Not specified</span>
                  )}
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <DollarSign className="h-4 w-4" />
                  Compensation
                </div>
                <p className="text-base font-medium">{compensation}</p>
              </div>

              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Calendar className="h-4 w-4" />
                  Posted
                </div>
                <p className="text-base font-medium">{posted}</p>
              </div>

              {job.job_level ? (
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Users className="h-4 w-4" />
                    Level
                  </div>
                  <Badge variant="outline" className="w-fit">
                    {job.job_level}
                  </Badge>
                </div>
              ) : null}

              {job.job_function ? (
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Building2 className="h-4 w-4" />
                    Function
                  </div>
                  <Badge variant="outline" className="w-fit">
                    {job.job_function}
                  </Badge>
                </div>
              ) : null}
            </div>
          </CardContent>
        </Card>

        <div className="mt-6 flex flex-wrap gap-3">
          {job.job_url ? (
            <Button asChild>
              <Link href={job.job_url} target="_blank" rel="noreferrer">
                Apply Now
              </Link>
            </Button>
          ) : null}
          <Button type="button" variant="outline">
            Save Job
          </Button>
          <Button type="button" variant="ghost">
            Share
          </Button>
        </div>

        <Separator className="my-8" />

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Job Description</CardTitle>
              {job.job_url ? (
                <Button asChild variant="outline" size="sm">
                  <Link href={job.job_url} target="_blank" rel="noreferrer">
                    <ExternalLink className="h-4 w-4 mr-2" />
                    Open in new tab
                  </Link>
                </Button>
              ) : null}
            </div>
          </CardHeader>
          <CardContent>
            <div className="prose prose-slate max-w-none prose-job-description whitespace-pre-wrap">
              {job.description ?? "The hiring team will update this description soon."}
            </div>
          </CardContent>
        </Card>

        {/* LLM-Parsed Job Details */}
        {(job.summary || 
          job.job_categories?.length || 
          job.technologies?.length ||
          job.required_skills?.length ||
          job.preferred_skills?.length ||
          job.responsibilities?.length ||
          job.benefits?.length ||
          job.required_education ||
          job.required_years_experience !== null) && (
          <>
            <Separator className="my-8" />
            
            {/* Summary */}
            {job.summary && (
              <Card>
                <CardHeader>
                  <CardTitle>Summary</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-base leading-7">{job.summary}</p>
                </CardContent>
              </Card>
            )}

            {/* Job Categories & Technologies */}
            {(job.job_categories?.length || job.technologies?.length) && (
              <Card className="mt-6">
                <CardHeader>
                  <CardTitle>Categories & Technologies</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {job.job_categories?.length ? (
                    <div>
                      <h4 className="text-sm font-medium text-muted-foreground mb-2">Categories</h4>
                      <div className="flex flex-wrap gap-2">
                        {job.job_categories.map((category) => (
                          <Badge key={category} variant="secondary">
                            {category}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  ) : null}
                  {job.technologies?.length ? (
                    <div>
                      <h4 className="text-sm font-medium text-muted-foreground mb-2">Technologies</h4>
                      <div className="flex flex-wrap gap-2">
                        {job.technologies.map((tech) => (
                          <Badge key={tech} variant="outline">
                            {tech}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  ) : null}
                </CardContent>
              </Card>
            )}

            {/* Requirements */}
            {(job.required_skills?.length || 
              job.preferred_skills?.length || 
              job.required_education || 
              job.required_years_experience !== null) && (
              <Card className="mt-6">
                <CardHeader>
                  <CardTitle>Requirements</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {job.required_years_experience !== null && (
                    <div>
                      <h4 className="text-sm font-medium text-muted-foreground mb-1">Experience</h4>
                      <p className="text-base">{job.required_years_experience}+ years</p>
                    </div>
                  )}
                  {job.required_education && (
                    <div>
                      <h4 className="text-sm font-medium text-muted-foreground mb-1">Education</h4>
                      <p className="text-base">{job.required_education}</p>
                      {job.preferred_education && (
                        <p className="text-sm text-muted-foreground mt-1">
                          Preferred: {job.preferred_education}
                        </p>
                      )}
                    </div>
                  )}
                  {job.required_skills?.length ? (
                    <div>
                      <h4 className="text-sm font-medium text-muted-foreground mb-2">Required Skills</h4>
                      <ul className="list-disc list-inside space-y-1">
                        {job.required_skills.map((skill, idx) => (
                          <li key={idx} className="text-base">{skill}</li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                  {job.preferred_skills?.length ? (
                    <div>
                      <h4 className="text-sm font-medium text-muted-foreground mb-2">Preferred Skills</h4>
                      <ul className="list-disc list-inside space-y-1">
                        {job.preferred_skills.map((skill, idx) => (
                          <li key={idx} className="text-base text-muted-foreground">{skill}</li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                </CardContent>
              </Card>
            )}

            {/* Responsibilities */}
            {job.responsibilities?.length ? (
              <Card className="mt-6">
                <CardHeader>
                  <CardTitle>Responsibilities</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="list-disc list-inside space-y-2">
                    {job.responsibilities.map((responsibility, idx) => (
                      <li key={idx} className="text-base leading-7">{responsibility}</li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            ) : null}

            {/* Benefits & Compensation */}
            {(job.benefits?.length || 
              job.parsed_salary_min || 
              job.parsed_salary_max || 
              job.compensation_basis ||
              job.independent_contractor_friendly !== null) && (
              <Card className="mt-6">
                <CardHeader>
                  <CardTitle>Benefits & Compensation</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {(job.parsed_salary_min || job.parsed_salary_max) && (
                    <div>
                      <h4 className="text-sm font-medium text-muted-foreground mb-1">Salary Range</h4>
                      <p className="text-base">
                        {job.parsed_salary_currency || "USD"}{" "}
                        {job.parsed_salary_min && formatCurrency(job.parsed_salary_min, job.parsed_salary_currency || "USD")}
                        {job.parsed_salary_min && job.parsed_salary_max && " - "}
                        {job.parsed_salary_max && formatCurrency(job.parsed_salary_max, job.parsed_salary_currency || "USD")}
                        {job.compensation_basis && ` (${job.compensation_basis})`}
                      </p>
                    </div>
                  )}
                  {job.independent_contractor_friendly && (
                    <div>
                      <Badge variant="secondary">Independent Contractor Friendly</Badge>
                    </div>
                  )}
                  {job.benefits?.length ? (
                    <div>
                      <h4 className="text-sm font-medium text-muted-foreground mb-2">Benefits</h4>
                      <ul className="list-disc list-inside space-y-1">
                        {job.benefits.map((benefit, idx) => (
                          <li key={idx} className="text-base">{benefit}</li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                </CardContent>
              </Card>
            )}

            {/* Work Details */}
            {(job.work_arrangement || 
              job.team_size || 
              job.location_restrictions?.length ||
              job.culture_keywords?.length) && (
              <Card className="mt-6">
                <CardHeader>
                  <CardTitle>Work Details</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {job.work_arrangement && (
                    <div>
                      <h4 className="text-sm font-medium text-muted-foreground mb-1">Work Arrangement</h4>
                      <Badge variant="outline">{job.work_arrangement}</Badge>
                    </div>
                  )}
                  {job.team_size && (
                    <div>
                      <h4 className="text-sm font-medium text-muted-foreground mb-1">Team Size</h4>
                      <p className="text-base">{job.team_size}</p>
                    </div>
                  )}
                  {job.location_restrictions?.length ? (
                    <div>
                      <h4 className="text-sm font-medium text-muted-foreground mb-1">Location Requirements</h4>
                      <div className="flex flex-wrap gap-2">
                        {job.location_restrictions.map((location, idx) => (
                          <Badge key={idx} variant="secondary">{location}</Badge>
                        ))}
                      </div>
                      {job.exclusive_location_requirement && (
                        <p className="text-sm text-muted-foreground mt-2">
                          * Must be located in one of these regions
                        </p>
                      )}
                    </div>
                  ) : null}
                  {job.culture_keywords?.length ? (
                    <div>
                      <h4 className="text-sm font-medium text-muted-foreground mb-2">Culture</h4>
                      <div className="flex flex-wrap gap-2">
                        {job.culture_keywords.map((keyword, idx) => (
                          <Badge key={idx} variant="outline">{keyword}</Badge>
                        ))}
                      </div>
                    </div>
                  ) : null}
                </CardContent>
              </Card>
            )}
          </>
        )}

        {company ? (
          <>
            <Separator className="my-8" />
            <Card>
              <CardHeader>
                <CardTitle>About {company.name}</CardTitle>
                {company.tagline ? (
                  <CardDescription>{company.tagline}</CardDescription>
                ) : null}
              </CardHeader>
              <CardContent className="space-y-6">
                {company.description ? (
                  <p className="text-base leading-7 text-muted-foreground">
                    {company.description}
                  </p>
                ) : null}

                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Building2 className="h-4 w-4" /> Industry
                    </div>
                    <p className="font-medium">
                      {company.industry ?? "Not specified"}
                    </p>
                  </div>

                  <div className="space-y-1">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Users className="h-4 w-4" /> Company Size
                    </div>
                    <p className="font-medium">
                      {formatCompanySize(
                        company.company_size_min,
                        company.company_size_max
                      )}
                    </p>
                  </div>

                  <div className="space-y-1">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <MapPin className="h-4 w-4" /> Headquarters
                    </div>
                    <p className="font-medium">
                      {[company.hq_city, company.hq_state, company.hq_country]
                        .filter((value): value is string => Boolean(value))
                        .join(", ") || "Not specified"}
                    </p>
                  </div>

                  <div className="space-y-1">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Calendar className="h-4 w-4" /> Founded
                    </div>
                    <p className="font-medium">
                      {company.founded_year ?? "Not specified"}
                    </p>
                  </div>

                  {company.website ? (
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Globe className="h-4 w-4" /> Website
                      </div>
                      <Link
                        href={company.website}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 font-medium text-primary hover:underline"
                      >
                        Visit site
                        <ExternalLink className="h-3.5 w-3.5" />
                      </Link>
                    </div>
                  ) : null}

                  {company.linkedin_url ? (
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <ExternalLink className="h-4 w-4" /> LinkedIn
                      </div>
                      <Link
                        href={company.linkedin_url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 font-medium text-primary hover:underline"
                      >
                        View profile
                        <ExternalLink className="h-3.5 w-3.5" />
                      </Link>
                    </div>
                  ) : null}
                </div>

                {company.specialities?.length ? (
                  <div>
                    <p className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                      Specialities
                    </p>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {company.specialities.map((speciality) => (
                        <Badge key={speciality} variant="secondary">
                          {speciality}
                        </Badge>
                      ))}
                    </div>
                  </div>
                ) : null}
              </CardContent>
            </Card>
          </>
        ) : null}

        <Separator className="my-8" />

        <Card>
          <CardHeader>
            <CardTitle>Additional Information</CardTitle>
          </CardHeader>
          <CardContent>
            <dl className="grid gap-4 sm:grid-cols-2">
              <div>
                <dt className="text-sm font-semibold text-muted-foreground">
                  Listing Type
                </dt>
                <dd className="text-base font-medium">
                  {job.listing_type ?? "Not specified"}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-semibold text-muted-foreground">
                  Company Industry
                </dt>
                <dd className="text-base font-medium">
                  {job.company_industry ?? company?.industry ?? "Not specified"}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-semibold text-muted-foreground">
                  Company Headquarters
                </dt>
                <dd className="text-base font-medium">
                  {job.company_headquarters ??
                    ([company?.hq_city, company?.hq_state, company?.hq_country]
                      .filter((value): value is string => Boolean(value))
                      .join(", ") || "Not specified")}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-semibold text-muted-foreground">
                  Company Employees
                </dt>
                <dd className="text-base font-medium">
                  {job.company_employees_count ?? "Not specified"}
                </dd>
              </div>
              <div className="sm:col-span-2">
                <dt className="text-sm font-semibold text-muted-foreground">
                  Contact Emails
                </dt>
                <dd className="mt-2 flex flex-wrap gap-3">
                  {job.emails?.length ? (
                    job.emails.map((email) => (
                      <Link
                        key={email}
                        href={`mailto:${email}`}
                        className="text-primary hover:underline"
                      >
                        {email}
                      </Link>
                    ))
                  ) : (
                    <span className="text-muted-foreground">Not provided</span>
                  )}
                </dd>
              </div>
            </dl>
          </CardContent>
        </Card>
      </div>
    </PageLayout>
    </AuthGuard>
  )
}
