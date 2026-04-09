# WF02 V76 - Quick Deployment Reference

> **One-Page Guide** for rapid V76 deployment. See full docs for details.

---

## ✅ Pre-Deployment Checklist

```bash
# 1. Verify WF06 is deployed
bash scripts/test-wf06-endpoints.sh
# Expected: All 10 tests pass

# 2. Check files exist
ls -l n8n/workflows/02_ai_agent_conversation_V76_PROACTIVE_UX.json
ls -l scripts/wf02-v76-state-machine.js
ls -l scripts/deploy-wf02-v76.sh
# Expected: All files present (105K, 418 lines, 235 lines)
```

---

## 🚀 Deployment Steps (15 minutes)

### Step 1: Run Automation Script
```bash
cd /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot
bash scripts/deploy-wf02-v76.sh
```
**What it does**: Validates environment, creates V76 base, shows manual steps

### Step 2: Manual n8n Configuration (5 min)

**2.1 Import Workflow**
- Open: http://localhost:5678
- Click: "Workflows" → "Import from File"
- Select: `n8n/workflows/02_ai_agent_conversation_V76_PROACTIVE_UX.json`
- **Keep INACTIVE**

**2.2 Add HTTP Request Node 1** (after State 8 confirmation)
```
Name: "HTTP Request - Get Next Dates"
URL: http://e2bot-n8n-dev:5678/webhook/calendar-availability
Method: POST
Body (JSON):
{
  "action": "next_dates",
  "count": 3,
  "duration_minutes": 120
}
Continue on Fail: ✅ Yes
Retry on Fail: ✅ Yes (2 attempts)
Store response in: wf06_next_dates
```

**2.3 Add HTTP Request Node 2** (after State 10 date selection)
```
Name: "HTTP Request - Get Available Slots"
URL: http://e2bot-n8n-dev:5678/webhook/calendar-availability
Method: POST
Body (JSON):
{
  "action": "available_slots",
  "date": {{ $json.scheduled_date }},
  "duration_minutes": 120
}
Continue on Fail: ✅ Yes
Retry on Fail: ✅ Yes (2 attempts)
Store response in: wf06_available_slots
```

**2.4 Update State Machine Code**
- Open: "State Machine V73.4" node
- Replace: All code with content from `scripts/wf02-v76-state-machine.js`
- Save workflow (still INACTIVE)

### Step 3: Test
```bash
# E2E test (interactive)
bash scripts/test-wf02-v76-e2e.sh

# Expected: All steps pass
# Critical: ✨ V76 PROACTIVE date/time suggestions
```

### Step 4: Canary Deployment

**Day 1 - 20% traffic**:
1. Update WF01 routing: 80% V75, 20% V76
2. Activate V76 workflow in n8n
3. Monitor logs for 30 minutes: `docker logs -f e2bot-n8n-dev | grep V76`
4. Continue monitoring for 24 hours

**Success Criteria** (Day 1):
- ✅ Error rate <1%
- ✅ No critical bugs
- ✅ WF06 availability >95%

**Day 3 - Progressive rollout**:
- Morning: 50% traffic (monitor 12h)
- Afternoon: 80% traffic (monitor 12h)

**Day 4 - Full production**:
- 100% traffic
- Deactivate V75 (keep as backup)
- Monitor for 48 hours

---

## 🚨 Rollback (if errors >5%)

```bash
# 1. Update WF01 routing to 100% V75
# 2. Deactivate V76 workflow in n8n
# 3. Review logs
docker logs e2bot-n8n-dev | grep -E "V76|ERROR" > v76_errors.log
# 4. Fix issues and retry
```

---

## 📊 Monitoring Commands

**Real-time logs**:
```bash
docker logs -f e2bot-n8n-dev | grep -E "V76|ERROR|WARN"
```

**V76 usage rate**:
```sql
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "
SELECT
  COUNT(CASE WHEN current_state IN ('show_available_dates', 'process_date_selection',
                                     'show_available_slots', 'process_slot_selection') THEN 1 END) * 100.0 / COUNT(*) as v76_usage_pct
FROM conversations
WHERE created_at > NOW() - INTERVAL '24 hours';"
```

**Fallback rate** (should be <10%):
```sql
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "
SELECT
  COUNT(CASE WHEN current_state LIKE '%_manual' THEN 1 END) * 100.0 /
  COUNT(CASE WHEN current_state LIKE 'show_available_%' OR current_state LIKE '%_manual' THEN 1 END) as fallback_rate_pct
FROM conversations
WHERE updated_at > NOW() - INTERVAL '24 hours';"
```

**WF06 health**:
```bash
curl -s -X POST "http://localhost:5678/webhook/calendar-availability" \
  -H "Content-Type: application/json" \
  -d '{"action":"next_dates","count":3}' | jq '.success'
# Expected: true
```

---

## 📚 Full Documentation

- **Technical Details**: `docs/WF02_V76_IMPLEMENTATION_GUIDE.md`
- **Complete Deployment**: `docs/WF02_V76_DEPLOYMENT_SUMMARY.md`
- **Implementation Report**: `docs/WF02_V76_COMPLETION_REPORT.md`
- **State Machine Code**: `scripts/wf02-v76-state-machine.js`
- **Deployment Automation**: `scripts/deploy-wf02-v76.sh`
- **E2E Testing**: `scripts/test-wf02-v76-e2e.sh`

---

## 🎯 Expected Results

| Metric | Before (V75) | After (V76) |
|--------|--------------|-------------|
| Input Errors | 2-3 per conversation | 0 (happy path) |
| Total Interactions | 7-10 | ~8 |
| Mobile Typing | Heavy | Minimal (1-3, 1-N) |
| Completion Rate | ~75% | >90% |

---

**Status**: ✅ Ready for Production
**Estimated Deploy Time**: 15 minutes (manual steps) + 4 days (canary)
**Risk Level**: Low (graceful fallback, canary deployment)
