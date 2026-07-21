# SiteSafe

Construction-site safety monitoring: PPE + crane hook/suspended-load
detection (YOLO), incidents, live camera streaming, and real-time
notifications.

## What's real vs. what's a placeholder

Everything below has been **actually run and verified** in the process
of building this (REST API smoke-tested end-to-end with a real SQLite
DB, Alembic migration generated and confirmed to upgrade/downgrade
cleanly, frontend `npm run build` completed successfully):

- Auth (register/login/JWT), Cameras/Incidents/Notifications CRUD,
  dashboard + analytics endpoints
- Database schema + Alembic migration
- Full frontend build (React + Vite + Tailwind)

**Not verified, because the pieces needed for it aren't included in this
project:**

- **Live detection.** `backend/models/` needs your trained
  `ppe.pt` and `hook_load.pt` weight files — they were never part of
  any upload, only the code that loads them. Without them, PPE
  detection falls back to a generic COCO model (detects "person" only,
  no hardhat/vest awareness), and hook/load detection will fail to
  start entirely. See `backend/models/README.md`.
- **PPE violation class names.** `PPE_VIOLATION_LABELS` in
  `app/services/detection_service.py` is a best-effort guess at your
  model's label names (`no_hardhat`, `no_vest`, etc.) — there was no
  `ppe.pt` to inspect. Update it once you can check
  `YOLO("models/ppe.pt").names`.
- **Camera calibration.** `backend/config.py` (ground-plane geometry
  constants) has placeholder values — this file was referenced
  everywhere but never actually existed in any upload. Tune it per
  camera, or leave `use_calibrated=False` (the default in
  `detection_service.py`) to use the simpler pixel-space fall-zone
  check, which needs no calibration.

## Quick start (Docker — recommended)

```bash
cp .env.example .env          # then edit JWT_SECRET_KEY to something random
docker-compose up --build
```

This starts Postgres, runs Alembic migrations automatically, and starts
both the backend (`:8000`) and frontend dev server (`:5173`).

Open **http://localhost:5173**, register an account, and go.

To stop: `docker-compose down` (add `-v` to also wipe the Postgres volume).

## Manual setup (no Docker)

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# edit .env: set DATABASE_URL to a Postgres instance you have running,
# and JWT_SECRET_KEY to something random

# create the database first, e.g.:
#   createdb sitesafe
alembic upgrade head

uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
cp .env.example .env    # VITE_API_BASE_URL, defaults to localhost:8000

npm run dev
```

Open http://localhost:5173

## Enabling real detection

1. Drop your trained weights into `backend/models/`:
   `ppe.pt`, `hook_load.pt`, `bytetrack.yaml`
2. Check `YOLO("models/ppe.pt").names` and update
   `PPE_VIOLATION_LABELS` in `app/services/detection_service.py` to
   match your actual class names.
3. Add a camera with a real `feed_url` (RTSP/HTTP stream), or leave it
   blank to fall back to a local webcam / a test clip dropped in
   `backend/test_videos/ppe.mp4`.
4. Open that camera's "View live" tile in the frontend — this opens
   the `/api/cameras/{id}/stream` WebSocket, which runs detection on
   each frame and creates Incident + Notification rows automatically
   when a rule fires (30s cooldown per camera+type to avoid flooding).
5. Tune `backend/config.py` for your actual camera mounting
   height/tilt/focal length if you want the calibrated (ground-plane)
   fall-zone math instead of the pixel-space default.

## Project structure

```
sitesafe/
├── docker-compose.yml
├── backend/
│   ├── app/               FastAPI app: models, schemas, crud, routers, services
│   ├── detector/           YOLO wrappers (PPE, hook/load, tracking)
│   ├── geometry/           Ground-plane calibration, danger-zone math
│   ├── rules/              Fall-zone violation rules
│   ├── reporting/          Screenshot + JSON incident logging
│   ├── models/             Drop your .pt weight files here (not included)
│   └── alembic/            DB migrations
└── frontend/
    └── src/
        ├── context/         Auth + app-wide data context
        ├── hooks/           Data hooks (cameras, incidents, notifications, dashboard, camera stream)
        ├── services/        REST + WebSocket API clients
        ├── components/      Layout, LiveStream, NotificationBell, ProtectedRoute
        └── pages/           Dashboard, Incidents, Camera, Analytics, Login, Register
```

## Known gaps / next steps

- No automated tests
- Single-process WebSocket connection tracking (`app/services/connection_manager.py`)
  — fine for one uvicorn worker; move to Redis pub/sub if you scale to
  multiple workers/processes
- No role-based access control yet (the `role` field on `User` exists
  but nothing checks it)
- No rate limiting on auth endpoints
