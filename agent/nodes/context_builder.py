import os
from agent.state import AgentState, AgentStatus
import structlog

logger = structlog.get_logger()


def run(state: AgentState) -> AgentState:
    """
    Context Builder node:
    Takes RAG retrieved chunks and assembles
    a rich prompt context for Claude.
    Reads:  state.retrieved_chunks, state.plan
    Writes: state.assembled_context, state.status
    """
    logger.info("context_builder_started", session_id=state["session_id"])

    try:
        context_parts = []

        # 1. Add user intent
        context_parts.append(f"Developer Request: {state['cleaned_intent']}")

        # 2. Add plan
        context_parts.append("\nImplementation Plan:")
        for i, step in enumerate(state["plan"], 1):
            context_parts.append(f"  {i}. {step}")

        # 3. Add repo structure summary
        context_parts.append("\nRepository Structure:")
        for folder, files in state["repo_structure"].items():
            if files:
                context_parts.append(f"  {folder}/: {', '.join(files)}")

        # 4. Add RAG retrieved chunks
        if state["retrieved_chunks"]:
            context_parts.append("\nRelevant Code From Repository:")
            for chunk in state["retrieved_chunks"]:
                context_parts.append(
                    f"\n--- {chunk['file_path']} "
                    f"({chunk['chunk_type']}: {chunk['chunk_name']}) ---"
                )
                context_parts.append(chunk["content"])
        else:
            context_parts.append("\nNo existing relevant code found.")

        assembled = "\n".join(context_parts)

        logger.info(
            "context_built",
            chunks=len(state["retrieved_chunks"]),
            context_length=len(assembled)
        )

        return {
            **state,
            "assembled_context": assembled,
            "status":            AgentStatus.GENERATING,
            "logs":              state["logs"] + [
                f"Context built from {len(state['retrieved_chunks'])} RAG chunks"
            ]
        }

    except Exception as e:
        logger.error("context_builder_failed", error=str(e))
        return {
            **state,
            "status":        AgentStatus.FAILED,
            "error_message": f"Context builder failed: {str(e)}"
        }
