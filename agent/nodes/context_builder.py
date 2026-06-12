import os
from agent.state import AgentState, AgentStatus
from agent.streaming.event_bus import publish_event
from agent.streaming.events import StreamEvent, EventType
import structlog

logger = structlog.get_logger()


def run(state: AgentState) -> AgentState:
    logger.info("context_builder_started", session_id=state["session_id"])

    publish_event(StreamEvent(
        event_type=EventType.CONTEXT_STARTED,
        session_id=state["session_id"],
        message="Building context from retrieved code...",
        data={}
    ))

    try:
        context_parts = []
        context_parts.append(f"Developer Request: {state['cleaned_intent']}")
        context_parts.append("\nImplementation Plan:")
        for i, step in enumerate(state["plan"], 1):
            context_parts.append(f"  {i}. {step}")

        context_parts.append("\nRepository Structure:")
        for folder, files in state["repo_structure"].items():
            if files:
                context_parts.append(f"  {folder}/: {', '.join(files)}")

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

        publish_event(StreamEvent(
            event_type=EventType.CONTEXT_COMPLETED,
            session_id=state["session_id"],
            message=f"Context built from {len(state['retrieved_chunks'])} chunks",
            data={"context_length": len(assembled)}
        ))

        logger.info("context_built", chunks=len(state["retrieved_chunks"]))

        return {
            **state,
            "assembled_context": assembled,
            "status":            AgentStatus.GENERATING,
            "logs":              state["logs"] + [f"Context built from {len(state['retrieved_chunks'])} RAG chunks"]
        }

    except Exception as e:
        logger.error("context_builder_failed", error=str(e))

        publish_event(StreamEvent(
            event_type=EventType.AGENT_FAILED,
            session_id=state["session_id"],
            message=f"Context building failed: {str(e)}",
            data={"error": str(e)}
        ))

        return {
            **state,
            "status":        AgentStatus.FAILED,
            "error_message": f"Context builder failed: {str(e)}"
        }
