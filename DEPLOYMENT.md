# Deployment Guide — CI/CD (Docker Swarm + Self-Hosted Runner)

This project deploys automatically. Every push to the `main` branch builds a new
Docker image **on your server** and updates the running Docker Swarm stack with a
zero-downtime rolling update. If the new version fails, Swarm rolls back
automatically.

```
git push origin main
        │
        ▼
GitHub Actions
   ├─ CI  (ci.yml)  → lint + build + smoke test   [GitHub's runners]
   └─ CD  (cd.yml)  → build image + deploy stack   [YOUR server, self-hosted]
                                   │
                                   ▼
                         docker stack deploy → rolling update
```

You only need to do the **one-time server setup** below once. After that,
deployment is fully automatic on every `git push`.

---

## What you need to do on the server (one time)

Your server already has Docker installed and configured. Complete these 4 steps.

### Step 1 — Initialize Docker Swarm (if not already done)

```bash
# Check current state
docker info --format '{{.Swarm.LocalNodeState}}'
```

If it prints `inactive`, initialize Swarm:

```bash
docker swarm init
# On a server with multiple network interfaces, pin the address:
# docker swarm init --advertise-addr <SERVER_PUBLIC_IP>
```

If it already prints `active`, skip this step.

### Step 2 — Create the Docker secrets

The production stack (`compose.prod.swarm.yaml`) reads all sensitive values from
**Docker Swarm secrets** — nothing sensitive lives in the repo. Create all ten
secrets once. Replace the example values with your real ones.

```bash
# --- Database connection strings (note the service name "db" as the host) ---
printf 'postgresql+asyncpg://postgres:CHANGE_ME@db:5432/fastapi_ecom'  | docker secret create database_url -
printf 'postgresql+psycopg2://postgres:CHANGE_ME@db:5432/fastapi_ecom' | docker secret create database_sync_url -

# --- App security ---
printf '29-oFCiXVm9pyCtGkZVkQGxrO0RkPiqwYtTwie5SvZo' | docker secret create secret_key -
printf 'HS256'                                       | docker secret create algorithm -

# --- Celery / Redis (service name "redis" as the host) ---
printf 'redis://redis:6379/0' | docker secret create celery_broker_url -
printf 'redis://redis:6379/1' | docker secret create celery_result_backend -

# --- Gunicorn ---
printf '2' | docker secret create gunicorn_workers -

# --- PostgreSQL container credentials (must match the URLs above) ---
printf 'postgres'      | docker secret create postgres_user -
printf 'CHANGE_ME'     | docker secret create postgres_password -
printf 'fastapi_ecom'  | docker secret create postgres_db -
```

> Use `printf` (not `echo`) so no trailing newline is stored in the secret.
> Verify them with `docker secret ls` — you should see all 10.

**To change a secret later**, you must remove and recreate it (secrets are
immutable), then redeploy:

```bash
docker secret rm secret_key
printf 'NEW_VALUE' | docker secret create secret_key -
# then push to main again, or re-run the CD workflow manually
```

### Step 3 — Install the GitHub Actions self-hosted runner

The CD workflow runs on a runner installed on this server (label: `self-hosted`).

1. In your browser open:
   **GitHub repo → Settings → Actions → Runners → New self-hosted runner → Linux.**
2. GitHub shows you a set of commands with a one-time token. Run them on the
   server as a **non-root user that is in the `docker` group** (so the runner can
   build images and talk to the Swarm). It looks like this:

   ```bash
   mkdir actions-runner && cd actions-runner
   curl -o actions-runner-linux-x64.tar.gz -L \
     https://github.com/actions/runner/releases/download/<VERSION>/actions-runner-linux-x64-<VERSION>.tar.gz
   tar xzf ./actions-runner-linux-x64.tar.gz
   ./config.sh --url https://github.com/dilmurod2006/Kiyim-Kechal-Backend --token <TOKEN_FROM_GITHUB>
   ```

   When `config.sh` asks for labels, accept the default `self-hosted` (the CD
   workflow targets that label).

3. Install it as a background service so it survives reboots:

   ```bash
   sudo ./svc.sh install
   sudo ./svc.sh start
   sudo ./svc.sh status   # should say "active (running)"
   ```

   Confirm the runner shows as **Idle** in GitHub → Settings → Actions → Runners.

> Make sure the runner's user can run docker without sudo:
> `sudo usermod -aG docker $USER` then log out/in (or restart the runner service).

### Step 4 — Open the firewall port (if using UFW)

```bash
sudo ufw allow 8000/tcp   # FastAPI
sudo ufw allow 22/tcp     # SSH (don't lock yourself out)
sudo ufw enable
```

---

## First deployment

Everything is ready. Trigger the first deploy in either way:

- **Push any change** to `main`, **or**
- In GitHub → **Actions → "CD - Deploy to Swarm" → Run workflow**.

Watch it in the Actions tab. When it finishes, check the server:

```bash
docker stack services kiyim          # all replicas should read 1/1 (or 2/2)
curl http://localhost:8000/          # {"message":"Welcome to the E-commerce API!"}
```

From your machine: `http://<SERVER_IP>:8000/`.

---

## Day-to-day: how a deploy works

1. You push to `main`.
2. **CI** (`ci.yml`) runs on GitHub's runners: lint, build the prod image, boot it
   and hit `/`. A broken build never reaches the server.
3. **CD** (`cd.yml`) runs on your server's runner: builds
   `fastapi-ecom-backend:<commit-sha>` + `:latest`, then `docker stack deploy`.
4. Swarm performs a **rolling update** (`order: start-first`) — the new container
   starts and only then the old one stops, so there is no downtime. If the new
   container fails, Swarm **rolls back automatically** (`failure_action: rollback`).

Database migrations run automatically via the `migrate` service
(`alembic upgrade head`) each deploy.

---

## Useful commands on the server

```bash
docker stack services kiyim                 # status of every service
docker service logs -f kiyim_backend        # live API logs
docker service logs -f kiyim_worker         # live Celery worker logs
docker service ps kiyim_backend --no-trunc  # task history / why a task failed
docker stack ps kiyim                        # all tasks in the stack
```

### Manual rollback to the previous version

```bash
docker service rollback kiyim_backend
docker service rollback kiyim_worker
```

### Remove the whole stack (does not delete the data volumes)

```bash
docker stack rm kiyim
```

---

## Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| CD job fails: *"Docker Swarm is not active"* | Run `docker swarm init` on the server (Step 1). |
| CD job fails: *"Missing Docker secrets"* | Create the missing secrets from Step 2; the job prints the names. |
| Job stays *queued* forever | Self-hosted runner is offline. `sudo ./svc.sh status` in the runner folder. |
| `permission denied` talking to docker | Runner's user isn't in the `docker` group. Add it, restart the runner. |
| `backend` task keeps restarting | `docker service ps kiyim_backend --no-trunc` then `docker service logs kiyim_backend`. Usually a wrong DB secret or DB not ready. |
| Can't reach port 8000 from outside | Open the firewall (Step 4) and the cloud provider's security group. |

---

## Notes on what changed for production

- `compose.prod.swarm.yaml` images are now tagged `${IMAGE_TAG:-latest}` so each
  deploy ships a uniquely tagged image and Swarm can roll back to the previous one.
- The `./:/app` bind mounts were removed from the prod Swarm services: containers
  now run the code baked into the image (correct for production), not a host folder.
- `Dockerfile.prod` now has a real default `CMD` (it was empty).
- `.gitignore` / `.dockerignore` added so `.env` files and caches never get
  committed or shipped inside the image.
