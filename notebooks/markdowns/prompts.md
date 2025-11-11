### Init prompt for project setup
```
i need to setup backend and frontend projects for job apply assistant bot. 

PROJECT SUMMARY: 

need to build tool / bot that scrape businesses from linkedin, process with llm, filter the jobs, and generate the tailored resume for each job. 

CURRENT TASK: 

scaffold backend and frontend project and implement a script / job that scrape the jobs and company profile; store it into db. 

ADDITIONAL REQUIREMENTS: 

need to be simple, quick, and fast solution rather than comprehensive. 

BACKEND STACKS: 

fastapi for backend apis, 

custom cli to start scraping task, 

use jobspy for scraping jobs, 

check [mention] to get linkedin company profile info 

postgresql for db (use docker compose file for local dev setup. skip dockerizing fastapi itself) 

use pdm for requirements / packages. 

BACKEND TASK: 

- setup models for job and company 
- setup a CLI tool (need to be good UI, use rich and typer packages) that scrape jobs + company profile and store it into db (avoid duplicate scrapes for company profile)
- no auth required (just internal tool)

FRONTEND TASK: 

- use react / nextjs to setup the project. 
- simple ui / table that shows jobs in the table. 
- need to show detailed job (job description, company profile, etc)
- use any framework, but simpler is better 
```