# Vulnerability Management System

A modern platform for managing and analyzing vulnerability data collected from Microsoft Defender.

## Key Features

- 🎨 **Modern UI** – Apple Liquid Glass inspired visuals with fluid interactions.
- 📊 **Rich Visualizations** – Multiple dashboards and charts for instant situational awareness.
- 🔍 **Powerful Filtering** – Combine multiple fields and ranges (CVE, device, CVSS, status, etc.).
- 💬 **AI Copilot** – Built-in assistant to reason about vulnerability data.
- 📱 **Responsive Layout** – Optimized for desktop, tablet, and mobile.
- ⚡ **High Performance** – Stable pagination and filtering on 200k+ records.

## Project Structure

```
VulnManagement/
├── defender.py           # Microsoft Defender synchronization script
├── app.py                # Flask backend entry point
├── servicenow_client.py  # ServiceNow API client
├── frontend/             # React application
│   ├── src/              # Source code
│   ├── dist/             # Production build output
│   └── package.json      # Frontend dependencies
├── requirements.txt      # Python dependencies
└── README.md             # Documentation (Chinese)
```

## Installation

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment variables

Copy `.env.example` to `.env` (local) or `.env.prod` (server) and fill in real secrets. Generate a new `INTEGRATIONS_SECRET_KEY` with:

```bash
python - <<'PY'
import os, base64
print(base64.urlsafe_b64encode(os.urandom(32)).decode())
PY
```

Minimum variables required:

```env
# Microsoft Defender API
TENANT_ID=your_tenant_id
APP_ID=your_app_id
APP_SECRET=your_app_secret
REGION_ENDPOINT=api.securitycenter.microsoft.com
APP_DOMAIN=your.domain.com

# MySQL
DB_HOST=localhost
DB_PORT=3306
DB_NAME=your_database
DB_USER=your_db_user
DB_PASSWORD=your_db_password

# Traefik / certificates
TRAEFIK_ACME_EMAIL=admin@example.com
```

### 3. Initialize the database

```bash
python3 defender.py
```

This will:
- Create the required tables.
- Download machine-level vulnerabilities and the vulnerability catalog from Microsoft Defender.
- Persist everything into MySQL.

APIs in use:
1. `/api/machines/SoftwareVulnerabilitiesByMachine` – incremental device-level sync.
2. `/api/vulnerabilities` – catalog-only, full sync (requires authentication).

### 4. Build the frontend (production)

```bash
cd frontend
npm install
npm run build
cd ..
```

### 5. Run the Flask server

```bash
python3 app.py
```

The backend serves traffic on `http://localhost:5001`.

**Dev mode tips**
- `python3 app.py` for the backend (port 5001)
- `cd frontend && npm run dev` for the Vite dev server (port 3000)

## Usage Guide

### Data synchronization

Run `defender.py` on a schedule:

```bash
python3 defender.py
```

The job automatically:
- Performs a full sync every 7 days if needed.
- Runs incremental machine syncs in between.
- Always re-syncs the catalog (no incremental endpoint exists).
- Stores snapshots for machines and catalog data.

### Web UI

1. **Vulnerability table** – pageable list (25/50/100/200 per page) with detail dialogs.
2. **Filtering** – CVE, device, severity, status, CVSS range, exploitability, OS platform, etc.
3. **Charts** – auto-refreshing distributions by severity, status, platform, vendor, exploitability.
4. **AI assistant** – chat column on the right for natural language questions about your dataset.

## Docker Migration & Deployment

Use Docker + Compose to ship code and data to an Ubuntu VM.

1. **Build images** – ensure `.env` is ready, then run `docker compose build`. The multi-stage Dockerfile builds React first, then bundles the Flask app.
2. **Export database** – `mysqldump --single-transaction --routines --triggers -h 127.0.0.1 -P 3308 -u root -p vulndb > dump.sql` (adjust host/port/user as needed).
3. **Push code** – commit and push everything except secrets / dumps to GitHub. The VM will `git pull` from there.
4. **Prepare the server** – install Docker Engine + Compose, copy `.env.prod` to the repo root, and transfer `dump.sql` (via SCP, offline media, etc.).
5. **Start services** – run `docker compose --env-file .env.prod up -d --build`. Traefik will request certificates for `APP_DOMAIN` (e.g., `ati.victrex.link`) and route requests hitting `https://APP_DOMAIN/vulnmanagement` to the Flask app. Then import the data: `docker compose exec db mysql -u root -p"$MYSQL_ROOT_PASSWORD" ${DB_NAME} < /backup/dump.sql`.
6. **Sync data** – to pull fresh data immediately: `docker compose --env-file .env.prod run --rm app python defender.py`. Add the same command to cron: `0 */6 * * * cd /opt/vuln && docker compose --env-file .env.prod run --rm app python defender.py`.

> **Security** – run `git rm --cached .env` before pushing. After accidental exposure, rotate Azure AD secrets and database passwords immediately.

## API Reference

### GET /api/vulnerabilities
Retrieve the vulnerability list.

Query params: `page`, `per_page`, `cve_id`, `device_name`, `vulnerability_severity_level`, `status`, `os_platform`, `exploitability_level`, `cvss_min`, `cvss_max`.

Response example:
```json
{
  "data": [...],
  "total": 200000,
  "page": 1,
  "per_page": 50,
  "total_pages": 4000
}
```

### GET /api/statistics
Returns severity/status/platform/vendor/exploitability aggregates.

### GET /api/filter-options
Metadata for all dropdown filters.

### POST /api/chat
Chat endpoint for the AI assistant.

```json
{ "message": "Your question" }
```

## Performance Tips

1. **Indexes** – create indexes on all frequently filtered columns (`cve_id`, `device_name`, `vulnerability_severity_level`, etc.).
2. **Pagination** – keep per-page sizes reasonable (50–100 items) to protect DB memory.
3. **TODO** – `/api/vulnerabilities` currently limits catalog sync to 24,000 rows (3 pages * 8,000). Remove this guard once Microsoft exposes a reliable total count / paging API.
4. **Caching** – cache statistics or common filter results in Redis to offload MySQL.
5. **Connection pooling** – adopt a proper connection pool (e.g., `mysql-connector` pooling or SQLAlchemy) for higher concurrency.

## Extensibility

### AI Integrations

Example snippet for OpenAI (replace with the official SDK you use):

```python
import openai

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message', '')

    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=[
            {"role": "system", "content": "You are a vulnerability expert..."},
            {"role": "user", "content": message}
        ]
    )
    return jsonify({
        'message': response.choices[0].message.content
    })
```

### Exporting data

```python
@app.route('/api/export', methods=['GET'])
def export_vulnerabilities():
    # Implement CSV/Excel export logic here
    pass
```

## Database Schema Overview

1. **vulnerability_info** – device-level snapshots from `/api/machines/SoftwareVulnerabilitiesByMachine`.
2. **vulnerability_list** – catalog entries from `/api/vulnerabilities` with CVE, CVSS, EPSS, exploit flags, etc.
3. **vulnerability_snapshots** – aggregated stats for device vulnerabilities.
4. **vulnerability_list_snapshots** – aggregated stats for the catalog (counts, severities, exploit metrics, average EPSS, affected machines).

## Troubleshooting

- **DB connection failures** – verify `.env` settings, ensure MySQL is reachable, and check firewalls.
- **API failures** – confirm Defender credentials, network connectivity, and inspect `defender_api.log`. `/api/vulnerabilities` requires `Vulnerability.Read.All` (Application) or `Vulnerability.Read` (Delegated).
- **Frontend not loading** – ensure Flask is running, check browser dev tools, and confirm static paths.

## License

MIT License.

## Contributions & TODO

Pull requests and issues are welcome!

Open items:
- [ ] TI tab (design, additional data sources besides Recorded Future / inspiration from WIZ).
- [ ] MFA-enabled sign-in flow.
- [ ] Additional charts / visual polish.
