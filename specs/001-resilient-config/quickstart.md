# Quickstart: Resilient Configuration

**Created**: 2026-01-14  
**Purpose**: Operator guide for configuring modular pipelines

## Overview

This feature lets operators and maintainers select modules per processing stage, validate compatibility, and activate configurations safely with rollback and fallback behavior.

## Create a Configuration

1. Create a configuration with module selections for each required stage.
2. Validate the configuration to ensure capability contracts match.
3. Review validation results before activation.

## Activate a Configuration

1. Activate the validated configuration.
2. Activation is queued if processing is active.
3. Once active, the new configuration applies to future runs only.

## Roll Back

1. Select a previous configuration version.
2. Trigger rollback to restore it as the active version.
3. Confirm rollback results in the configuration history.

## Monitor Changes

- Review structured logs for module selection, activation, and fallback events.
- Use basic metrics to track activation outcomes and failure rates.

## API Usage Notes

- Configuration endpoints require `X-User-Role` header set to `operator` or `maintainer`.
- Activation and rollback support `processing_active` query parameter to queue changes during active runs.
- Validation should be called before activation to avoid rejection.

## Handling Failures

- If a selected module is unavailable at startup, the fallback module is used and a warning is emitted.
- If a module fails mid-run and no fallback exists, only the affected stage fails while others remain available.
