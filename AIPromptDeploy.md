# AI Server Provisioning Prompt

*This file contains a professional prompt designed to be copied and pasted to another AI (like ChatGPT, Claude, etc.) to help you automatically provision your server for the `FastAPI-E-Commarce` project deployment.*

---

## 📋 Copy the text below and paste it to your AI assistant:

```text
Act as a Senior DevOps and Site Reliability Engineer. I need to provision a fresh Linux server (Ubuntu 22.04 LTS) to host a containerized FastAPI application with a Celery worker, Redis, and PostgreSQL database.

The application uses Docker Swarm for orchestration and GitHub Actions (via a Self-Hosted Runner) for CI/CD auto-deployments. 

Please provide a highly professional, step-by-step guide and an automation bash script to set up my server. The setup must include the following requirements:

### 1. System Updates & Basic Security
- Update and upgrade all system packages.
- Install essential utilities (`curl`, `git`, `ufw`, `apt-transport-https`, `ca-certificates`, `software-properties-common`).
- Configure UFW (Uncomplicated Firewall) to allow:
  - SSH (Port 22)
  - HTTP/HTTPS (Ports 80/443 - if using reverse proxy in the future)
  - FastAPI Application (Port 8000)
  - Enable UFW.

### 2. Docker & Docker Swarm
- Install the latest stable version of Docker Engine, Docker CLI, and containerd from the official Docker repository.
- Ensure Docker starts on boot and add the current user to the `docker` group.
- Initialize Docker Swarm as a manager node (`docker swarm init`).

### 3. GitHub Actions Self-Hosted Runner Preparation
- Create a dedicated user for the GitHub runner (e.g., `github-runner`) and add it to the `docker` group for passwordless docker access.
- Provide instructions on where and how to download the GitHub Actions Runner package from the repository's settings.
- Explain how to install and start the runner as a background systemd service (`sudo ./svc.sh install`, `sudo ./svc.sh start`).

### 4. Best Practices
- Ensure the bash script is idempotent where possible.
- Include comments explaining each critical step in the bash script.

Please output the complete bash script first, followed by clear, step-by-step instructions on how I should execute it and how to link the GitHub runner.
```
