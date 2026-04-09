# WF07 V6 - Docker Template Access Solution

> **Date**: 2026-03-30
> **Issue**: V5 execution 16333 - Read Template File cannot access host filesystem
> **Root Cause**: Email templates exist on host but are not mounted in Docker container
> **Solution**: 3 approaches - Docker volume mount (recommended), workflow mount copy, or template embedding
> **Status**: Planning phase, requires user decision on approach

---

## 🔴 Problem Summary

### V5 Error (Execution 16333)

**URL**: `http://localhost:5678/workflow/ctLeuOPzWPvwmMvW/executions/16333`

**Symptoms**:
```
"Read Template File" node tries to access:
/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/email-templates/confirmacao_agendamento.html

Inside Docker container:
- Path doesn't exist (host filesystem not accessible)
- Node fails to read file
- Workflow cannot complete
```

**Impact**:
- WF07 V5 cannot read email templates inside Docker container
- WF05 → WF07 integration broken (no confirmation emails)
- Email automation completely non-functional

---

## 🔍 Root Cause Analysis

### Docker Container Architecture

**Docker Inspect Results** (`e2bot-n8n-dev`):
```json
"Mounts": [
  {
    "Type": "volume",
    "Name": "e2bot_n8n_dev_data",
    "Source": "/var/lib/docker/volumes/e2bot_n8n_dev_data/_data",
    "Destination": "/home/node/.n8n",
    "Mode": "z"
  },
  {
    "Type": "bind",
    "Source": "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows",
    "Destination": "/workflows",
    "Mode": "ro"
  }
]
```

**Key Finding**:
- ✅ Container has access to `/workflows` (read-only mount)
- ✅ Container has access to `/home/node/.n8n` (n8n data)
- ❌ Container does NOT have access to `/home/bruno/Desktop/.../email-templates/`
- ❌ Host filesystem path `/home/bruno/...` does not exist inside container

### Email Templates Location

**Host**: `/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/email-templates/`
```bash
ls -la email-templates/
total 32
drwxr-xr-x  2 bruno bruno  4096 Mar 30 18:45 .
drwxr-xr-x 12 bruno bruno  4096 Mar 30 19:22 ..
-rw-r--r--  1 bruno bruno  6534 Mar 30 18:45 apos_visita.html
-rw-r--r--  1 bruno bruno  7128 Mar 30 18:45 confirmacao_agendamento.html
-rw-r--r--  1 bruno bruno  5891 Mar 30 18:45 lembrete_2h.html
-rw-r--r--  1 bruno bruno  5234 Mar 30 18:45 novo_lead.html
```

**Container**: Path `/home/bruno/...` does not exist (different user context)

### Why V4.1 and V5 Fixes Were Insufficient

**V4.1 Fix**: Added `encoding: "utf8"` option
- ✅ Correct approach for text file reading
- ❌ Irrelevant - file cannot be read if path doesn't exist

**V5 Fix**: Added `dataPropertyName: "data"` option
- ✅ Correct approach for output property definition
- ❌ Irrelevant - file cannot be read if path doesn't exist

**V4.1 + V5 Configuration** (lines 34-39):
```json
{
  "parameters": {
    "operation": "read",
    "filePath": "=/home/bruno/Desktop/.../email-templates/{{ $json.template_file }}",
    "options": {
      "encoding": "utf8",          // ✅ V4.1: Text reading
      "dataPropertyName": "data"   // ✅ V5: Output property
    }
  }
}
```

**Result**: Both fixes are technically correct, but container cannot access the file path at all.

---

## ✅ V6 Solutions - Docker-Compatible Template Access

### **Solution 1: Docker Volume Mount** (RECOMMENDED ⭐)

**Approach**: Mount email templates directory into Docker container

**Pros**:
- ✅ Clean separation: templates stay in dedicated directory
- ✅ Easy updates: edit templates on host, immediately available in container
- ✅ No code duplication: templates exist in single location
- ✅ Scalable: works for any number of templates
- ✅ Standard Docker practice: proper use of volume mounts

**Cons**:
- ⚠️ Requires Docker restart: `docker-compose down` + `up`
- ⚠️ Infrastructure change: modifies docker-compose-dev.yml

**Implementation Steps**:

1. **Update `docker/docker-compose-dev.yml`** (add mount):
```yaml
n8n-dev:
  image: n8nio/n8n:latest
  container_name: e2bot-n8n-dev
  # ... existing config ...
  volumes:
    # Existing mounts
    - n8n_dev_data:/home/node/.n8n
    - ../n8n/workflows:/workflows:ro

    # ✅ NEW: Email templates mount
    - ../email-templates:/email-templates:ro
```

2. **Update WF07 V6 Read File path** (V5 → V6):
```json
// V5 (BROKEN - host path)
"filePath": "=/home/bruno/Desktop/.../email-templates/{{ $json.template_file }}"

// V6 (WORKING - container mount)
"filePath": "=/email-templates/{{ $json.template_file }}"
```

3. **Restart Docker container**:
```bash
docker-compose -f docker/docker-compose-dev.yml down
docker-compose -f docker/docker-compose-dev.yml up -d
```

4. **Verify mount inside container**:
```bash
docker exec e2bot-n8n-dev ls -la /email-templates/
# Expected: 4 HTML files visible
```

**File Changes**:
- `docker/docker-compose-dev.yml`: Add 1 volume mount line
- WF07 V6 workflow: Change filePath to `/email-templates/...`

---

### **Solution 2: Copy Templates to Workflows Mount** (ALTERNATIVE)

**Approach**: Copy templates into existing `/workflows` mount subdirectory

**Pros**:
- ✅ No Docker restart: uses existing mount
- ✅ No docker-compose.yml change: zero infrastructure modifications
- ✅ Immediate availability: copy and test instantly

**Cons**:
- ⚠️ Code organization: templates mixed with workflow JSON files
- ⚠️ Manual updates: need to copy templates after every change
- ⚠️ Duplication: templates exist in 2 locations (original + copy)
- ⚠️ Sync risk: original and copy can become out of sync

**Implementation Steps**:

1. **Copy templates to workflows mount**:
```bash
mkdir -p n8n/workflows/email-templates
cp email-templates/*.html n8n/workflows/email-templates/
```

2. **Update WF07 V6 Read File path** (V5 → V6):
```json
// V5 (BROKEN - host path)
"filePath": "=/home/bruno/Desktop/.../email-templates/{{ $json.template_file }}"

// V6 ALT (WORKING - workflows mount)
"filePath": "=/workflows/email-templates/{{ $json.template_file }}"
```

3. **Verify access inside container**:
```bash
docker exec e2bot-n8n-dev ls -la /workflows/email-templates/
# Expected: 4 HTML files visible
```

**File Changes**:
- `n8n/workflows/email-templates/` directory: Create + copy 4 HTML files
- WF07 V6 workflow: Change filePath to `/workflows/email-templates/...`

**Maintenance**:
- After editing templates: `cp email-templates/*.html n8n/workflows/email-templates/`
- Consider adding sync script: `scripts/sync-email-templates.sh`

---

### **Solution 3: Embed Templates in Workflow** (NOT RECOMMENDED)

**Approach**: Store HTML templates directly in workflow JSON as base64 or strings

**Pros**:
- ✅ No Docker changes: zero infrastructure modifications
- ✅ No filesystem: self-contained workflow
- ✅ Portable: workflow contains everything needed

**Cons**:
- ❌ Workflow bloat: JSON file becomes 50+ KB (currently 14 KB)
- ❌ Hard to edit: HTML templates embedded in JSON are difficult to maintain
- ❌ Version control mess: diffs show entire HTML changes
- ❌ Not scalable: adding templates requires workflow regeneration
- ❌ Professional bad practice: mixing code and content

**Implementation** (NOT RECOMMENDED):
- Would require embedding 4 HTML templates (total ~25 KB) into workflow JSON
- Replace Read File node with Code node containing embedded templates
- Update after every template change = workflow regeneration

**Recommendation**: Only use if Docker restart is absolutely impossible AND Solution 2 is unacceptable.

---

## 📊 Solution Comparison

| Criterion | Solution 1 (Volume) | Solution 2 (Copy) | Solution 3 (Embed) |
|-----------|---------------------|-------------------|-------------------|
| **Docker Restart** | Required | Not required | Not required |
| **Infrastructure Change** | Yes (docker-compose.yml) | No | No |
| **Template Updates** | Direct (edit in place) | Manual copy | Workflow regeneration |
| **Code Organization** | ⭐ Clean separation | ⚠️ Mixed locations | ❌ Embedded mess |
| **Maintainability** | ⭐ Easy | ⚠️ Manual sync | ❌ Very difficult |
| **Scalability** | ⭐ Excellent | ⚠️ Manual work | ❌ Not scalable |
| **File Size** | 14 KB workflow | 14 KB workflow | 50+ KB workflow |
| **Best Practice** | ⭐ Standard Docker | ⚠️ Acceptable | ❌ Anti-pattern |
| **Implementation Time** | 5 minutes | 2 minutes | 15 minutes |
| **Production Ready** | ⭐ Yes | ⚠️ With sync process | ❌ No |

---

## 🎯 Recommendation

**Use Solution 1 (Docker Volume Mount)** ⭐

**Rationale**:
1. **Professional Standard**: Proper Docker practice for persistent data
2. **Developer Experience**: Edit templates directly, see changes immediately
3. **Maintainability**: Single source of truth, no duplication
4. **Scalability**: Adding templates is trivial (just create HTML file)
5. **Long-term**: Sets up proper infrastructure for production deployment

**Trade-off**: Requires 5-minute Docker restart, but gains proper architecture

**Fallback**: Solution 2 if Docker restart is temporarily impossible (e.g., active production system)

---

## 🚀 Implementation Plan - Solution 1 (Volume Mount)

### Pre-Implementation Checklist

- [x] Email templates exist in `/email-templates/` directory
- [x] Docker container running (`e2bot-n8n-dev`)
- [ ] No active n8n workflow executions (safe to restart)
- [ ] WF05 V4.0.4 not in production testing (or plan downtime)
- [ ] Backup current docker-compose-dev.yml

### Implementation Steps

**Step 1: Backup Current Configuration**:
```bash
cp docker/docker-compose-dev.yml docker/docker-compose-dev.yml.backup_$(date +%Y%m%d_%H%M%S)
```

**Step 2: Update docker-compose-dev.yml**:
```yaml
# Add to n8n-dev service volumes section (line ~72)
volumes:
  # Existing mounts
  - n8n_dev_data:/home/node/.n8n
  - ../n8n/workflows:/workflows:ro

  # ✅ NEW: Email templates mount (read-only)
  - ../email-templates:/email-templates:ro
```

**Step 3: Restart Docker Stack**:
```bash
# Stop containers
docker-compose -f docker/docker-compose-dev.yml down

# Start containers with new mount
docker-compose -f docker/docker-compose-dev.yml up -d

# Wait for n8n to start (30-60 seconds)
sleep 45

# Check n8n health
docker logs -f e2bot-n8n-dev | head -20
```

**Step 4: Verify Mount Inside Container**:
```bash
# List mounted templates
docker exec e2bot-n8n-dev ls -la /email-templates/

# Expected output:
# -rw-r--r-- 1 node node 7128 Mar 30 confirmacao_agendamento.html
# -rw-r--r-- 1 node node 5891 Mar 30 lembrete_2h.html
# -rw-r--r-- 1 node node 5234 Mar 30 novo_lead.html
# -rw-r--r-- 1 node node 6534 Mar 30 apos_visita.html

# Test read access
docker exec e2bot-n8n-dev cat /email-templates/confirmacao_agendamento.html | head -5
# Expected: HTML content visible
```

**Step 5: Generate WF07 V6 Workflow**:
- Script: `scripts/generate-workflow-wf07-v6-docker-volume-fix.py`
- Changes from V5:
  - Line 35: `filePath` = `/email-templates/{{ $json.template_file }}`
  - Line 49: notes = "V6: Docker volume mount fix - container path"
- Output: `n8n/workflows/07_send_email_v6_docker_volume_fix.json`

**Step 6: Import WF07 V6 to n8n**:
```
http://localhost:5678 → Workflows → Import from File
→ n8n/workflows/07_send_email_v6_docker_volume_fix.json
→ Import
```

**Step 7: Test Read Template File Node**:
```
Execute workflow (manual trigger with test data)
→ Click "Read Template File" node
→ Verify output: { "data": "<html>...</html>", ... }
→ Expected: ✅ No "No output data returned" error
→ Expected: ✅ HTML content in $json.data
```

**Step 8: Test Complete WF05 → WF07 V6 Flow**:
```
WhatsApp → WF02 (Service 1/3) → Complete → Confirm
→ WF05 V4.0.4 executes (Google Calendar + DB)
→ WF07 V6 triggers (email with templates from /email-templates/)
→ Verify: Email sent to lead_email with correct content
```

**Step 9: Monitor (2 hours)**:
```sql
-- Check email logs
SELECT
  recipient_email,
  subject,
  template_used,
  status,
  sent_at
FROM email_logs
WHERE sent_at > NOW() - INTERVAL '2 hours'
ORDER BY sent_at DESC;

-- Check for template read errors
SELECT * FROM email_logs
WHERE status = 'failed'
  AND error_message LIKE '%template%'
  AND sent_at > NOW() - INTERVAL '2 hours';
```

**Step 10: Production Approval**:
```
Success Criteria:
✅ Docker container restarts successfully with new mount
✅ /email-templates/ accessible inside container (4 HTML files)
✅ Read Template File node outputs $json.data with HTML content
✅ Manual test email received with correct formatting
✅ WF05 integration email received within 5 minutes
✅ No "No output data returned" errors
✅ No path errors in logs
✅ Email logs show 'sent' status (no failures)

If all pass → Production approved (V6 deployed)
If any fail → Rollback to docker-compose-dev.yml backup
```

---

## 🔙 Rollback Procedure

**If V6 fails or causes issues**:

**Step 1: Restore docker-compose-dev.yml**:
```bash
# Find backup
ls -la docker/docker-compose-dev.yml.backup_*

# Restore
cp docker/docker-compose-dev.yml.backup_YYYYMMDD_HHMMSS docker/docker-compose-dev.yml
```

**Step 2: Restart Docker Stack**:
```bash
docker-compose -f docker/docker-compose-dev.yml down
docker-compose -f docker/docker-compose-dev.yml up -d
```

**Step 3: Deactivate WF07 V6 in n8n**:
```
http://localhost:5678 → Workflows → "07 - Send Email V6" → Deactivate
```

**Step 4: Investigate Failure**:
```bash
# Check Docker logs
docker logs e2bot-n8n-dev | grep -i error | tail -20

# Check mount status
docker inspect e2bot-n8n-dev | jq '.[] | .Mounts'

# Check n8n workflow execution logs
# http://localhost:5678/workflow/[workflow-id]/executions
```

---

## 📞 Troubleshooting

### Issue: Mount Not Visible Inside Container

**Possible Causes**:
1. Docker not restarted after docker-compose.yml change
2. Typo in volume mount path
3. Host directory doesn't exist or has permission issues

**Resolution**:
```bash
# Verify host directory exists
ls -la /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/email-templates/

# Check Docker mount configuration
docker inspect e2bot-n8n-dev | jq '.[] | .Mounts'

# Restart Docker stack
docker-compose -f docker/docker-compose-dev.yml down
docker-compose -f docker/docker-compose-dev.yml up -d

# Verify mount inside container
docker exec e2bot-n8n-dev ls -la /email-templates/
```

### Issue: Read Template File Still Returns "No output data"

**Possible Causes**:
1. Wrong filePath in workflow (still using host path)
2. Missing encoding or dataPropertyName options
3. File permissions issue

**Resolution**:
```bash
# Verify WF07 V6 configuration
jq '.nodes[] | select(.id == "read-template-file") | .parameters' \
  n8n/workflows/07_send_email_v6_docker_volume_fix.json

# Expected output:
# {
#   "operation": "read",
#   "filePath": "=/email-templates/{{ $json.template_file }}",
#   "options": {
#     "encoding": "utf8",
#     "dataPropertyName": "data"
#   }
# }

# Check file permissions inside container
docker exec e2bot-n8n-dev ls -la /email-templates/
# All files should be readable (r-- permission)
```

### Issue: Template Variables Not Replaced

**Possible Cause**: "Render Template" node not receiving data correctly

**Resolution**: Verify "Read Template File" output contains `.data` property

### Issue: Email Not Sent

**Possible Causes**:
1. SMTP credentials not configured
2. Workflow not activated
3. WF05 trigger incorrect

**Resolution**:
```bash
# Check SMTP credentials
# n8n UI → Settings → Credentials → SMTP - E2 Email

# Check workflow active
# n8n UI → Workflows → "07 - Send Email V6" → Active: ON

# Check WF05 trigger
# WF05 should call executeWorkflow with correct WF07 V6 ID
```

---

## 🎓 Lessons Learned

### Key Insight

**Docker container isolation**: Containers do not have access to host filesystem by default. Any files needed inside containers must be explicitly mounted via docker-compose volumes configuration.

### Technical Understanding

**n8n Read/Write Files node** in Docker context:
- Node executes inside container environment
- Only paths visible inside container can be accessed
- Host filesystem paths (e.g., `/home/bruno/...`) do not exist in container
- Solution requires either volume mount or using already-mounted paths

### Best Practices for n8n in Docker

1. ✅ Mount all required data directories as Docker volumes
2. ✅ Use container paths (e.g., `/email-templates/`) in workflows, not host paths
3. ✅ Test file access inside container before workflow configuration
4. ✅ Document mount requirements in project setup guides
5. ✅ Use read-only mounts (`:ro`) for data that shouldn't be modified

### Documentation Standards

**Critical for Docker-based n8n**:
1. Document all required volume mounts in docker-compose.yml
2. Specify container paths in workflow documentation (not host paths)
3. Include verification steps for mount accessibility
4. Maintain rollback procedures for docker-compose.yml changes
5. Test workflows inside container environment, not just on host

---

## 📝 Documentation References

**Related Files**:
- `docs/PLAN_V5_READ_FILE_DATA_PROPERTY.md` - V5 dataPropertyName fix (insufficient for Docker)
- `docs/BUGFIX_WF07_V5_DATA_PROPERTY_FIX.md` - V5 bugfix documentation (incomplete)
- `docs/BUGFIX_WF07_V4.1_ENCODING_FIX.md` - V4.1 encoding fix
- `docs/BUGFIX_WF07_V4_READ_FILE_FIX.md` - V4 Docker path attempt (incomplete)
- `docker/docker-compose-dev.yml` - Current Docker configuration (needs update)

**New Files** (to be created):
- `scripts/generate-workflow-wf07-v6-docker-volume-fix.py` - V6 generator script
- `n8n/workflows/07_send_email_v6_docker_volume_fix.json` - V6 workflow (Docker-compatible)
- `docs/BUGFIX_WF07_V6_DOCKER_VOLUME_FIX.md` - V6 bugfix documentation

---

**End of Planning Document - V6**

**Next Step**: User decision on solution approach → Implementation → Testing → Production deployment
