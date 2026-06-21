# Deployment Guide

## Repository Audit

Large or generated files excluded from Git:

- `traffic_help.db` — generated SQLite database (~118 MB)
- `data/raw/*.csv` — source dataset (~104 MB)

These are excluded via `.gitignore` and should not be committed. For backup or CI restoration, use Git LFS or external artifact storage.

---

## GitHub Upload with Git LFS

Large data files must use Git LFS because GitHub rejects files over 100 MB.

```powershell
# 1. Install Git LFS (once)
winget install GitLfs
# or: choco install git-lfs

# 2. Initialize LFS in the repository
git lfs install

# 3. Track large file types
git lfs track "*.db"
git lfs track "*.csv"
git lfs track "*.zip"

# 4. Commit the LFS config
git add .gitattributes
git commit -m "Configure Git LFS for large data files"

# 5. Add everything else
git add .
git commit -m "Initial commit: Sprint 1 MVP deployment-ready"

# 6. Set branch and remote
git branch -M main
git remote add origin https://github.com/mj064/BangalorePolice-Helper.git

# 7. Push (LFS files upload separately)
git push -u origin main
```

Recommended pre-push checklist:

- [ ] `.env` files are NOT committed
- [ ] `.gitignore` does NOT list `*.db` or `*.csv` (LFS handles them)
- [ ] `.gitattributes` contains LFS tracking entries
- [ ] README.md renders cleanly on GitHub

### Verify LFS is working

```powershell
git lfs ls-files
```

You should see `traffic_help.db` and `data/raw/jan to may police violation_anonymized791b166.csv` in the output.

---

## Environment Variables

### Backend

| Variable | Required | Example |
|----------|----------|---------|
| `DATABASE_URL` | Yes | `sqlite+aiosqlite:///./traffic_help.db` |
| `DATA_CSV_PATH` | Yes | `data/raw/jan to may police violation_anonymized791b166.csv` |
| `CORS_ORIGINS` | Yes | `["https://<frontend-domain>"]` |
| `PYTHONPATH` | Render/Linux | `.` |

### Frontend

| Variable | Required | Example |
|----------|----------|---------|
| `VITE_API_BASE_URL` | Yes | `/api` or `https://<backend-domain>/api` |

---

## Render (Backend)

### Prerequisites

- GitHub repository connected to Render
- `traffic_help.db` and `data/raw/*.csv` available in the repo or mounted externally

### Steps

1. Create a new **Web Service**.
2. Connect the GitHub repository.
3. Set **Root Directory** to `backend` (or leave blank if `render.yaml` handles paths).
4. Set **Runtime** to **Python 3**.
5. Set **Build Command**: `pip install -r backend/requirements.txt`
6. Set **Start Command**: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
7. Add environment variables from the table above.
8. Set **Health Check Path** to `/health`.
9. Click **Create Web Service**.

### Notes

- First deployment may take 2–5 minutes while dependencies install.
- Startup will ingest CSV and train LightGBM once; consider an **Instance Type** with at least 512 MB RAM.
- SQLite file persists only if stored on the same filesystem; Render free instances have ephemeral filesystems. For persistence, use:
  - Render Persistent Disks, OR
  - External object storage (e.g., Supabase Storage) with sync on boot, OR
  - Migrate to PostgreSQL/PostGIS on Render.

---

## Vercel (Frontend)

### Prerequisites

- Backend URL known (e.g., `https://<service>.onrender.com`)
- Frontend repository directory ready

### Steps

1. Import the project into Vercel.
2. Set **Framework Preset** to **Vite**.
3. Set **Root Directory** to `frontend`.
4. Set **Build Command** to `npm run build`.
5. Set **Output Directory** to `dist`.
6. Add environment variable:
   - `VITE_API_BASE_URL` = `https://<backend-url>/api`
7. Click **Deploy**.

### Notes

- If the backend and frontend are on different domains, ensure CORS allows the frontend origin.
- Vercel Preview deployments inherit production environment variables.

---

## Docker

```powershell
# Build and start everything
docker compose up --build

# Stop
docker compose down
```

Services:

- Frontend: `http://localhost`
- Backend API docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

Volumes:

- `./traffic_help.db` is mounted into both containers.
- `./data/raw` is mounted for CSV ingestion.

---

## Troubleshooting

### Backend fails to start on Render

- Check that `DATA_CSV_PATH` points to an existing file.
- Check that `PYTHONPATH` is set to `.` so `backend.app` imports resolve.
- Inspect logs for SQLite file permissions.

### Frontend cannot reach backend

- Verify `VITE_API_BASE_URL` is set correctly.
- Check backend CORS configuration in `backend/app/core/config.py`.
- Inspect browser network tab for 404/403 responses.

### Hotspot detection never runs

- Ensure `hotspots` table is empty or absent. Startup runs detection only when the table has zero rows.
- If needed, truncate the table or delete the SQLite file before a fresh run.

### LightGBM training is slow

- Normal on first boot. Subsequent starts reuse the in-memory prediction cache.
- For faster demo startups, persist the model artifact to disk and load it instead of retraining.

---

## Known Deployment Risks

1. **Ephemeral filesystem on Render**: SQLite DB and any generated model artifacts disappear on redeploy unless a Persistent Disk is attached.
2. **Large dataset size**: CSV + DB total ~220 MB. CI or fresh clones without Git LFS must fetch these separately.
3. **Startup latency**: LightGBM training adds ~20–30 s before the API is ready.
4. **CORS granularity**: Current `CORS_ORIGINS` allows all origins in some environments. Tighten before public exposure.
5. **No HTTPS termination in Docker**: Frontend container serves HTTP only; terminate TLS at a reverse proxy in production.
6. **No database migrations**: Schema changes currently rely on `Base.metadata.create_all` in `lifespan`. Use Alembic or similar for production rollouts.

---

## Recommended Deployment Order

1. Push to GitHub with `.gitignore` enforced.
2. Deploy backend to Render; verify `/health` and `/api/dashboard/summary`.
3. Deploy frontend to Vercel; set `VITE_API_BASE_URL` to the Render backend.
4. Run end-to-end smoke test:
   - Load dashboard
   - Select a hotspot
   - Verify predictions and recommendations render
5. Attach a Render Persistent Disk or migrate to PostgreSQL/PostGIS if persistence across deploys is required.