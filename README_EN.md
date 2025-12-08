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

## Installation (Step by Step)

### 1. Run MySQL 8.0 with Docker
```bash
docker run -d \
  --name mysql-db \
  -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=change-this-root-password \
  -e MYSQL_DATABASE=vulndb \
  -e MYSQL_USER=vuln_app \
  -e MYSQL_PASSWORD=vuln_app_password \
  mysql:8.0 \
  --character-set-server=utf8mb4 \
  --collation-server=utf8mb4_unicode_ci
```
- Keep `MYSQL_DATABASE/USER/PASSWORD` in sync with `.env`.
- Validate with `mysql -h127.0.0.1 -P3306 -uroot -p` and `docker logs mysql-db`.

### 2. Import the legacy dump (`dump.sql`)
```bash
# Upload the dump (example)
scp dump.sql user@server:/opt/vuln/dump.sql

# Pipe it into the container
cat /opt/vuln/dump.sql | docker exec -i mysql-db \
  mysql -uroot -p"$MYSQL_ROOT_PASSWORD" vulndb
```
- When the dump already contains `CREATE DATABASE`, recreate the schema first: `docker exec -it mysql-db mysql -uroot -p -e "DROP DATABASE IF EXISTS vulndb; CREATE DATABASE vulndb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"`.
- Verify the import with `mysql -h127.0.0.1 -P3306 -uvuln_app -p vulndb -e "SHOW TABLES;"`.

### 3. Configure environment variables
- Local: `cp .env.example .env`
- Server: `cp .env.example .env.prod`
- Minimum keys:
```env
TENANT_ID=your-tenant-id
APP_ID=your-app-id
APP_SECRET=your-app-secret
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=vulndb
DB_USER=vuln_app
DB_PASSWORD=vuln_app_password
MYSQL_ROOT_PASSWORD=change-this-root-password
SECRET_KEY=change-this-secret
INTEGRATIONS_SECRET_KEY=base64-url-safe-32-byte-key
```
> `config.py` loads these automatically and `initialize_app_database()` runs migrations on startup.

### 4. Prepare and run the Flask backend
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py  # foreground test
nohup python app.py > backend.log 2>&1 &  # keep running
```
- API base URL: `http://127.0.0.1:5001/api/...`
- Inspect `tail -f backend.log` or `lsof -i :5001` for health checks.

### 5. Build the React frontend
```bash
cd frontend
npm install  # first time
npm run build
```
- Output lives in `frontend/dist`; Flask serves it automatically.
- Or sync to `/var/www/vuln-frontend/` for Nginx-only hosting.

### 6. Configure Nginx (port 80 entry point)
```
server {
    listen 80;
    server_name your_domain.com;

    root /var/www/vuln-frontend;  # or the repo's frontend/dist path
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```
- `sudo nginx -t && sudo systemctl reload nginx`
- Validate with `curl http://your_domain/api/vulnerabilities`.

### 7. (Optional) Sync Microsoft Defender data
```bash
source .venv/bin/activate
python defender.py
```
- Add `python defender.py` to cron (e.g., `0 */6 * * * /opt/vuln/.venv/bin/python /opt/vuln/defender.py`).

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
