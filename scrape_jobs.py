#!/usr/bin/env python3
"""
LinkedIn Job Scraper using JobSpy Library
Scrapes job postings from LinkedIn and saves them to a CSV file.


https://github.com/nubelaco/enrich-linkedin-companies-in-bulk
"""

import csv
from jobspy import scrape_jobs


def main():
    """Main function to scrape LinkedIn jobs and save to CSV."""
    
    print("Starting LinkedIn job scraper...")
    print("-" * 50)
    
    # Hardcoded search parameters
    search_term = "software engineer"
    location = "San Francisco, CA"
    results_wanted = 1
    
    print(f"Search Term: {search_term}")
    print(f"Location: {location}")
    print(f"Results Wanted: {results_wanted}")
    print("-" * 50)
    
    try:
        # Scrape jobs from LinkedIn
        jobs = scrape_jobs(
            site_name=["linkedin"],
            search_term=search_term,
            location=location,
            results_wanted=results_wanted,
            linkedin_fetch_description=True,  # Get full job details
            hours_old=None,  # No time filter
            country_indeed='USA'
        )
        
        # Check if any jobs were found
        if jobs is not None and len(jobs) > 0:
            print(f"\n✓ Successfully scraped {len(jobs)} jobs from LinkedIn")
            
            # Display first few results
            print("\nFirst 3 results preview:")
            print(jobs.head(3).to_string())
            
            # Save to CSV
            output_file = "jobs.csv"
            jobs.to_csv(
                output_file,
                quoting=csv.QUOTE_NONNUMERIC,
                escapechar="\\",
                index=False
            )
            print(f"\n✓ Jobs saved to '{output_file}'")
            
        else:
            print("\n✗ No jobs found. Try adjusting your search parameters.")
            
    except Exception as e:
        print(f"\n✗ Error occurred while scraping jobs: {str(e)}")
        print("\nTroubleshooting tips:")
        print("- Check your internet connection")
        print("- LinkedIn may be rate-limiting requests (try using proxies)")
        print("- Verify that python-jobspy is installed correctly")
        raise


if __name__ == "__main__":
    main()

