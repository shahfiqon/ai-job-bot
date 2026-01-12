from jobspy import scrape_jobs as jobspy_scrape_jobs


jobs_df = jobspy_scrape_jobs(
    site_name=["indeed"],
    search_term="python",
    results_wanted=100,
    is_remote=True,
    hours_old=1,
)

print(f"Scraped {len(jobs_df)} jobs.")

import json

# Save jobs_df as JSON file
output_path = "jobs_output.json"
if jobs_df is not None:
    jobs_df.to_json(output_path, orient="records", force_ascii=False, indent=2)
    print(f"Saved jobs to {output_path}")
else:
    print("jobs_df is None. Nothing to write.")

