from __future__ import annotations

import logging
import pandas as pd
import typer
from jobspy import scrape_jobs as jobspy_scrape_jobs
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app.db import SessionLocal
from app.models.company import Company
from app.models.job import Job
from cli.main import app, console
from cli.utils import (
    fetch_company_from_proxycurl,
    map_dataframe_row_to_job,
    map_proxycurl_to_company,
    normalize_linkedin_url,
)

logger = logging.getLogger(__name__)


@app.command()
def scrape(
    search_term: str = typer.Option(
        ...,
        "--search-term",
        "-s",
        help="Job search term (e.g., 'software engineer').",
    ),
    location: str = typer.Option(
        ...,
        "--location",
        "-l",
        help="Job location (e.g., 'San Francisco, CA').",
    ),
    results_wanted: int = typer.Option(
        15,
        "--results-wanted",
        "-r",
        min=1,
        show_default=True,
        help="Number of jobs to request from job boards.",
    ),
) -> None:
    """Scrape jobs, enrich companies, and persist everything to PostgreSQL."""
    console.print(
        Panel.fit(
            f"[bold white]Job Scraping Configuration[/]\n"
            f"[cyan]Search:[/] {search_term}\n"
            f"[cyan]Location:[/] {location}\n"
            f"[cyan]Results:[/] {results_wanted}",
            border_style="cyan",
        )
    )

    session = SessionLocal()
    jobs_df: pd.DataFrame | None = None

    try:
        progress = Progress(
            SpinnerColumn(),
            TextColumn("{task.description}"),
            BarColumn(bar_width=None),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console,
            transient=False,
        )

        with progress:
            scrape_task = progress.add_task(
                "[bold]Scraping jobs from LinkedIn...[/bold]", total=1
            )
            try:
                jobs_df = jobspy_scrape_jobs(
                    site_name=["linkedin"],
                    search_term=search_term,
                    location=location,
                    results_wanted=results_wanted,
                    linkedin_fetch_description=True,
                    country_indeed="USA",
                    is_remote=True,
                    hours_old=3,
                )
            except Exception as exc:  # noqa: BLE001
                logger.exception("Job scraping failed")
                console.print(f"[bold red]Failed to scrape jobs:[/] {exc}")
                raise typer.Exit(code=1) from exc
            finally:
                progress.update(scrape_task, completed=1)

            if jobs_df is None or jobs_df.empty:
                console.print("[yellow]No jobs found for the given criteria.[/]")
                raise typer.Exit(code=0)

            console.print(
                f"[green]Scraped {len(jobs_df)} jobs with "
                f"{len(jobs_df.columns)} fields.[/]"
            )
            preview_columns = [
                col
                for col in ["title", "company", "location", "job_url"]
                if col in jobs_df.columns
            ]
            if preview_columns:
                console.print(jobs_df[preview_columns].head().to_string(index=False))

            linkedin_urls = _extract_unique_linkedin_urls(jobs_df)
            console.print(
                f"[bold cyan]Found {len(linkedin_urls)} LinkedIn company URLs.[/]"
            )

            if not settings.PROXYCURL_API_KEY:
                console.print(
                    "[bold red]Proxycurl API key missing.[/] "
                    "Set PROXYCURL_API_KEY in your environment or .env file to enable company enrichment."
                )
                raise typer.Exit(code=1)

            company_cache: dict[str, int] = {}
            company_stats = {
                "created": 0,
                "cached": 0,
                "failed": 0,
            }

            if linkedin_urls:
                company_task = progress.add_task(
                    "[bold]Enriching company profiles...[/bold]",
                    total=len(linkedin_urls),
                )
                for linkedin_url in linkedin_urls:
                    company_id = _ensure_company(
                        session,
                        linkedin_url,
                        company_cache,
                        company_stats,
                    )
                    if company_id:
                        company_cache[linkedin_url] = company_id
                    progress.advance(company_task, 1)
                progress.update(company_task, completed=len(linkedin_urls))
                session.commit()

            jobs_task = progress.add_task(
                "[bold]Storing jobs in database...[/bold]",
                total=len(jobs_df),
            )
            job_stats = {
                "created": 0,
                "skipped": 0,
            }
            for _, row in jobs_df.iterrows():
                _ = _persist_job(
                    session=session,
                    row=row,
                    company_cache=company_cache,
                    job_stats=job_stats,
                )
                progress.advance(jobs_task, 1)
            progress.update(jobs_task, completed=len(jobs_df))
            session.commit()

        _show_summary(
            total_jobs=len(jobs_df),
            job_created=job_stats["created"],
            job_skipped=job_stats["skipped"],
            companies_found=len(linkedin_urls),
            company_created=company_stats["created"],
            company_cached=company_stats["cached"],
            company_failed=company_stats["failed"],
        )
    except typer.Exit:
        raise
    except Exception as exc:  # noqa: BLE001
        session.rollback()
        logger.exception("Scrape command failed")
        console.print(f"[bold red]Unexpected error:[/] {exc}")
        raise typer.Exit(code=1) from exc
    finally:
        session.close()


def _extract_unique_linkedin_urls(df: pd.DataFrame) -> list[str]:
    linkedin_urls: set[str] = set()
    source_columns = [
        column for column in ("company_url", "company_url_direct") if column in df.columns
    ]
    if not source_columns:
        return []

    for column in source_columns:
        for raw_url in df[column].dropna().astype(str):
            normalized = normalize_linkedin_url(raw_url)
            if normalized:
                linkedin_urls.add(normalized)
    return sorted(linkedin_urls)


def _ensure_company(
    session,
    linkedin_url: str,
    company_cache: dict[str, int],
    company_stats: dict[str, int],
) -> int | None:
    if linkedin_url in company_cache:
        company_stats["cached"] += 1
        return company_cache[linkedin_url]

    existing = (
        session.query(Company).filter(Company.linkedin_url == linkedin_url).first()
    )
    if existing:
        company_stats["cached"] += 1
        return existing.id

    company_data = fetch_company_from_proxycurl(linkedin_url)
    if not company_data:
        company_stats["failed"] += 1
        return None

    try:
        with session.begin_nested():
            company = map_proxycurl_to_company(company_data, linkedin_url)
            session.add(company)
            session.flush()
        company_stats["created"] += 1
        return company.id
    except SQLAlchemyError as exc:
        company_stats["failed"] += 1
        logger.exception("Failed to persist company %s", linkedin_url)
        console.print(
            f"[red]Failed to save company {linkedin_url}: "
            f"{exc.__class__.__name__}[/]"
        )
        return None


def _persist_job(
    session,
    row: pd.Series,
    company_cache: dict[str, int],
    job_stats: dict[str, int],
) -> Job | None:
    job_url = row.get("job_url")
    if not job_url:
        return None

    existing = session.query(Job.id).filter(Job.job_url == job_url).first()
    if existing:
        job_stats["skipped"] += 1
        return None

    company_id = None
    linkedin_url = normalize_linkedin_url(row.get("company_url"))
    if linkedin_url:
        company_id = company_cache.get(linkedin_url)
        if company_id is None:
            company_id = (
                session.query(Company.id)
                .filter(Company.linkedin_url == linkedin_url)
                .scalar()
            )
            if company_id:
                company_cache[linkedin_url] = company_id

    try:
        with session.begin_nested():
            job = map_dataframe_row_to_job(row, company_id)
            session.add(job)
            session.flush()
        job_stats["created"] += 1
        return job
    except SQLAlchemyError as exc:
        job_stats["skipped"] += 1
        logger.exception("Failed to persist job %s", job_url)
        console.print(
            f"[red]Failed to save job {job_url}: {exc.__class__.__name__}[/]"
        )
        return None


def _show_summary(
    *,
    total_jobs: int,
    job_created: int,
    job_skipped: int,
    companies_found: int,
    company_created: int,
    company_cached: int,
    company_failed: int,
) -> None:
    table = Table(title="Scrape Summary")
    table.add_column("Metric", justify="left", style="cyan", no_wrap=True)
    table.add_column("Count", justify="right", style="green")

    table.add_row("Jobs Scraped", str(total_jobs))
    table.add_row("Jobs Created", str(job_created))
    table.add_row("Jobs Skipped (duplicates)", str(job_skipped))
    table.add_row("Companies Found", str(companies_found))
    table.add_row("Companies Created", str(company_created))
    table.add_row("Companies Cached", str(company_cached))
    table.add_row("Companies Failed", str(company_failed))

    console.print(table)
    console.print(
        Panel(
            "[bold green]Scrape completed successfully![/]",
            border_style="green",
        )
    )
