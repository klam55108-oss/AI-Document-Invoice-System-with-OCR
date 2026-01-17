# Research Decisions: Switchable OCR Providers

## Decision 1: Provider selection and configuration is config-driven

**Decision**: Use a configurable provider registry with an enabled list and default provider, managed by admin-only controls.  
**Rationale**: Meets requirements for non-code configuration, reduces errors, and keeps provider selection consistent across runs.  
**Alternatives considered**: Hardcoded provider; per-user default configuration.

## Decision 2: Comparison output is side-by-side with text and key fields

**Decision**: Provide side-by-side outputs showing extracted text and key fields for both providers.  
**Rationale**: Supports direct comparison and user review without additional processing steps.  
**Alternatives considered**: Diff-only view; high-level quality summary only.

## Decision 3: Comparison failure returns partial result

**Decision**: If one provider fails, return the successful result and mark the failed provider with an error status.  
**Rationale**: Preserves usable output while making failures explicit, enabling resilient comparisons.  
**Alternatives considered**: Fail the entire comparison; retry then fail.

## Decision 4: DeepSeek OCR runs CPU-only on macOS

**Decision**: Run DeepSeek OCR with CPU-only execution and no CUDA/GPU usage.  
**Rationale**: Matches target hardware constraints (Apple M3 Pro, no CUDA).  
**Alternatives considered**: Require GPU; use a remote OCR service.
