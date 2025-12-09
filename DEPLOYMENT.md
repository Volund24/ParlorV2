# Deployment Guide for The Backroom Parlor

This guide explains how to deploy the bot on a Linode VPS (or any Docker-enabled server).

## Prerequisites

- A Linode VPS (Ubuntu 22.04 recommended)
- Docker and Docker Compose installed on the server
- A Discord Bot Token
- API Keys (NVIDIA, Gemini, Supermachine)

## 1. Prepare the Server

SSH into your Linode server:
```bash
ssh root@your-linode-ip
```

Install Docker & Docker Compose (if not already installed):
```bash
apt update
apt install -y docker.io docker-compose
```

## 2. Setup the Project

Clone the repository or copy the files to your server.
```bash
git clone <your-repo-url> parlor-bot
cd parlor-bot
```

## 3. Configuration

Create the `.env` file from the example:
```bash
cp .env.example .env
```

Edit the `.env` file with your actual keys:
```bash
nano .env
```

**Important:**
- Set `WEBHOOK_URL` to your server's public IP or domain.
  - Example: `WEBHOOK_URL=http://<your-linode-ip>:3000`
  - Or if using a domain: `WEBHOOK_URL=https://your-domain.com/webhook` (requires reverse proxy setup)
- Ensure `DATABASE_URL` is set to `sqlite:////app/data/backroom_parlor.db` (this is the default in Dockerfile, but good to be explicit).

## 4. Networking & Firewall (Crucial Step)

For the `WEBHOOK_URL` to work, the internet must be able to reach port `3000` on your server.

**If using UFW (Uncomplicated Firewall) on Ubuntu:**
```bash
ufw allow 3000/tcp
ufw reload
```

**If using Linode Cloud Firewall:**
1. Go to your Linode Dashboard > Firewalls.
2. Edit the Inbound Rules.
3. Add a rule:
   - **Type:** Custom TCP
   - **Port:** 3000
   - **Action:** Accept
   - **Source:** All IPv4 / All IPv6

**Constructing your URL:**
If your Linode IP is `192.0.2.123`, your webhook URL is:
`http://192.0.2.123:3000`

Update your `.env` file:
```bash
WEBHOOK_URL=http://192.0.2.123:3000
```

## 5. Run with Docker Compose

Build and start the container:
```bash
docker-compose up -d --build
```

Check logs to ensure it's running:
```bash
docker-compose logs -f
```

## 5. Data Persistence

The database is stored in the `./data` directory on the host machine (mapped to `/app/data` in the container). This ensures your user data and battle history are preserved even if you restart the container.

## 7. Updating the Bot

To update the bot after pushing changes to git:

```bash
git pull
docker-compose up -d --build
```

## 8. Verification

After starting the container, verify that the webhook is accessible from the outside world.

Open your browser or use `curl` on your local machine:
```bash
curl http://<your-linode-ip>:3000/ping
```
You should see: `Pong! Tunnel is active.` (Note: The message says "Tunnel" but it applies to the direct connection too).

## Troubleshooting

- **Webhook Issues:** If Supermachine images aren't returning, check that port 3000 is open on your firewall (`ufw allow 3000`).
- **Database Issues:** Check permissions on the `./data` folder. Docker usually handles this, but ensure the user has write access.
