# Virtual Lab Frontend (Next.js)

## Overview

React 프론트엔드 - FastAPI 백엔드와 통신하는 웹 UI

## Tech Stack

- **Framework**: Next.js 16.1.6
- **Language**: TypeScript 5.x
- **Styling**: Tailwind CSS 4.x
- **HTTP Client**: Fetch API

## Project Structure

```
frontend/
├── src/
│   ├── app/              # App Router pages
│   │   ├── api/          # Next.js API routes
│   │   └── page.tsx      # Main page
│   └── lib/              # Utilities
│       └── api.ts        # FastAPI client
├── public/               # Static files
├── next.config.ts        # Next.js configuration
├── tailwind.config.ts    # Tailwind configuration
└── tsconfig.json         # TypeScript configuration
```

## Setup

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Environment Variables

Create `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Run Development Server

```bash
npm run dev
```

Server runs at: http://localhost:3000

## API Integration

### Proxy Configuration

Next.js rewrites `/api/*` requests to FastAPI backend:

```typescript
// next.config.ts
{
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/api/:path*",
      },
    ];
  }
}
```

### API Client

Use the API client in `src/lib/api.ts`:

```typescript
import { submitResearch, healthCheck } from '@/lib/api';

// Submit research request
const result = await submitResearch({
  topic: "NGT safety assessment",
  constraints: "Focus on EU regulations"
});

// Health check
const health = await healthCheck();
```

## CORS Configuration

FastAPI backend is configured to accept requests from:
- `http://localhost:3000` (Next.js dev server)
- `http://localhost:8501` (Streamlit dev server)

## Testing

### Test Next.js API Route

```bash
curl http://localhost:3000/api/test
```

Expected response:
```json
{
  "status": "ok",
  "message": "Next.js frontend is running",
  "timestamp": "2026-02-08T10:01:15.548Z"
}
```

### Test FastAPI Connection

Ensure FastAPI is running:
```bash
cd ..
uvicorn server:app --reload --port 8000
```

Test health endpoint:
```bash
curl http://localhost:3000/api/health
```

## Scripts

- `npm run dev` - Start development server (http://localhost:3000)
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

## Notes

- Next.js uses Turbopack for faster development builds
- TypeScript is enabled by default
- Tailwind CSS is configured with PostCSS
- All API requests are proxied to avoid CORS issues
