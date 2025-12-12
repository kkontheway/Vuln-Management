# 漏洞管理系统

一个现代化的漏洞管理系统，用于管理和分析Microsoft Defender收集的漏洞数据。

## 功能特性

- 🎨 **现代化UI设计** - 采用Apple Liquid Glass效果，美观流畅
- 📊 **数据可视化** - 支持多种统计图表展示
- 🔍 **强大的过滤功能** - 支持多条件组合过滤
- 💬 **AI聊天助手** - 内置AI助手，帮助分析漏洞数据
- 📱 **响应式设计** - 适配各种屏幕尺寸
- ⚡ **高性能** - 支持20万+数据的高效查询和分页
- 🔐 **身份扩展** - 已预留 Microsoft Entra ID 接入点

## 系统架构

```
VulnManagement/
├── defender.py          # Defender API数据同步脚本
├── app.py              # FastAPI后端API服务器
├── servicenow_client.py # ServiceNow API客户端
├── frontend/           # React前端应用
│   ├── src/           # 源代码
│   ├── dist/          # 构建输出（生产环境）
│   └── package.json   # 前端依赖
├── requirements.txt    # Python依赖
└── README.md          # 说明文档
```

## 安装步骤（Step by Step）

### 1. 用 Docker 启动 MySQL 8.0
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
- `MYSQL_DATABASE/USER/PASSWORD` 请与 `.env` 中保持一致。
- 容器启动后可用 `mysql -h127.0.0.1 -P3306 -uroot -p` 和 `docker logs mysql-db` 检查状态。

### 2. 导入历史数据（dump.sql）
```bash
# 将 dump.sql 上传到服务器（示例）
scp dump.sql user@server:/opt/vuln/dump.sql

# 通过 docker exec 导入
cat /opt/vuln/dump.sql | docker exec -i mysql-db \
  mysql -uroot -p"$MYSQL_ROOT_PASSWORD" vulndb
```
- 如果 dump 内含 `CREATE DATABASE`，可先执行 `docker exec -it mysql-db mysql -uroot -p -e "DROP DATABASE IF EXISTS vulndb; CREATE DATABASE vulndb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"`。
- 导入完成后使用 `mysql -h127.0.0.1 -P3306 -uvuln_app -p vulndb -e "SHOW TABLES;"` 验证。

### 3. 配置环境变量
- 本地：`cp .env.example .env`
- 服务器：`cp .env.example .env.prod`
- 至少需要设置：
```env
TENANT_ID=xxx
APP_ID=xxx
APP_SECRET=xxx
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=vulndb
DB_USER=vuln_app
DB_PASSWORD=vuln_app_password
MYSQL_ROOT_PASSWORD=change-this-root-password
SECRET_KEY=change-this-secret
INTEGRATIONS_SECRET_KEY=base64-url-safe-32-byte-key
```
> `.env` 会被 `config.py` 自动读取，`initialize_app_database()` 会在后端启动时建表/迁移。

### 4. 安装并运行 FastAPI 后端
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 5001 --reload  # 开发模式
# 或使用脚本封装
python app.py  # 调用 uvicorn.run，适合本地验证
nohup python app.py > backend.log 2>&1 &  # 后台常驻
```
- API 地址：`http://127.0.0.1:5001/api/...`
- 使用 `tail -f backend.log`、`lsof -i :5001` 或 `uvicorn --version`/`ps aux | grep uvicorn` 检查运行情况。

### 5. 构建 React 前端
```bash
cd frontend
npm install  # 首次
npm run build
```
- 构建产物位于 `frontend/dist`，FastAPI 会自动作为静态目录。
- 若想由 Nginx 直接托管，可 `rsync -av frontend/dist/ /var/www/vuln-frontend/`。

### 6. 配置 Nginx（统一 80 端口）
```
server {
    listen 80;
    server_name your_domain.com;

    root /var/www/vuln-frontend;  # 或项目内 frontend/dist 的绝对路径
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
- 用 `curl http://your_domain/api/vulnerabilities` 验证代理是否透传。

### 7. 同步 Microsoft Defender 数据（可选）
```bash
source .venv/bin/activate
python defender.py
```
- 可以将 `python defender.py` 写入 `cron`（如 `0 */6 * * * /opt/vuln/.venv/bin/python /opt/vuln/defender.py`）保持数据库最新。

## 使用说明

### 数据同步

定期运行 `defender.py` 来同步最新的漏洞数据：

```bash
python3 defender.py
```

脚本会自动：
- 检查是否需要全量同步（每7天一次）
- 执行增量同步获取最新变更（设备漏洞详情）
- 同时执行全量同步获取漏洞列表（因为该API不支持增量）
- 更新数据库中的漏洞信息
- 创建快照记录（包括设备漏洞详情快照和漏洞列表快照）

### Web界面使用

1. **查看漏洞列表**
   - 表格显示所有漏洞信息
   - 支持分页浏览（25/50/100/200条每页）
   - 点击"详情"按钮查看完整信息

2. **过滤数据**
   - 使用顶部过滤器面板设置过滤条件
   - 支持按CVE ID、设备名称、严重程度、状态等过滤
   - 支持CVSS分数范围过滤
   - 点击"应用过滤"执行过滤，"清除过滤"重置

3. **查看统计图表**
   - 自动生成按严重程度、状态、平台的分布图表
   - 图表实时更新，反映当前过滤结果

4. **AI助手**
   - 右侧聊天框可以与AI助手交互
   - 可以询问关于漏洞数据的问题
   - AI功能可以集成OpenAI或其他AI服务

## API接口

### GET /api/vulnerabilities
获取漏洞列表

**查询参数：**
- `page`: 页码（默认1）
- `per_page`: 每页数量（默认50）
- `cve_id`: CVE ID过滤
- `device_name`: 设备名称过滤
- `vulnerability_severity_level`: 严重程度过滤
- `status`: 状态过滤
- `os_platform`: 操作系统平台过滤
- `exploitability_level`: 可利用性级别过滤
- `cvss_min`: CVSS最低分
- `cvss_max`: CVSS最高分

**响应：**
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
获取统计信息

**响应：**
```json
{
  "severity": [...],
  "status": [...],
  "platform": [...],
  "vendor": [...],
  "exploitability": [...]
}
```

### GET /api/filter-options
获取过滤器选项列表

### POST /api/chat
AI聊天接口

**请求体：**
```json
{
  "message": "你的问题"
}
```

## 性能优化建议

对于20万+数据量，建议：

1. **数据库索引优化**
   - 确保在常用过滤字段上创建索引
   - 特别是 `cve_id`, `device_name`, `vulnerability_severity_level` 等

2. **分页查询**
   - 使用合理的每页数量（建议50-100条）

## TODO

- [ ] `/api/vulnerabilities` 暂未提供可靠的 `@odata.count`，目前 catalog 同步默认最多拉取 24,000 条（3 页 * 8,000 条）。后续一旦确认官方提供总数或新的分页方式，需要移除该上限并完成全量拉取。
   - 避免一次性加载所有数据

3. **缓存策略**
   - 可以考虑对统计数据进行缓存
   - 使用Redis缓存常用查询结果

4. **数据库连接池**
   - 考虑使用连接池管理数据库连接
   - 减少连接开销

## 扩展功能

### 集成AI服务

在 `app.py` 的 `/api/chat` 接口中，可以集成OpenAI API：

```python
import openai

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message', '')
    
    # 集成OpenAI
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "你是一个漏洞管理专家..."},
            {"role": "user", "content": message}
        ]
    )
    
    return jsonify({
        'message': response.choices[0].message.content
    })
```

### 导出功能

可以添加导出功能，将过滤后的数据导出为CSV或Excel：

```python
@app.route('/api/export', methods=['GET'])
def export_vulnerabilities():
    # 实现导出逻辑
    pass
```

## 数据库表结构

### 主要数据表

1. **vulnerability_info** - 设备级别的漏洞详情
   - 存储从 `/api/machines/SoftwareVulnerabilitiesByMachine` API获取的数据
   - 包含设备信息、软件信息、漏洞严重程度等
   - 主键：id (VARCHAR(255))

2. **vulnerability_list** - 漏洞列表
   - 存储从 `/api/vulnerabilities` API获取的数据
   - 包含CVE ID、描述、严重程度、CVSS分数、EPSS分数、利用信息等
   - 字段包括：id (CVE ID), name, description, severity, cvss_v3, exposed_machines, public_exploit, exploit_verified, exploit_in_kit, epss等
   - 主键：id (VARCHAR(50))

### 快照表

1. **vulnerability_snapshots** - 设备漏洞详情快照
   - 记录设备漏洞详情的统计信息
   - 包括总漏洞数、唯一CVE数、按严重程度统计、按状态统计等

2. **vulnerability_list_snapshots** - 漏洞列表快照
   - 记录漏洞列表的统计信息
   - 包括总漏洞数、按严重程度统计（Critical/High/Medium/Low）、公开利用漏洞数、已验证利用漏洞数、在工具包中的漏洞数、平均EPSS分数、总受影响设备数等

## 故障排除

### 数据库连接失败
- 检查 `.env` 文件中的数据库配置
- 确认MySQL服务正在运行
- 检查防火墙设置

### API请求失败
- 检查Microsoft Defender API凭证（两个API都需要Bearer token认证）
- 确认网络连接正常
- 查看日志文件 `defender_api.log`
- 注意 `/api/vulnerabilities` API需要 `Vulnerability.Read.All` 权限（Application）或 `Vulnerability.Read` 权限（Delegated）

### 前端无法加载
- 确认FastAPI服务器正在运行
- 检查浏览器控制台错误
- 确认静态文件路径正确

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

# TODO
- [ ] TI Tab
  - [ ] 如何实现
  - [ ] 除了从record future中获取，我还能从哪里获取数据，参考WIZ
- [ ] 登陆 with MFA
- [ ] 图表
- [ ] 
