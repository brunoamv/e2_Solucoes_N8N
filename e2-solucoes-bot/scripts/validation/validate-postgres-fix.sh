#!/bin/bash
# Validate PostgreSQL Query Fix

echo "🔍 Validating PostgreSQL Query Fix..."
echo "=================================="

# Check if workflow file exists
if [ -f "n8n/workflows/02_ai_agent_conversation_V16.json" ]; then
    echo "✓ Workflow V16 file exists"
else
    echo "❌ Workflow V16 file not found"
    exit 1
fi

# Check for Build SQL Queries node
if grep -q "Build SQL Queries" n8n/workflows/02_ai_agent_conversation_V16.json; then
    echo "✓ Build SQL Queries node present"
else
    echo "❌ Build SQL Queries node not found"
    exit 1
fi

# Check for query_count usage
if grep -q "query_count" n8n/workflows/02_ai_agent_conversation_V16.json; then
    echo "✓ query_count field is being used"
else
    echo "❌ query_count field not found"
    exit 1
fi

# Check for query_details usage
if grep -q "query_details" n8n/workflows/02_ai_agent_conversation_V16.json; then
    echo "✓ query_details field is being used"
else
    echo "❌ query_details field not found"
    exit 1
fi

# Check for query_upsert usage
if grep -q "query_upsert" n8n/workflows/02_ai_agent_conversation_V16.json; then
    echo "✓ query_upsert field is being used"
else
    echo "❌ query_upsert field not found"
    exit 1
fi

echo ""
echo "✅ All validations passed!"
echo ""
echo "📋 To import into n8n:"
echo "1. Open http://localhost:5678"
echo "2. Go to Workflows → Import"
echo "3. Select file: n8n/workflows/02_ai_agent_conversation_V16.json"
