from langgraph.graph import StateGraph, END
from agent.state import AgentState, AgentStatus
from agent.nodes import (
    planner,
    retrieval,
    context_builder,
    code_generator,
    validator,
    decision,
    github_commit
)
import structlog

logger = structlog.get_logger()


def route_after_decision(state: AgentState) -> str:
    '''
    Tells LangGraph which edge to follow after decision node.
    Returns: commit | retry | fail
    '''
    return decision.route(state)


def build_graph() -> StateGraph:
    '''
    Builds and compiles the full LangGraph agent.
    Call this once at startup.
    '''
    graph = StateGraph(AgentState)

    # Register all nodes
    graph.add_node('planner',         planner.run)
    graph.add_node('retrieval',       retrieval.run)
    graph.add_node('context_builder', context_builder.run)
    graph.add_node('code_generator',  code_generator.run)
    graph.add_node('validator',       validator.run)
    graph.add_node('decision',        decision.run)
    graph.add_node('github_commit',   github_commit.run)

    # Linear edges
    graph.add_edge('planner',         'retrieval')
    graph.add_edge('retrieval',       'context_builder')
    graph.add_edge('context_builder', 'code_generator')
    graph.add_edge('code_generator',  'validator')
    graph.add_edge('validator',       'decision')

    # Conditional edge at decision node
    graph.add_conditional_edges(
        'decision',
        route_after_decision,
        {
            'retry':  'code_generator',
            'commit': 'github_commit',
            'fail':   END
        }
    )

    graph.add_edge('github_commit', END)

    # First node to run
    graph.set_entry_point('planner')

    return graph.compile()


# Compiled graph — imported by worker/tasks.py
agent_graph = build_graph()
