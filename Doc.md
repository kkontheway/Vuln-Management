# 漏洞管理系统技术文档

## 1. 系统概述

### 1.1 系统简介
漏洞管理系统是一个现代化的漏洞管理平台，用于管理和分析Microsoft Defender收集的漏洞数据。系统采用前后端分离架构，提供漏洞查询、统计分析、数据同步、快照管理、ServiceNow集成、威胁情报和AI聊天等功能。

### 1.2 技术栈
- **后端**: FastAPI 0.115 + Uvicorn (Python)
- **前端**: React 18.3.1 + TypeScript + Vite
- **数据库**: MySQL 8.0+
- **UI框架**: Tailwind CSS + Radix UI
- **图表库**: Recharts
- **HTTP客户端**: Axios

### 1.3 系统架构
```
┌─────────────┐
│   React     │ 前端应用 (Port 3000/5001)
│  Frontend   │
└──────┬──────┘
       │ HTTP/REST API
┌──────▼──────┐
│  FastAPI    │ 后端API服务器 (Port 5001)
│   Backend   │
└──────┬──────┘
       │
   ┌───┴───┐
   │       │
┌──▼──┐ ┌─▼────┐
│MySQL│ │Defender│ Microsoft Defender API
│     │ │  API   │
└─────┘ └───────┘
```

## 2. 系统架构

### 2.1 目录结构
```
VulnManagement/
├── app/                      # FastAPI应用主目录
│   ├── __init__.py          # FastAPI应用工厂
│   ├── routes/              # API路由模块
│   │   ├── vulnerabilities.py    # 漏洞管理API
│   │   ├── snapshots.py          # 快照管理API
│   │   ├── sync.py               # 数据同步API
│   │   ├── servicenow.py         # ServiceNow集成API
│   │   ├── threat_intelligence.py # 威胁情报API
│   │   ├── chat.py               # AI聊天API
│   │   └── (routers同目录结构)   # FastAPI APIRouter
│   ├── services/            # 业务逻辑服务层
│   │   ├── vulnerability_service.py
│   │   ├── snapshot_service.py
│   │   ├── sync_service.py
│   │   └── threat_intelligence_service.py
│   ├── integrations/        # 第三方集成
│   │   └── defender/        # Microsoft Defender集成
│   │       ├── auth.py            # OAuth认证
│   │       ├── api_client.py      # API客户端
│   │       ├── service.py         # 服务封装
│   │       ├── sync.py            # 同步逻辑
│   │       ├── repository.py      # 数据仓库
│   │       ├── database.py         # 数据库初始化
│   │       └── transformers.py    # 数据转换
│   ├── repositories/        # 数据访问层
│   ├── constants/           # 常量定义
│   └── utils/               # 工具函数
├── frontend/                # React前端应用
│   ├── src/
│   │   ├── pages/           # 页面组件
│   │   ├── components/      # UI组件
│   │   ├── services/        # API服务
│   │   ├── types/           # TypeScript类型定义
│   │   └── styles/          # 样式文件
│   └── package.json
├── app.py                   # FastAPI应用入口（uvicorn封装）
├── config.py                # 配置管理
├── database.py              # 数据库连接
├── servicenow_client.py     # ServiceNow客户端
└── requirements.txt         # Python依赖
```

### 2.2 模块划分
- **路由层 (routes/)**: 处理HTTP请求，参数验证，调用服务层
- **服务层 (services/)**: 业务逻辑处理，数据查询和转换
- **集成层 (integrations/)**: 第三方API集成，数据同步
- **数据访问层 (repositories/)**: 数据库操作封装
- **前端层 (frontend/)**: React组件，UI交互，API调用

## 3. 后端文档

### 3.1 FastAPI应用结构
- **app/__init__.py**: FastAPI应用工厂，注册APIRouter、配置中间件、初始化数据库，并将 `frontend/dist` 挂载为静态资源
- **app.py**: 应用入口，封装 `uvicorn.run`（端口5001）

### 3.2 路由模块 (app/routes/)

#### 3.2.1 vulnerabilities.py - 漏洞管理API
- `GET /api/vulnerabilities`: 获取漏洞列表（支持分页和过滤）
- `GET /api/statistics`: 获取统计信息（严重程度、状态、平台等）
- `GET /api/unique-cve-count`: 获取唯一CVE数量
- `GET /api/severity-counts`: 获取严重程度统计
- `GET /api/filter-options`: 获取过滤器选项
- `GET /api/fixed-vulnerabilities`: 获取已修复漏洞列表

#### 3.2.2 snapshots.py - 快照管理API
- `POST /api/create-initial-snapshot`: 创建初始快照
- `GET /api/snapshots`: 获取快照列表
- `GET /api/snapshots/<id>/details`: 获取快照详情
- `GET /api/cve-history/<cve_id>`: 获取CVE历史记录
- `GET /api/snapshots/trend`: 获取快照趋势数据

#### 3.2.3 sync.py - 数据同步API
- `GET /api/sync-status`: 获取同步状态
- `GET /api/sync-progress`: 获取同步进度
- `POST /api/sync`: 触发数据同步

同步流程结束后会自动触发 Rapid7 Metasploit / ProjectDiscovery Nuclei 数据集同步：
- 后端会从 Github 最新数据源实时下载 `modules_metadata_base.json` 与 `cves.json`，逐条解析 JSON (Rapid7 为模块字典、Nuclei 为 JSON Lines) 并提取 CVE、标题、描述、严重度、CVSS 等信息。
- 仅保留当前环境中实际存在的 CVE，并写入 `rapid_vulnerabilities`、`nuclei_vulnerabilities` 两张表，字段包含 `cve_id`、`device_count`、`max_severity`、`max_cvss`、`last_seen` 以及 `source_title`、`source_description`、`source_severity`、`source_cvss` 等字段，便于展示外部上下文。
- 同步过程中同时刷新 `vulnerabilities` 表中的 `metasploit_detected`、`nuclei_detected` 标记，方便前端展示。
- 下载失败或数据源不可达时会记录日志但不会阻断整个同步。

#### 3.2.4 servicenow.py - ServiceNow集成API
- `GET /api/servicenow/tickets`: 获取工单列表
- `POST /api/servicenow/tickets`: 创建工单
- `GET /api/servicenow/tickets/<id>`: 获取工单详情
- `GET /api/servicenow/tickets/<id>/notes`: 获取工单备注
- `POST /api/servicenow/tickets/<id>/notes`: 添加工单备注
- `POST /api/servicenow/test-connection`: 测试连接

#### 3.2.5 threat_intelligence.py - 威胁情报API
- `POST /api/threat-intelligence/extract-ip`: 从文本中提取IP地址

#### 3.2.6 chat.py - AI聊天API
- `POST /api/chat`: AI聊天接口（待集成AI服务）

### 3.3 服务层 (app/services/)

#### 3.3.1 vulnerability_service.py
- `get_vulnerabilities()`: 获取分页漏洞列表，支持多条件过滤
- `get_statistics()`: 获取统计信息（严重程度、状态、平台、供应商、可利用性、年龄分布等）
- `get_unique_cve_count()`: 获取唯一CVE数量
- `get_severity_counts()`: 获取严重程度统计
- `get_fixed_vulnerabilities()`: 获取已修复漏洞列表
- `get_filter_options()`: 获取过滤器选项

#### 3.3.2 snapshot_service.py
- 快照创建、查询、趋势分析等功能

#### 3.3.3 sync_service.py
- 同步状态查询、进度跟踪、触发同步等功能

#### 3.3.4 threat_intelligence_service.py
- IP地址提取和CSV生成功能

#### 3.3.5 device_tag_service.py
- 维护 `device_tag_rules` 默认规则（如 `panjin`、`victrex`、预留的 `txv`）
- `apply_device_tag_rules()` 会在每次 Defender 全量同步后运行，将匹配结果写入 `vulnerabilities.device_tag` 与 `device_tags` 表
- 暴露统计与选项查询，供 `get_filter_options()` 和 Dashboard 读取

### 3.4 集成模块 (app/integrations/defender/)

#### 3.4.1 auth.py
- `get_access_token()`: 获取Microsoft Defender API访问令牌（OAuth2客户端凭证模式）

#### 3.4.2 api_client.py
- `fetch_device_vulnerabilities()`: 从Defender API获取设备漏洞数据（支持分页）
- `run_advanced_query()`: 执行高级查询

#### 3.4.3 service.py
- `DefenderService`: Defender API服务封装，提供令牌管理和API调用

#### 3.4.4 sync.py
- `sync_device_vulnerabilities_full()`: 全量同步设备漏洞数据

#### 3.4.5 repository.py
- `save_vulnerabilities()`: 保存漏洞数据到数据库（使用临时表切换策略）
- `record_snapshot()`: 记录快照
- `update_sync_time()`: 更新同步时间

#### 3.4.6 database.py
- `create_db_connection()`: 创建数据库连接
- `migrate_database()`: 数据库迁移
- `initialize_database()`: 初始化数据库表结构

#### 3.4.7 transformers.py
- 数据转换和格式化工具

### 3.5 配置管理
- **config.py**: 应用配置（数据库、FastAPI、日志等）
- **app/integrations/defender/config.py**: Defender API配置
- **app/constants/api.py**: API端点常量
- **app/constants/database.py**: 数据库表名常量

## 4. 前端文档

### 4.1 React应用结构
- **入口**: `frontend/src/main.tsx`
- **路由**: `frontend/src/App.tsx` (React Router)
- **构建工具**: Vite

### 4.2 页面组件 (frontend/src/pages/)

#### 4.2.1 Dashboard.tsx
- 仪表板页面，显示漏洞统计概览

#### 4.2.2 Vulnerabilities.tsx
- 漏洞列表页面，支持过滤、分页、详情查看

#### 4.2.3 ThreatIntelligence.tsx
- 威胁情报页面，IP地址提取功能

#### 4.2.4 ServiceNow.tsx
- ServiceNow集成页面，工单管理

#### 4.2.5 ServiceNowConfig.tsx
- ServiceNow配置页面

#### 4.2.6 AIChat.tsx
- AI聊天页面

#### 4.2.7 ChatConfig.tsx
- AI聊天配置页面

### 4.3 UI组件 (frontend/src/components/)

#### 4.3.1 Table/
- **VulnerabilityTable.tsx**: 漏洞表格组件
- **ThreatTable.tsx**: 威胁情报表格组件

#### 4.3.2 Charts/
- **BarChart.tsx**: 柱状图组件
- **LineChart.tsx**: 折线图组件
- **PieChart.tsx**: 饼图组件

#### 4.3.3 FilterPanel/
- **FilterPanel.tsx**: 漏洞过滤面板
- **ThreatFilterPanel.tsx**: 威胁情报过滤面板

#### 4.3.4 ChatBox/
- **ChatBox.tsx**: 聊天框组件
- **IPExtractBox.tsx**: IP提取框组件

#### 4.3.5 Sidebar/
- **Sidebar.tsx**: 侧边栏导航组件

#### 4.3.6 Header/
- **Header.tsx**: 页面头部组件

#### 4.3.7 Cards/
- **StatCard.tsx**: 统计卡片组件

#### 4.3.8 ui/
- Radix UI组件封装（button, card, dialog, input, select, table等）

### 4.4 API服务层 (frontend/src/services/)
- **api.ts**: 统一的API服务封装，使用Axios
  - `getVulnerabilities()`: 获取漏洞列表
  - `getStatistics()`: 获取统计信息
  - `getSnapshots()`: 获取快照列表
  - `triggerSync()`: 触发同步
  - `sendChatMessage()`: 发送聊天消息
  - ServiceNow相关API调用
  - 威胁情报相关API调用

### 4.5 类型定义 (frontend/src/types/)
- **api.ts**: API请求/响应类型定义
  - `Vulnerability`: 漏洞数据类型
  - `StatisticsResponse`: 统计响应类型
  - `Snapshot`: 快照类型
  - `SyncStatus`: 同步状态类型
  - 等
- **servicenow.ts**: ServiceNow相关类型
- **threat.ts**: 威胁情报相关类型

## 5. API文档

### 5.1 漏洞管理API

#### GET /api/vulnerabilities
获取漏洞列表，支持分页和过滤

**查询参数:**
- `page` (int, 默认1): 页码
- `per_page` (int, 默认50): 每页数量
- `cve_id` (string): CVE ID过滤
- `device_name` (string): 设备名称过滤
- `vulnerability_severity_level` (string): 严重程度过滤
- `status` (string): 状态过滤
- `os_platform` (string): 操作系统平台过滤
- `exploitability_level` (string): 可利用性级别过滤
- `cvss_min` (float): CVSS最低分
- `cvss_max` (float): CVSS最高分
- `date_from` (datetime): 开始日期
- `date_to` (datetime): 结束日期

**响应:**
```json
{
  "data": [...],
  "total": 200000,
  "page": 1,
  "per_page": 50,
  "total_pages": 4000
}
```

#### GET /api/statistics
获取统计信息

**响应:**
```json
{
  "severity": [{"name": "Critical", "value": 100}],
  "status": [{"name": "Active", "value": 500}],
  "platform": [...],
  "vendor": [...],
  "exploitability": [...],
  "age_distribution": {...},
  "exploitability_ratio": [...],
  "autopatch_coverage": {...},
  "new_vulnerabilities_7days": 10
}
```

### 5.2 快照管理API

#### POST /api/create-initial-snapshot
创建初始快照

#### GET /api/snapshots
获取快照列表

**查询参数:**
- `limit` (int, 默认100): 返回数量限制

#### GET /api/snapshots/<snapshot_id>/details
获取快照详情

#### GET /api/snapshots/trend
获取快照趋势数据

### 5.3 同步API

#### GET /api/sync-status
获取同步状态

**响应:**
```json
{
  "last_sync_time": "2024-01-01T00:00:00",
  "sync_type": "full",
  "is_syncing": false
}
```

#### POST /api/sync
触发数据同步

**响应:**
```json
{
  "message": "Sync started",
  "sync_id": "sync_123"
}
```

### 5.4 ServiceNow API

#### GET /api/servicenow/tickets
获取工单列表

**查询参数:**
- `table` (string, 默认"incident"): 表名
- `query` (string): 查询条件
- `limit` (int, 默认100): 数量限制
- `offset` (int, 默认0): 偏移量

#### POST /api/servicenow/tickets
创建工单

**请求体:**
```json
{
  "table": "incident",
  "short_description": "漏洞修复工单",
  "description": "...",
  "priority": "3",
  "urgency": "3",
  "impact": "3"
}
```

### 5.5 威胁情报API

#### POST /api/threat-intelligence/extract-ip
从文本中提取IP地址

**请求体:**
```json
{
  "text": "IP addresses: 192.168.1.1, 10.0.0.1"
}
```

**响应:**
```json
{
  "ips": ["192.168.1.1", "10.0.0.1"],
  "csv": "192.168.1.1\n10.0.0.1",
  "count": 2
}
```

### 5.6 AI聊天API

#### POST /api/chat
AI聊天接口

**请求体:**
```json
{
  "message": "你的问题"
}
```

**响应:**
```json
{
  "message": "AI回复内容",
  "timestamp": "2024-01-01T00:00:00"
}
```

## 6. 数据库文档

### 6.1 数据库表结构

#### 6.1.1 vulnerabilities - 漏洞主表
存储从Microsoft Defender API获取的设备级别漏洞详情

**字段说明:**
- `id` (VARCHAR(255), PRIMARY KEY): 主键，唯一标识符
- `cve_id` (VARCHAR(50)): CVE ID
- `device_id` (VARCHAR(100)): 设备ID
- `device_name` (VARCHAR(255)): 设备名称
- `rbac_group_name` (VARCHAR(100)): RBAC组名
- `os_platform` (VARCHAR(50)): 操作系统平台
- `os_version` (VARCHAR(50)): 操作系统版本
- `os_architecture` (VARCHAR(20)): 操作系统架构
- `software_vendor` (VARCHAR(100)): 软件供应商
- `software_name` (VARCHAR(100)): 软件名称
- `software_version` (VARCHAR(100)): 软件版本
- `vulnerability_severity_level` (VARCHAR(50)): 漏洞严重程度
- `cvss_score` (FLOAT): CVSS分数
- `status` (VARCHAR(20)): 状态（Active/Fixed等）
- `exploitability_level` (VARCHAR(50)): 可利用性级别
- `security_update_available` (BOOLEAN): 是否有安全更新
- `recommended_security_update` (TEXT): 推荐的安全更新
- `recommended_security_update_id` (VARCHAR(100)): 推荐更新ID
- `recommended_security_update_url` (TEXT): 推荐更新URL
- `recommendation_reference` (VARCHAR(255)): 推荐参考
- `autopatch_covered` (BOOLEAN): 是否被Autopatch覆盖
- `disk_paths` (JSON): 磁盘路径
- `registry_paths` (JSON): 注册表路径
- `last_seen_timestamp` (DATETIME): 最后发现时间
- `first_seen_timestamp` (DATETIME): 首次发现时间
- `event_timestamp` (DATETIME): 事件时间戳
- `last_synced` (DATETIME): 最后同步时间

**索引:**
- `idx_cve_id`: CVE ID索引
- `idx_device_id`: 设备ID索引
- `idx_cve_device`: CVE ID和设备ID联合索引
- `idx_status`: 状态索引
- `idx_severity`: 严重程度索引
- `idx_autopatch_covered`: Autopatch覆盖索引
- `idx_last_seen`: 最后发现时间索引
- `idx_first_seen`: 首次发现时间索引

#### 6.1.2 sync_state - 同步状态表
记录同步操作历史

**字段说明:**
- `id` (INT, AUTO_INCREMENT, PRIMARY KEY): 主键
- `last_sync_time` (DATETIME, NOT NULL): 最后同步时间
- `sync_type` (VARCHAR(20), DEFAULT 'full'): 同步类型
- `records_count` (INT, DEFAULT 0): 记录数量
- `created_at` (DATETIME, DEFAULT CURRENT_TIMESTAMP): 创建时间

**索引:**
- `idx_sync_time`: 同步时间索引

#### 6.1.3 vulnerability_snapshots - 快照表
记录漏洞快照统计信息

**字段说明:**
- `id` (INT, AUTO_INCREMENT, PRIMARY KEY): 主键
- `snapshot_time` (DATETIME, NOT NULL): 快照时间
- `total_vulnerabilities` (INT, DEFAULT 0): 总漏洞数
- `unique_cve_count` (INT, DEFAULT 0): 唯一CVE数量
- `critical_count` (INT, DEFAULT 0): Critical数量
- `high_count` (INT, DEFAULT 0): High数量
- `medium_count` (INT, DEFAULT 0): Medium数量
- `low_count` (INT, DEFAULT 0): Low数量
- `fixed_count` (INT, DEFAULT 0): 已修复数量
- `active_count` (INT, DEFAULT 0): 活跃数量
- `total_devices_affected` (INT, DEFAULT 0): 受影响设备总数
- `created_at` (DATETIME, DEFAULT CURRENT_TIMESTAMP): 创建时间

**索引:**
- `idx_snapshot_time`: 快照时间索引

#### 6.1.4 cve_device_snapshots - CVE-设备快照表
记录CVE-设备组合快照，用于跟踪修复状态

**字段说明:**
- `id` (INT, AUTO_INCREMENT, PRIMARY KEY): 主键
- `snapshot_id` (INT, NOT NULL): 快照ID（外键）
- `cve_id` (VARCHAR(50), NOT NULL): CVE ID
- `device_id` (VARCHAR(100), NOT NULL): 设备ID
- `device_name` (VARCHAR(255)): 设备名称
- `status` (VARCHAR(20), NOT NULL): 状态
- `severity` (VARCHAR(50)): 严重程度
- `cvss_score` (FLOAT): CVSS分数
- `first_seen` (DATETIME): 首次发现时间
- `last_seen` (DATETIME): 最后发现时间

**索引:**
- `uk_snapshot_cve_device`: 快照ID、CVE ID和设备ID唯一索引
- `idx_snapshot_id`: 快照ID索引
- `idx_cve_id`: CVE ID索引
- `idx_device_id`: 设备ID索引
- `idx_status`: 状态索引

**外键:**
- `snapshot_id` -> `vulnerability_snapshots.id` (ON DELETE CASCADE)

### 6.2 数据关系图
```
vulnerability_snapshots (1) ──< (N) cve_device_snapshots
```

### 6.3 数据库初始化
- 应用启动时自动执行 `initialize_database()` 创建表结构
- 支持数据库迁移 `migrate_database()` 处理表结构变更

### 6.4 设备标签
- `vulnerabilities.device_tag`: 由 `device_tag_rules` 匹配得到的归属标签（如 `panjin`、`victrex`），可为空。
- `device_tag_rules`: 维护 `tag/pattern/priority/enabled`，默认包含上述规则并预留 `txv`，支持按优先级（数值越小越先匹配）执行。
- `device_tags`: 物化后的 `device_name → tag` 映射，`apply_device_tag_rules()` 每次全量同步后重建，供前端过滤和统计读取。

## 7. 配置文档

### 7.1 环境变量配置 (.env)
```env
# Microsoft Defender API配置
TENANT_ID=your_tenant_id
APP_ID=your_app_id
APP_SECRET=your_app_secret
REGION_ENDPOINT=api.securitycenter.microsoft.com

# MySQL数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_NAME=your_database_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password

# FastAPI配置
SECRET_KEY=your_secret_key
API_DEBUG=False
LOG_LEVEL=INFO
```

### 7.2 Microsoft Defender API配置
- 需要Azure AD应用注册
- 需要 `Vulnerability.Read.All` 权限（Application）或 `Vulnerability.Read` 权限（Delegated）
- 使用OAuth2客户端凭证模式认证

### 7.3 ServiceNow配置
- 通过前端配置页面设置
- 需要实例URL、用户名和密码

## 8. 部署文档

### 8.1 安装步骤

#### 1. 安装Python依赖
```bash
pip install -r requirements.txt
```

#### 2. 配置环境变量
创建 `.env` 文件，配置上述环境变量

#### 3. 初始化数据库
应用启动时会自动初始化数据库表结构

#### 4. 构建前端（生产环境）
```bash
cd frontend
npm install
npm run build
cd ..
```

#### 5. 启动Web服务器
```bash
uvicorn app:app --host 0.0.0.0 --port 5001 --reload
# 或
python3 app.py
```

服务器将在 `http://localhost:5001` 启动

### 8.2 开发模式
- FastAPI后端: `uvicorn app:app --reload --port 5001`
- React开发服务器: `cd frontend && npm run dev` (端口3000)

### 8.3 数据同步
运行同步脚本（或通过API触发）:
```bash
python3 defender.py
```

## 9. 开发指南

### 9.1 代码结构规范
- 路由层: 处理HTTP请求，参数验证
- 服务层: 业务逻辑处理
- 集成层: 第三方API封装
- 数据访问层: 数据库操作封装

### 9.2 开发环境设置
1. Python 3.8+
2. Node.js 16+
3. MySQL 8.0+
4. 安装依赖（见部署文档）

### 9.3 调试方法
- 后端: FastAPI + uvicorn reload 日志（`uvicorn app:app --reload`），同步完成后可执行 `SELECT device_tag, COUNT(*) FROM vulnerabilities GROUP BY device_tag` 验证标签效果
- 前端: 浏览器开发者工具，React DevTools
- 数据库: 直接查询MySQL数据库

## 10. 功能模块详细说明

### 10.1 漏洞管理功能
- 漏洞列表查询（分页、过滤）
- 多维度统计（严重程度、状态、平台、供应商等）
- 漏洞详情查看
- 已修复漏洞追踪

### 10.2 数据同步机制
- 从Microsoft Defender API同步漏洞数据
- 支持全量同步
- 同步状态和进度跟踪
- 自动创建快照

### 10.3 快照和趋势分析
- 创建漏洞快照
- 快照历史查询
- 趋势图表展示
- CVE历史追踪

### 10.4 ServiceNow集成
- 工单创建和管理
- 工单备注功能
- 连接测试

### 10.5 威胁情报功能
- IP地址提取
- CSV导出

### 10.6 AI聊天功能
- 聊天接口（待集成AI服务）

---

**文档版本**: 1.0  
**最后更新**: 2024
