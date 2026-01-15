# Data Model: Resilient Configurable Architecture

**Created**: 2026-01-14  
**Purpose**: Define entities, relationships, and constraints for configuration-driven modules

## Entities

### Module

Represents a pluggable implementation for a processing stage.

- **Fields**: module_id, name, stage_id, capability_contract_id, status, is_fallback, metadata
- **Relationships**: belongs to `ProcessingStage`, references `CapabilityContract`
- **Constraints**: Only one active fallback module per stage

### Module Configuration

Versioned selection of modules and settings across stages.

- **Fields**: config_id, version, status, created_by, created_at, activated_at, summary
- **Relationships**: has many `ModuleSelection`, has many `ConfigurationChangeEvent`
- **Constraints**: Exactly one active configuration at any time; new versions do not overwrite prior versions

### Module Selection

Mapping of a stage to a specific module within a configuration.

- **Fields**: selection_id, config_id, stage_id, module_id, settings
- **Relationships**: belongs to `ModuleConfiguration`, `ProcessingStage`, and `Module`
- **Constraints**: One selection per stage per configuration

### Capability Contract

Defines required inputs, outputs, and behavioral guarantees for a stage.

- **Fields**: contract_id, name, inputs, outputs, guarantees, constraints
- **Relationships**: referenced by `Module` and `ProcessingStage`
- **Constraints**: Selected modules must declare a matching contract

### Fallback Policy

Rules that define alternative behavior when a module fails or is unavailable.

- **Fields**: policy_id, stage_id, fallback_module_id, trigger_conditions, actions
- **Relationships**: belongs to `ProcessingStage`, references `Module`
- **Constraints**: Fallback module must satisfy the stage capability contract

### Processing Stage

Discrete step in the invoice workflow.

- **Fields**: stage_id, name, order, capability_contract_id, is_required
- **Relationships**: has many `Module`, `ModuleSelection`, and `FallbackPolicy`
- **Constraints**: Required stages must have a module selection in active config

### Configuration Change Event

Audit record of configuration actions.

- **Fields**: event_id, config_id, action, actor, result, message, created_at
- **Relationships**: belongs to `ModuleConfiguration`
- **Constraints**: Records all activation, rollback, and validation results

## State Transitions

### Module Configuration

- **Draft** → **Validated** → **Active** → **Superseded**
- **Active** → **Rolled Back** (when rollback action creates a new active version)
- **Validated** → **Rejected** (when compatibility checks fail)

## Data Integrity Rules

- Configurations can only be activated if all required stages have valid selections.
- Stage selections must reference modules that match the stage capability contract.
- Activation is queued while processing is active; only one activation is pending at a time.
