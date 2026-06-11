# Deployment — CI/CD to AWS EC2 (GitHub Actions + SSH)

Every push to `main` runs the tests (CI) and then automatically deploys to your
EC2 server over SSH (CD). You never deploy by hand again.

```
git push origin main
        │
        ▼
GitHub Actions
   ├─ CI  (ci.yml)  → ruff lint + build prod image + smoke test
   └─ CD  (cd.yml)  → runs only if CI passed
                         │  SSH into EC2
                         ▼
              git pull  →  docker compose -f compose.prod.yaml up -d --build
                         │
                         ▼
              migrate (alembic + seed) → backend + worker restart
```

Only port **8000** (the API) is exposed. Postgres and Redis stay private on the
Docker network.

---

## One-time setup

### 1. Push the project to GitHub

```bash
git remote add origin git@github.com:<you>/<repo>.git
git push -u origin main
```

### 2. Prepare the EC2 server (once)

SSH in and install Docker + the Compose plugin, then clone the repo.

```bash
ssh -i your-key.pem ec2-user@<EC2_PUBLIC_IP>

# Amazon Linux 2023 / 2:
sudo yum update -y
sudo yum install -y docker git
sudo systemctl enable --now docker
sudo usermod -aG docker $USER          # log out & back in after this

# Docker Compose plugin:
sudo mkdir -p /usr/libexec/docker/cli-plugins
sudo curl -SL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 \
  -o /usr/libexec/docker/cli-plugins/docker-compose
sudo chmod +x /usr/libexec/docker/cli-plugins/docker-compose

# (Ubuntu AMI instead? use: sudo apt-get update && sudo apt-get install -y docker.io docker-compose-v2 git)

# Clone the repo into your home directory:
git clone https://github.com/<you>/<repo>.git ~/Kiyim-Kechal-Backend
cd ~/Kiyim-Kechal-Backend
```

### 3. Create the production env file ON THE SERVER

```bash
cp .env.prod.example .env.prod
nano .env.prod        # set a strong POSTGRES_PASSWORD, SECRET_KEY, etc.
```

> `.env.prod` is gitignored — it lives only on the server, never in the repo.
> Generate a secret with: `openssl rand -base64 32`

### 4. First manual boot (verify it works)

```bash
docker compose -f compose.prod.yaml up -d --build
docker compose -f compose.prod.yaml ps
curl http://localhost:8000/        # {"message":"Welcome to the E-commerce API!"}
```

### 5. Open port 8000 in the EC2 Security Group

In the AWS console → EC2 → Security Groups → inbound rules, add:

- **Custom TCP · port 8000 · source 0.0.0.0/0** (the API)
- Keep **SSH · port 22** limited to your own IP.

Now the API is reachable at `http://<EC2_PUBLIC_IP>:8000`.

### 6. Add GitHub Actions secrets

In GitHub → repo → **Settings → Secrets and variables → Actions → New repository secret**:

| Secret name     | Value                                                            |
|-----------------|-----------------------------------------------------------------|
| `EC2_HOST`      | Your EC2 public IP or DNS                                        |
| `EC2_USER`      | `ec2-user` (Amazon Linux) or `ubuntu` (Ubuntu)                  |
| `EC2_SSH_KEY`   | The **private** key (full contents of your `.pem` file)         |
| `EC2_APP_DIR`   | *(optional)* path to the repo, default `~/Kiyim-Kechal-Backend` |
| `EC2_SSH_PORT`  | *(optional)* only if you changed SSH from 22                     |

That's it. From now on:

```bash
git push origin main      # → CI runs → on success, auto-deploys to EC2
```

You can also trigger a deploy manually from the **Actions** tab → *CD - Deploy to EC2* → *Run workflow*.

---

## Connecting the frontend

The frontend reads the API base URL from `VITE_API_URL`. Point it at your server:

```bash
# in the frontend project, .env
VITE_API_URL=http://<EC2_PUBLIC_IP>:8000
```

Also update the backend CORS origins in `main.py` if you host the frontend
somewhere other than `localhost:5173`.

---

## Useful commands on the server

```bash
docker compose -f compose.prod.yaml logs -f backend    # tail API logs
docker compose -f compose.prod.yaml ps                 # service status
docker compose -f compose.prod.yaml restart backend    # restart API
docker compose -f compose.prod.yaml down               # stop everything
```

## How seeding behaves in production

The `migrate` service runs `alembic upgrade head` then `python seed.py`. Seeding
is idempotent — existing users/categories/products are skipped, and product
images are refreshed. The default admin/user accounts (see README) are created
on first deploy. **Change those passwords for a real production site.**

---

> Note: the older Docker Swarm files (`compose.prod.swarm.yaml`) are left in the
> repo for reference but are not used by this single-server EC2 pipeline.
