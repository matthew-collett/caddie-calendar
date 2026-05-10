# Caddie Calendar

A web app that auto-books golf tee times the moment the booking window opens.

## Stack

- **api/** — Flask, APScheduler, SQLAlchemy, Postgres, gunicorn + gevent.
- **ui/** — React 19, Vite, TypeScript, TanStack Query, React Hook Form, Tailwind v4, shadcn/ui.
- **Deploy** — API on Railway, UI on S3 + CloudFront, both via GitHub Actions on push to `main`.
