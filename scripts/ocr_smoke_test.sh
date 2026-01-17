#!/usr/bin/env bash
set -euo pipefail

API_BASE_URL="${API_BASE_URL:-http://127.0.0.1:8000}"
DATA_FILE="${DATA_FILE:-data/sample.png}"
PROVIDER_A="${PROVIDER_A:-paddleocr}"
PROVIDER_B="${PROVIDER_B:-deepseek-ocr}"

echo "Using API_BASE_URL=${API_BASE_URL}"
echo "Using DATA_FILE=${DATA_FILE}"
echo "Using PROVIDER_A=${PROVIDER_A}"
echo "Using PROVIDER_B=${PROVIDER_B}"

echo "1) List providers"
curl -s "${API_BASE_URL}/api/v1/ocr/providers" | jq .

echo "2) Run OCR (single provider)"
curl -s -X POST "${API_BASE_URL}/api/v1/ocr/run" \
  -H "Content-Type: application/json" \
  -d "{\"input_id\":\"${DATA_FILE}\",\"provider_id\":\"${PROVIDER_A}\"}" | jq .

echo "3) Compare providers (side-by-side)"
curl -s -X POST "${API_BASE_URL}/api/v1/ocr/compare" \
  -H "Content-Type: application/json" \
  -d "{\"input_id\":\"${DATA_FILE}\",\"provider_a_id\":\"${PROVIDER_A}\",\"provider_b_id\":\"${PROVIDER_B}\"}" | jq .
