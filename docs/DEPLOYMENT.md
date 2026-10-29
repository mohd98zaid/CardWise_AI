# Deployment and Local Execution

CardWise AI is designed and configured as a privacy-respecting, **local-only application**. It operates entirely on the local loopback interface (`127.0.0.1`) without requiring external cloud databases, distributed caches (Redis), container orchestrators (Kubernetes), or external network connections.

---

## 1. Local Architecture

- **Loopback Binding**: By default, the backend server binds to `127.0.0.1:8000` and the frontend binds to `127.0.0.1:5173`. Neither is exposed to public or local area networks.
- **Embedded Database**: Local SQLite (`sqlite:///./cardwise.db`) is the default and fully supported persistent datastore. PostgreSQL is supported via standard SQLAlchemy/Alembic if local containerization is desired.
- **In-Memory Rate Limiting**: The built-in sliding-window rate limiter runs locally in-process without requiring Redis or distributed cache dependencies.
- **Zero Cloud Dependencies**: Reward calculations, scenario optimization, portfolio management, and rule evaluation run deterministically on the host machine.

---

## 2. Running Locally

### Direct Host Process

```bash
# 1. Backend
cd backend
python -m pip install -e ".[dev]"
python -m alembic upgrade head
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 2. Frontend (in another terminal)
cd frontend
npm install
npm run dev
```

### Local Docker Compose

Docker Compose port mappings are explicitly bound to the local loopback interface (`127.0.0.1`):

```bash
docker compose up --build
```

---

## 3. Optional LAN Access Configuration & Security Implications

If you explicitly choose to make CardWise accessible across other devices on your home or office local network (e.g. accessing from a mobile browser on the same Wi-Fi):

### Configuration Steps

1. **Backend Host & CORS**:
   ```bash
   HOST=0.0.0.0
   ALLOWED_ORIGINS="http://127.0.0.1:5173,http://localhost:5173,http://<YOUR-LAN-IP>:5173"
   ```
2. **Frontend Target**:
   ```bash
   VITE_API_BASE_URL="http://<YOUR-LAN-IP>:8000"
   ```
3. In `frontend/vite.config.ts`, adjust `server.host: "0.0.0.0"`.

### Security Implications

> [!WARNING]
> Exposing CardWise beyond `127.0.0.1` introduces specific security considerations:
> - **Unencrypted Network Traffic**: HTTP traffic over local Wi-Fi exposes session tokens and financial scenario data in cleartext to network sniffers on the same subnet.
> - **Untrusted Network Neighbors**: Any device on the same local subnet (smart TVs, IoT devices, guest network users) can send requests to your local backend API.
> - **Credential Transmission**: Account logins and session tokens will travel without TLS encryption unless a local reverse proxy with self-signed or internal CA certificates (such as Caddy or mkcert) is deployed.
> - **Firewall Exposure**: Ensure your host operating system firewall does not forward these ports to the public internet or external WAN gateways.

---

## 4. Database Migrations

CardWise AI uses Alembic to manage database schema migrations.

```bash
# Apply migrations to head
cd backend
python -m alembic upgrade head

# Check current migration revision
python -m alembic current
```

Migrations support both clean initialization on fresh SQLite/PostgreSQL instances and incremental upgrades from prior revisions.
