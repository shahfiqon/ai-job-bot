# Job Apply Assistant - Frontend

Next.js 14 frontend application for browsing and managing job opportunities. Built with TypeScript, Tailwind CSS, and shadcn/ui components.

## Tech Stack
- Next.js 14+ (App Router)
- React 18
- TypeScript
- Tailwind CSS
- shadcn/ui
- date-fns
- Lucide React

## Prerequisites
- Node.js 18+ (or 20+)
- npm

## Backend Setup
The frontend expects the FastAPI backend + PostgreSQL stack to be running locally.

1. **Start PostgreSQL (run from repo root)**
   ```bash
   docker-compose up -d
   ```
2. **Start the backend API**
   ```bash
   cd backend
   pdm run uvicorn app.main:app --reload
   ```
   The API will be available at http://localhost:8000.
3. **Seed jobs (optional but recommended)**
   ```bash
   cd backend
   pdm run jobbot scrape --search-term "software engineer" --location "San Francisco" --results-wanted 20
   ```

## Getting Started

1. **Configure environment variables**
   ```bash
   cd frontend
   cp .env.example .env.local
   ```
   Edit `.env.local` and set `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` (or your deployed API URL).
2. **Install dependencies**
   ```bash
   cd frontend
   npm install
   ```
3. **Run the development server**
   ```bash
   npm run dev
   ```
   Open http://localhost:3000 in your browser.
4. **Build for production**
   ```bash
   npm run build
   npm start
   ```

## Environment Variables
- `NEXT_PUBLIC_API_BASE_URL` (required): URL of the FastAPI backend
  - Development default: `http://localhost:8000`
  - Production example: `https://your-api-domain.com`
  - Must include the `NEXT_PUBLIC_` prefix so client components can make requests.

## Project Structure
```
frontend/
├── app/                    # App Router entry points
│   ├── layout.tsx          # Root layout with fonts and metadata
│   ├── error.tsx           # Root error boundary
│   ├── loading.tsx         # Root loading UI
│   ├── page.tsx            # Jobs listing page
│   ├── jobs/[id]/          # Dynamic job detail route
│   │   ├── page.tsx        # Job detail server component
│   │   ├── loading.tsx     # Route-level loading UI
│   │   └── error.tsx       # Route-level error boundary
│   ├── not-found.tsx       # Custom 404 experience
│   └── globals.css         # Global styles and Tailwind layers
├── components/             # UI components
│   ├── ui/                 # shadcn/ui primitives
│   │   ├── badge.tsx       # Job labels
│   │   ├── button.tsx      # Action buttons
│   │   ├── card.tsx        # Content sections
│   │   └── separator.tsx   # Visual dividers
│   ├── jobs-table.tsx      # Jobs listing table component
│   └── page-layout.tsx     # Shared page layout/header/footer
├── lib/                    # Utilities, API helpers, mock data
│   ├── api.ts              # REST client for the FastAPI backend
│   ├── utils.ts            # cn, formatting, and text helpers
│   └── mock-data.ts        # Mock job & company data with helpers
├── types/                  # Shared TypeScript types
│   └── job.ts              # Job and Company interfaces
└── public/                 # Static assets
```

## API Integration
- API client lives in `lib/api.ts` and wraps `fetch` with helpful TypeScript types plus ISO date handling.
- `GET /api/jobs` powers the home page server component; results hydrate the client-only `JobsTable`.
- `GET /api/jobs/{id}` feeds both the detail page and its `generateMetadata` function for improved SEO.
- Loading states rely on `app/loading.tsx` and `app/jobs/[id]/loading.tsx`.
- Errors bubble to `app/error.tsx` and `app/jobs/[id]/error.tsx`, providing retry/back actions.
- Environment-driven base URL lets the frontend point to staging/production APIs without code changes.

## Features
- ✅ Responsive jobs listing table with remote indicators, salary display, and relative dates
- ✅ Job detail page with company profile, markdown descriptions, and custom 404 handling
- ✅ Loading and error boundaries for both listing and detail routes
- ✅ API integration with the FastAPI backend
  - Fetches paginated jobs from `GET /api/jobs`
  - Fetches job detail + company info from `GET /api/jobs/{id}`
  - Basic limit/offset pagination plumbing ready for future UI controls
  - Graceful error states with retry/back buttons
  - Configurable via `NEXT_PUBLIC_API_BASE_URL`

## Job Detail Page
The `/jobs/[id]` route fetches live data from the backend API (with mock data available for local testing via `lib/mock-data.ts`).

Features:
- Full markdown job description rendered with Tailwind Typography + custom prose styles
- Company profile with description, industry, size, headquarters, founded year, website, LinkedIn, and specialities
- Job metadata: location, remote indicator, job types, compensation, posted date, level, function
- Action buttons: Apply Now (opens the job URL), Save Job, Share
- Breadcrumb navigation back to the jobs listing and a custom 404 page when a job isn’t found
- Responsive grid layout built with shadcn/ui Card, Separator, Badge, and Button components

## Development Notes
- Data loads from the FastAPI backend running at `http://localhost:8000` via the helpers in `lib/api.ts`.
- `NEXT_PUBLIC_API_BASE_URL` controls the API target for both server and client components.
- Mock data under `lib/mock-data.ts` remains available for offline/local testing but is no longer wired into the UI.
- Job detail still uses dynamic routes (`/jobs/[id]`) with `notFound()` for 404s plus route-level loading/error files.
- Typography styles reside in `app/globals.css` to keep markdown job descriptions readable.

## Adding shadcn/ui Components
```bash
npx shadcn-ui@latest add <component-name>
```
Example: `npx shadcn-ui@latest add button`

## Available Scripts
- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm start` - Start production server
- `npm run lint` - Run ESLint

## Styling
- Tailwind CSS drives layout/styling; customize tokens via `tailwind.config.ts`.
- shadcn/ui relies on CSS variables declared in `app/globals.css`.
- Responsive breakpoints: sm (640px), md (768px), lg (1024px), xl (1280px), 2xl (1536px).

## Type Safety
- Strict TypeScript configuration (`tsconfig.json`).
- Domain types in `types/` mirror backend SQLAlchemy models for seamless integration.

## Troubleshooting
- **"Failed to load jobs"** – ensure the backend server is running on `http://localhost:8000`, confirm `NEXT_PUBLIC_API_BASE_URL` in `.env.local`, verify PostgreSQL has data, and review browser console/network logs.
- **"Job not found"** – the posting likely expired or was removed; navigate back to `/` and pick another listing.
- **CORS errors** – double-check the backend CORS settings still allow `http://localhost:3000` and restart the API server after changes.
