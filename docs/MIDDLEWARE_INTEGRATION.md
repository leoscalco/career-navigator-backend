# Middleware Integration Guide

This document explains how human-in-the-loop and guardrails are implemented in the workflow.

## Architecture

The workflow uses **LangGraph** for orchestration with:
- **Checkpointer** (`MemorySaver`) for state persistence
- **Interrupt mechanism** for human-in-the-loop checkpoints
- **Custom guardrails validation** in nodes

## Human-in-the-Loop

### How It Works

LangGraph's interrupt mechanism pauses the workflow at specific nodes, allowing human review before continuing.

### Checkpoints

1. **After `save_draft`** → `wait_confirmation` node
   - User reviews parsed data
   - Can approve, edit, or reject

2. **After `validate`** → `check_validation` node
   - User reviews validation results
   - Can fix errors and retry

3. **Before `generate_cv`**
   - User approves CV generation

4. **Before `save_product`**
   - User reviews final generated product

### Implementation

```python
# In workflow_graph.py
def _wait_confirmation_node(self, state: WorkflowState) -> WorkflowState:
    """Human-in-the-loop checkpoint."""
    state["current_step"] = "waiting_confirmation"
    
    if not state.get("is_confirmed", False):
        state["needs_human_review"] = True
        # Workflow pauses here
    
    return state
```

### Resuming After Review

```python
# Resume workflow with updated state
config = {
    "configurable": {
        "thread_id": f"user_{user_id}",
    }
}

# Update state with confirmation
state["is_confirmed"] = True

# Continue workflow
final_state = graph.invoke(state, config=config)
```

## Guardrails Validation

### How It Works

Custom validation runs in the `validate` node using LLM-based guardrails.

### Validation Checks

1. **Required fields** presence
2. **Date consistency** (start < end dates)
3. **Logical consistency**
4. **Data completeness**
5. **Format correctness**

### Implementation

```python
# In workflow_graph.py
def _validate_node(self, state: WorkflowState) -> WorkflowState:
    """Validate profile data using guardrails."""
    state["current_step"] = "validating"
    
    # Prepare validation data
    validation_data = {
        "profile": profile.model_dump(),
        "job_experiences": [...],
        "courses": [...],
        "academic_records": [...],
    }
    
    # Run guardrails validation
    prompt = GUARDRAIL_VALIDATION_PROMPT.format(...)
    response = self.llm.generate(prompt)
    validation_report = json.loads(response)
    
    state["validation_report"] = validation_report
    state["is_validated"] = validation_report.get("is_valid", False)
    
    return state
```

### Validation Report Structure

```json
{
    "is_valid": true,
    "errors": [
        {
            "field": "career_goals",
            "error_type": "missing",
            "message": "Career goals are required",
            "severity": "critical"
        }
    ],
    "warnings": [
        {
            "field": "job_experiences",
            "message": "Some job experiences lack achievements"
        }
    ],
    "completeness_score": 0.85,
    "recommendations": [
        "Add more details about your career goals",
        "Include achievements in job experiences"
    ]
}
```

## API Integration

### Workflow Endpoints

1. **Parse CV/LinkedIn**: `POST /workflow/parse-cv`
   - Parses and saves as draft
   - Workflow pauses at `wait_confirmation`

2. **Confirm Draft**: `POST /workflow/confirm-draft/{user_id}`
   - Resumes workflow after human review
   - Continues to validation

3. **Validate**: `POST /workflow/validate/{user_id}`
   - Runs guardrails validation
   - Returns validation report

4. **Generate CV**: `POST /workflow/generate-cv/{user_id}`
   - Generates CV after validation passes
   - Workflow pauses before saving product

## State Persistence

The checkpointer (`MemorySaver`) stores workflow state, allowing:
- **Resume after interruption**: Continue from checkpoint
- **State inspection**: Check current workflow state
- **Error recovery**: Recover from failures

### Thread ID

Each user gets a unique thread ID:
```python
config = {
    "configurable": {
        "thread_id": f"user_{user_id}",
    }
}
```

This allows multiple workflows to run concurrently for different users.

## Future Enhancements

1. **LangChain Agent Integration**: Use `create_agent` for LLM calls within nodes
2. **Advanced Middleware**: Add rate limiting, PII detection, etc.
3. **Persistent Checkpointer**: Use database-backed checkpointer instead of memory
4. **Webhook Integration**: Notify external systems at checkpoints

## References

- [LangGraph Interrupts](https://langchain-ai.github.io/langgraph/how-tos/interrupts/)
- [LangGraph Checkpointing](https://langchain-ai.github.io/langgraph/how-tos/checkpointing/)
- [LangChain Middleware](https://docs.langchain.com/oss/python/langchain/middleware)

