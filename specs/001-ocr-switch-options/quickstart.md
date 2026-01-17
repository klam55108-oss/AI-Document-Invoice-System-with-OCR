# Quickstart: Switchable OCR Providers

## Goal

Run OCR with a selected provider and compare PaddleOCR vs DeepSeek OCR results on a single invoice.

## Prerequisites

- Access to an invoice/document input
- Admin access to set default and enabled providers
- CPU-only environment for DeepSeek OCR (no CUDA/GPU)

## Configure Providers

1. Enable `paddleocr` and `deepseek` providers.
2. Set a default provider (admin-only).
3. Ensure provider configuration can be updated without code changes.

## Run OCR with a Selected Provider

1. Submit an OCR request with the selected provider.
2. Verify the OCR result includes the provider label and extracted fields.

## Compare Providers (Single Invoice)

1. Submit a comparison request for a single invoice with both providers.
2. Confirm side-by-side output displays extracted text and key fields for both providers.
3. If one provider fails, confirm the successful result is returned and the failed provider is marked with an error status.

## Expected Outcomes

- Provider selection overrides default when explicitly specified.
- Comparison is limited to a single invoice per request.
