# Filter Architecture

```
FilterPanel (React UI) ──serializeFilters()──▶ /api/vulnerabilities
        │                                        │
        │                                 build_vulnerability_filters()
        ▼                                        ▼
frontend/src/config/filterSchema.ts      app/services/filter_registry.py
```

## Frontend Schema
- File: `frontend/src/config/filterSchema.ts`
- `FilterState` holds UI-friendly keys (e.g., `severity`, `platform`, `epssBucket`).
- `serializeFilters` converts the state into `VulnerabilityFilters` payloads that match the API (e.g., `vulnerability_severity_level`, `os_platform`, `epss_min`, `epss_max`, `cve_public_exploit`).
- `EPSS_BUCKET_RANGES` defines the numeric ranges for each EPSS bucket so buckets and min/max ranges stay in sync.
- `createDefaultFilterState()` centralises defaults for “Clear filters”.  Any new filter only needs to be added to this module for the component to pick it up.

## Backend Registry
- File: `app/services/filter_registry.py`
- `FILTER_FIELD_DEFINITIONS` declares every column, strategy (`contains`, `equals`, `boolean`, `in`), and acceptable parameter keys.
- `RANGE_FILTER_DEFINITIONS` / `DATE_FILTER_DEFINITIONS` describe the numeric/date comparisons (`>=`, `<=`).
- `normalize_list` and `parse_boolean` provide consistent parsing of multi-selects and tri-state toggles.
- `app/repositories/query_builder.py` imports these definitions and constructs the SQL WHERE clause via `_build_field_clause`, `_build_range_clause`, and `_build_date_clause`. Adding a new filter is typically just editing the registry file.

## Adding a New Filter
1. **UI / Schema**
   - Update `FilterState` and `createDefaultFilterState` with the new key.
   - Extend `serializeFilters` to map it to the intended API key(s).
   - Render the control in `FilterPanel.tsx` and call `handleFilterChange` with the schema key.
2. **API Payload**
   - Ensure `VulnerabilityFilters` in `frontend/src/types/api.ts` declares the query parameter.
3. **Backend**
   - Register the new parameter in `app/services/filter_registry.py` (choose strategy or range/date definition).
   - If it uses a new database column, confirm the column exists / is indexed.
4. **Verification**
   - Use the browser network tab to verify the query string.
   - Temporarily log the output of `build_vulnerability_filters` to ensure the clause and params are populated as expected.

## Troubleshooting Checklist
1. **No results** – confirm the query param matches the registry key. If not, add a serializer entry or alias.
2. **Filter ignored** – check whether the registry definition exists; missing entries will be silently skipped.
3. **Boolean / tri-state filters** – make sure `parse_boolean` can interpret the value (`true`/`false`/`all`).
4. **Multi-select filters** – `normalize_list` strips empty strings. If you expect multiple values, ensure the UI always sends an array.
5. **EPSS buckets** – all bucket math lives in `filterSchema.ts`. If values change, update the range map once and both UI + API inherit it.

Keeping the schema + registry authoritative means a new filter generally requires editing two files instead of scattering logic through multiple components.
