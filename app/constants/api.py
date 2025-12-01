"""API endpoint constants for Microsoft Defender."""

# API base URL
API_BASE_URL_DEFAULT = "https://api.securitycenter.microsoft.com"

# API endpoints
ENDPOINT_SOFTWARE_VULNERABILITIES_BY_MACHINE = "/api/machines/SoftwareVulnerabilitiesByMachine"
ENDPOINT_ADVANCED_QUERIES = "/api/advancedqueries/run"

# OAuth endpoint
OAUTH_TOKEN_ENDPOINT = "https://login.microsoftonline.com/{tenant_id}/oauth2/token"

