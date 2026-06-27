from langgraph.graph import StateGraph, END

from orchestrator.state import DebateState
from agents.models import AgentMessage


def _build_graph(provider: str | None = None, api_key: str | None = None):
    from agents.base import build_llm
    from agents.proponent import ProponentAgent
    from agents.critic import CriticAgent
    from agents.analyst import AnalystAgent
    from agents.fact_checker import FactCheckerAgent
    from agents.judge import JudgeAgent

    llm = build_llm(provider, api_key)
    proponent_agent = ProponentAgent(llm)
    critic_agent = CriticAgent(llm)
    analyst_agent = AnalystAgent(llm)
    fact_checker_agent = FactCheckerAgent(llm)
    judge_agent = JudgeAgent(llm)

    def proponent_node(state: DebateState):
        messages = [AgentMessage(**m) for m in state.get("transcript", [])]
        response = proponent_agent.respond(messages, state["topic"])
        new_msg = {"role": proponent_agent.role, "content": response, "round": state["round"]}
        return {"transcript": state.get("transcript", []) + [new_msg]}

    def critic_node(state: DebateState):
        messages = [AgentMessage(**m) for m in state.get("transcript", [])]
        response = critic_agent.respond(messages, state["topic"])
        new_msg = {"role": critic_agent.role, "content": response, "round": state["round"]}
        return {"transcript": state.get("transcript", []) + [new_msg]}

    def analyst_node(state: DebateState):
        messages = [AgentMessage(**m) for m in state.get("transcript", [])]
        response = analyst_agent.respond(messages, state["topic"])
        new_msg = {"role": analyst_agent.role, "content": response, "round": state["round"]}
        return {"transcript": state.get("transcript", []) + [new_msg]}

    def fact_checker_node(state: DebateState):
        messages = [AgentMessage(**m) for m in state.get("transcript", [])]
        response = fact_checker_agent.respond(messages, state["topic"])
        new_msg = {"role": fact_checker_agent.role, "content": response, "round": state["round"]}
        # round is incremented here so should_continue sees the updated value
        return {
            "transcript": state.get("transcript", []) + [new_msg],
            "round": state["round"] + 1,
        }

    def voting_node(state: DebateState):
        messages = [AgentMessage(**m) for m in state.get("transcript", [])]
        judgment = judge_agent.judge(messages, state["topic"])
        votes = {
            "accuracy": judgment.get("accuracy", 0),
            "balance": judgment.get("balance", 0),
            "depth": judgment.get("depth", 0),
            "reasoning_quality": judgment.get("reasoning_quality", 0),
        }
        return {
            "votes": votes,
            "winner": judgment.get("winner", ""),
            "verdict": judgment.get("verdict", ""),
            "status": "done",
        }

    def should_continue(state: DebateState):
        if state["round"] <= state["rounds"]:
            return "continue"
        return "voting"

    workflow = StateGraph(DebateState)
    workflow.add_node("proponent_node", proponent_node)
    workflow.add_node("critic_node", critic_node)
    workflow.add_node("analyst_node", analyst_node)
    workflow.add_node("fact_checker_node", fact_checker_node)
    workflow.add_node("voting_node", voting_node)

    workflow.set_entry_point("proponent_node")
    workflow.add_edge("proponent_node", "critic_node")
    workflow.add_edge("critic_node", "analyst_node")
    workflow.add_edge("analyst_node", "fact_checker_node")
    workflow.add_conditional_edges(
        "fact_checker_node",
        should_continue,
        {"continue": "proponent_node", "voting": "voting_node"},
    )
    workflow.add_edge("voting_node", END)

    return workflow.compile()


def run_debate(
    topic: str,
    rounds: int = 3,
    provider: str | None = None,
    api_key: str | None = None,
) -> DebateState:
    graph = _build_graph(provider, api_key)
    initial_state = DebateState(
        topic=topic,
        rounds=rounds,
        round=1,
        transcript=[],
        votes={},
        winner="",
        verdict="",
        status="debating",
    )
    return graph.invoke(initial_state)
