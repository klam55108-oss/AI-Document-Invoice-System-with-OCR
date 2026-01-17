# Feature Specification: Switchable OCR Providers

**Feature Branch**: `001-ocr-switch-options`  
**Created**: Jan 15, 2026  
**Status**: Draft  
**Input**: User description: "replace paddleOCR with deepseek-OCR, so I can switch btw the 2 ocr options to compare the process result"

## Clarifications

### Session 2026-01-15

- Q: What comparison output should users see? → A: Side-by-side outputs showing extracted text and key fields for both providers.
- Q: How should comparison behave if one provider fails? → A: Return the successful provider result and mark the failed one with an error status.
- Q: Who can change the default/enabled OCR providers? → A: Admin-only.
- Q: How should default provider apply during normal runs? → A: Default provider is used unless user explicitly selects a different enabled provider.
- Q: What is the comparison scope per request? → A: Comparison is limited to a single invoice at a time.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Choose an OCR provider per run (Priority: P1)

As a user processing invoices, I want to select the OCR provider for a run so I can see the extracted results from a specific engine.

**Why this priority**: Direct provider selection is required to compare outputs and validate accuracy.

**Independent Test**: Process a single invoice by selecting a provider and confirm the OCR results are generated and labeled with that provider.

**Acceptance Scenarios**:

1. **Given** an invoice is ready for OCR, **When** I select DeepSeek OCR and start processing, **Then** I receive OCR results labeled as DeepSeek OCR.
2. **Given** an invoice is ready for OCR, **When** I select PaddleOCR and start processing, **Then** I receive OCR results labeled as PaddleOCR.

---

### User Story 2 - Compare two OCR providers on the same input (Priority: P2)

As a user validating OCR quality, I want to compare results from two providers on the same invoice to understand differences.

**Why this priority**: Comparison enables evidence-based selection of the best OCR option.

**Independent Test**: Run a single invoice through both providers and verify a comparison output is produced.

**Acceptance Scenarios**:

1. **Given** an invoice is ready for OCR, **When** I request a comparison between two providers, **Then** the system produces side-by-side results showing extracted text and key fields for both providers.

---

### User Story 3 - Set default and allowed providers (Priority: P3)

As a system administrator, I want to define a default OCR provider and enable or disable providers so users follow approved options.

**Why this priority**: Controlled defaults reduce user friction and ensure consistency across processing.

**Independent Test**: Configure a default provider and confirm a run without explicit selection uses the default.

**Acceptance Scenarios**:

1. **Given** a default provider is configured, **When** a user starts OCR without selecting a provider, **Then** the default provider is used.
2. **Given** a default provider is configured and other providers are enabled, **When** a user selects a different provider, **Then** the selected provider is used for that run.

---

### Edge Cases

- What happens when a selected provider is unavailable at runtime?
- How does the system handle a comparison request if one provider fails?
- What happens when an invoice format is unsupported by a selected provider?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Users MUST be able to select an OCR provider for each processing request.
- **FR-002**: The system MUST support at least two OCR providers: PaddleOCR and DeepSeek OCR.
- **FR-003**: The system MUST record the provider used with every OCR result.
- **FR-004**: The system MUST allow configuring the default provider and the enabled provider list without code changes.
- **FR-009**: Only administrators MUST be allowed to change the default provider or enabled provider list.
- **FR-005**: The system MUST allow running the same input through two providers in a single comparison workflow.
- **FR-006**: The system MUST provide a clear error outcome when a selected provider is unavailable or fails, without corrupting existing results.
- **FR-007**: The system MUST provide side-by-side comparison output showing extracted text and key fields for both providers.
- **FR-008**: If one provider fails in a comparison, the system MUST return the successful provider result and mark the failed provider with an error status.
- **FR-010**: The system MUST use the default provider unless a user explicitly selects a different enabled provider.
- **FR-011**: The system MUST limit OCR comparison requests to a single invoice at a time.

### Key Entities *(include if feature involves data)*

- **OCR Provider**: Available OCR option with name, availability status, and supported input formats.
- **OCR Result**: Extracted text and metadata tied to an input and provider.
- **OCR Comparison**: A comparison record linking two provider results for the same input with a summary of differences.

## Assumptions

- Users have access to invoices or documents suitable for OCR processing.
- Comparing providers is limited to two providers per comparison run.
- Provider comparison is limited to a single invoice per request.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can complete an OCR run with a selected provider in under 2 minutes for a typical single-invoice input.
- **SC-002**: 95% of single-invoice OCR requests complete within 30 seconds.
- **SC-003**: 100% of OCR results include the provider label.
- **SC-004**: At least 90% of comparison requests generate both provider results without manual retries.
- **SC-005**: 90% of users can complete a provider comparison on the first attempt.
- **SC-006**: Resource usage per OCR request remains under 512 MB.
