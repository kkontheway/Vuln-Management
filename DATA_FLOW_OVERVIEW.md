# 数据流与威胁情报总览

> 目的：梳理后端数据更新链路、威胁情报处理逻辑、各表之间的交互关系，以及前端依赖的数据入口，便于快速定位“同步后数据没刷新/徽章缺失”等问题。

## 1. 核心数据对象与交互

| 表 / 数据集 | 关键字段 | 写入来源 | 主要消费者 | 备注 |
| --- | --- | --- | --- | --- |
| `vulnerabilities` | `cve_id`, 设备/软件字段, `cvss_score`, `status`, `cve_epss`, `metasploit_detected`, `nuclei_detected`, `recordfuture_detected`, `last_synced` 等 | `app/integrations/defender/repository.save_vulnerabilities`（全量表切换），Threat intel 标记脚本，DuckDB enrichment 脚本（填充 `cve_epss`） | `/api/vulnerabilities`（表格）、`/api/statistics`、`/api/filter-options`、推荐和报表接口 | 同步时整表替换；`cve_epss` 离线更新后直接被列表、统计和 Detail 使用。 |
| `rapid_vulnerabilities` | `cve_id`, `device_count`, `max_severity`, `source_*` 列 | `sync_threat_sources` 中 `_sync_source`（Metasploit 数据） | 计划用于情报面板/重叠统计 | 同步开始前 `TRUNCATE`，再批量插入。 |
| `nuclei_vulnerabilities` | 同上 | 同上（Nuclei GitHub feed） | 同上 | 同上。 |
| `recordfuture_indicators` | `indicator_type` (`ip`/`cve`), `indicator_value`, `metadata` | `recordfuture_service.save_indicators`（来自 `IPExtractBox` 或脚本） | `recordfuture_service._apply_recordfuture_detection_flags`（根据 `cve` 反写主表） | 只存原始指标，不直接驱动前端 UI。 |
| `sync_state` | `last_sync_time`, `sync_type`, `records_count` | `update_sync_time`（每次主同步） | `/api/sync-status`, Header Sync 面板 | 仅记录最后一次全量同步概况。 |
| `vulnerability_snapshots` / `cve_device_snapshots` | 快照统计、每次快照的 CVE-设备明细 | `record_snapshot`（主同步后立即执行） | Dashboard 趋势卡片、未来的修复对比 | 快照生成依赖主表最新数据。 |
| `sync_sources registry` | `key`, `name`, `description`, `default_enabled`, `order` | `app/services/sync_sources/registry.py`（声明各同步模块与 runner） | Header Sync 弹窗、`/api/sync-sources`、`sync_service` orchestrator | 新增数据源只需注册 runner + 文案，前端勾选直接驱动对应模块。 |
| 统计缓存 (`stats:overview`) | Chart 数据 | `vulnerability_service.get_statistics`（缓存 300 秒） | Dashboard、Header | 同步完成后若未手动清缓存，会等待 TTL 过期才刷新。 |

### 数据关系（ASCII 略图）
```
                +--> vulnerabilities  --> /api/vulnerabilities --> 前端表格
                |                     \-> statistics cache    --> Dashboard
Defender API ---+                     \-> snapshots          --> 趋势/报告
DuckDB EPSS -----^
Sync Modal (/api/sync-sources)
        |
        v
sync_service orchestrator --> [defender_vulnerabilities] --> vulnerabilities/snapshots/sync_state
                           -> [epss_enrichment]        --> vulnerabilities.cve_epss
                           -> [threat_feeds]           --> rapid/nuclei tables & detection flags
                           -> [recordfuture_flags]     --> recordfuture_detected 布尔列
Rapid7/Nuclei feeds ----------------------------------------------^
RecordFuture 工具 --> recordfuture_indicators ---------------------+
```

## 2. 数据更新链路

### 2.1 Orchestrator 式同步（多数据源）
1. **触发**：Header Sync 按钮弹出数据源多选弹窗（`/api/sync-sources` 提供列表），确认后调用 `apiService.triggerSync(selectedKeys)` → `/api/sync`。
2. ** orchestrator 流程**（`app/services/sync_service.py`）：
   - 根据用户勾选过滤 registry，保持既定顺序（默认勾选 `defender_vulnerabilities`、`epss_enrichment`、`threat_feeds`、`recordfuture_flags`）。
   - 每个 runner 只负责“同步”自身数据，`sync_progress.sources` 记录 `pending/running/success/error`，任意 runner 失败都会中止后续步骤。
3. **核心 runner（当前版本）**：
   - `defender_vulnerabilities`: `perform_full_sync`，写 `vulnerabilities`、`sync_state`、`vulnerability_snapshots`。
   - `epss_enrichment`: 下载官方 CSV.gz，使用 DuckDB 清洗到临时文件并批量更新 `vulnerabilities.cve_epss`。
   - `threat_feeds`: 调 `sync_threat_sources`，刷新 `rapid_vulnerabilities`/`nuclei_vulnerabilities` 与布尔标记。
   - `recordfuture_flags`: 调 `rebuild_detection_flags`，根据 `recordfuture_indicators` 清零并重建 `recordfuture_detected`。
4. **未纳入 orchestrator 的内容**：RecordFuture 指标录入、ServiceNow/AI 功能、`stats:overview` 缓存（仍需 TTL 或手动清理）。

### 2.2 Threat Intel Feed 刷新（Rapid/Nuclei）
- **触发**：当用户在 Sync 弹窗中勾选 `threat_feeds` 时，orchestrator 会在 Defender runner 之后执行 `sync_threat_sources()`。
- **数据源**：
  - Rapid7 Metasploit: `modules_metadata_base.json`（GitHub master）。
  - ProjectDiscovery Nuclei: `cves.json`（JSON Lines）。
- **处理流程**（`app/services/threat_source_sync_service.py`）：
  1. 下载并解析 feed，提取 `cve_id`、标题、描述、CVSS 等 metadata。
  2. `_fetch_local_stats` 只查询当前 `vulnerabilities` 内存在的 CVE，统计设备数、最近 `last_seen`、最大严重度。
  3. `_truncate_table` → `_bulk_insert` 将匹配项写到 `rapid_vulnerabilities`/`nuclei_vulnerabilities`。
  4. `_reset_detection_flag` 全表清零对应布尔列，再 `_apply_detection_flag` 按批次把命中 CVE 设置为 `TRUE`。
- **前端影响**：`VulnerabilityTable` Threat Intel 列、`statistics` 中的 feed 重叠数据使用 `metasploit_detected`/`nuclei_detected`。

### 2.3 RecordFuture 指标写入
- **入口**：`Tools` → `IPExtractBox`，或任意调用 `/api/threat-intelligence/extract-ip` + `/api/threat-intelligence/recordfuture/save`。
- **流程**：
  1. `extract_ip_addresses`（`app/services/threat_intelligence_service.py`）从自由文本提取 IPv4 & CVE，供用户确认。
  2. `save_recordfuture_indicators` → `recordfuture_service.save_indicators`：
     - 入库到 `recordfuture_indicators`（若冲突则 upsert），类型区分 `ip`/`cve`。
     - 针对本次传入的 `cves` 执行 `_apply_recordfuture_detection_flags`：按 500 条一批把 `vulnerabilities` 中对应 `cve_id` 设为 `recordfuture_detected = TRUE`。
- **注意**：
  - 仅“这次”传入的 CVE 会被标记；老数据需要手工重放（示例脚本见我们刚执行的 `python` 片段），或等待下一次 Sync 勾选 `recordfuture_flags` 时自动重放。
  - 自动阶段会先清零，再根据 `recordfuture_indicators` 中的所有 `cve` 重新打标；若需撤销仍需人工 `UPDATE ... SET recordfuture_detected = FALSE`。

### 2.4 统计与缓存
- `vulnerability_service.get_statistics` 会汇总多个仓储函数（严重度、平台、厂商、exploitability、年龄、Autopatch、RSS、threat feed 重叠、EPSS bucket、新增 7 天）并写入 Redis 缓存 `stats:overview`，TTL 300 秒。同步完成后如需立即刷新 Dashboard，可清缓存或在后台调用 `cache_set` 逻辑。

### 2.5 Sync 进度
- `sync_service` 在内存/Redis 保存 `sync_progress`，前端轮询 `/api/sync-progress` 每 2 秒更新。若线程异常结束，会把状态切到 `error`。

## 3. 前端数据消费一览

| 页面 / 组件 | 依赖 API | 主要数据 | 说明 |
| --- | --- | --- | --- |
| `components/Header/Header` | `getUniqueCveCount`, `getSeverityCounts`, `getSyncStatus`, `getSyncProgress`, `triggerSync`, `createInitialSnapshot` | 总体统计、同步状态 | Sync 按钮所在，负责轮询后台进度。 |
| `pages/Dashboard`（及其 `EpssAnalyticsSection`, `VulnerabilityTrendCard`, `BarChart` 等） | `getStatistics`, `getSnapshotsTrend`, `getFixedVulnerabilities` | 图表、趋势、已修复列表 | 依赖缓存的 `statistics`，同步后短时间内仍可能展示旧数据。 |
| `pages/Vulnerabilities` → `FilterPanel` | `getFilterOptions` | 枚举 `severity/status/os_platform/software_vendor` | Threat Intel 多选通过 `threat_intel` query 参数传递至后端。 |
| `pages/Vulnerabilities` → `VulnerabilityTable` | `getVulnerabilities` | 分页表格，包含 `metasploit_detected/nuclei_detected/recordfuture_detected` | Threat Intel 栏根据布尔列渲染徽章；重新加载表格即可反映标记。 |
| `VulnerabilityDetailDialog` | `getVulnerabilityCatalogEntry` | 聚合后的 CVSS/EPSS、Affected Devices | 明细弹窗直接读取 `vulnerabilities`（含 `cve_epss`），暂不展示 Defender Catalog 描述。 |
| `pages/Tools` → `IPExtractBox` | `extractIPAddresses`, `saveRecordFutureIndicators` | RecordFuture 指标 | 直接驱动 `recordfuture_indicators` 和主表标记。 |
| `pages/Tools` → `RecommendationGenerator`、`pages/ReportView` | `checkRecommendationReport`, `generateRecommendationReport`, `getRecommendationHistory`, `getRecommendationReport`, `getRecommendationReportByCVE`, `getCVEVulnerabilityData` | AI 推荐报告、关联设备 | 与威胁情报无关，但共享漏洞基础表。 |
| `pages/ServiceNow` / `ServiceNowConfig` | ServiceNow 相关 API | 工单、配置 | 不受 Defender 同步影响。 |
| `pages/AIChat`, `components/ChatBox/ChatBox`, `pages/ChatConfig` | `/api/chat`, `/integrations/settings` | AI 对话、配置 | 独立功能。 |
| `pages/ThreatIntelligence` → `ThreatFilterPanel` / `ThreatTable` | **目前使用 `mockThreats` 静态数据** | - | 暂未对接后台情报 API，因此不会显示真实数据。 |

> 若需追踪更多组件，可搜索 `apiService` 引用；当前项目所有取数点均集中在上表列出的页面/工具中。

## 4. 按钮触发场景：一次 Sync 会发生什么？

1. **用户点击 Header 的 Sync** → 弹窗列出 registry 中的同步源（复选框 + 描述）。提交后 `/api/sync` 将所选 key 传给 orchestrator。
2. **阶段/进度展示**：
   - `sync_progress.sources` 会列出每个 runner 的实时状态（Pending → Running → Success/Error），Header 右上角同步显示。
   - 默认顺序：`defender_vulnerabilities` → `epss_enrichment` → `threat_feeds` → `recordfuture_flags`，可按需勾选。
3. **自动更新的内容**：取决于所选模块。例如：
   - 仅勾选 `defender_vulnerabilities`：刷新 `vulnerabilities`、`sync_state`、`vulnerability_snapshots`。
   - 勾选 `epss_enrichment`：下载最新 EPSS CSV.gz，DuckDB 清洗后批量更新 `vulnerabilities.cve_epss`。
   - 勾选 `threat_feeds`：额外刷新 `rapid_vulnerabilities`/`nuclei_vulnerabilities` 与 `metasploit_detected`/`nuclei_detected`。
   - 勾选 `recordfuture_flags`：重放 `recordfuture_detected`。
4. **不会自动更新的内容**：
   - `recordfuture_indicators`（仍需 Tools/脚本新增指标）。
   - ServiceNow/AI/Recommendation 相关数据。
   - Redis 缓存（如 `stats:overview`）；需要等待 TTL 或手动清理。
   - 前端本地状态：`VulnerabilityTable` 需重新进入或切换过滤条件才会重新请求。
5. **潜在影响**：若下载 Rapid7/Nuclei feed 或 EPSS CSV 失败，orchestrator 会在该阶段停止并标记 error；检查网络/日志后可重新只勾选失败的 runner。

## 5. 快速定位 RecordFuture 徽章缺失

1. **确认标记**：在数据库执行 `SELECT cve_id FROM vulnerabilities WHERE recordfuture_detected = TRUE LIMIT 10;`。若为空，说明标记没打上。
2. **重放指标**：运行脚本 `python - <<'PY' ... _apply_recordfuture_detection_flags(...)`（示例见 `app/services/recordfuture_service.py`）即可把 `recordfuture_indicators` 中现有的 CVE 批量回写。
3. **前端刷新**：`VulnerabilityTable` 只要重新发起 `getVulnerabilities` 请求，就会看到 RecordFuture 徽章；Threat Filter 的 `Threat Intel` 多选会把 `threat_intel=recordfuture` 作为查询条件，映射到 `recordfuture_detected = TRUE`（`app/repositories/query_builder.py`）。
4. **区别**：RecordFuture 不依赖 Rapid/Nuclei 的 GitHub 下载；仍需通过 Tools 或脚本显式写入指标，但主 Sync 的 `recordfuture` 阶段会基于这些指标自动重放布尔标记。

---
如需在同步完成后强制刷新 Dashboard，可考虑：
- 在 `sync_service` 完成时清除 `stats:overview` 缓存；
- 或前端在 `syncProgress` 变成 complete 后重新调用 `getStatistics()`。
