#!/bin/bash

# Extrair chave do .env
OPENAI_KEY=$(grep "^OPENAI_API_KEY=" docker/.env | cut -d'=' -f2)

echo "=== Testando OpenAI API ==="
echo "Key length: ${#OPENAI_KEY}"
echo ""

# Testar embedding
response=$(curl -s -X POST "https://api.openai.com/v1/embeddings" \
  -H "Authorization: Bearer $OPENAI_KEY" \
  -H "Content-Type: application/json" \
  -d '{"input": "teste simples", "model": "text-embedding-3-small"}')

echo "Response:"
echo "$response" | jq

# Extrair embedding
embedding=$(echo "$response" | jq -r '.data[0].embedding[0:5]')
echo ""
echo "Primeiros 5 valores do embedding: $embedding"
