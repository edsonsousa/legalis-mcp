"""MCP tool for AI-guided case intake interview."""

from typing import Any, Optional

from ..client import get_client


async def run_interview(
    case_id: str,
    action: str,
    answers: Optional[dict] = None,
    session_id: Optional[str] = None,
) -> dict:
    """
    Interact with the AI-guided case intake interview.

    Actions:
    - "start": Begin a new interview session for the case.
    - "answer": Submit answers to the current interview questions.
    - "complete": Finalize the interview and save context.
    - "status": Get current interview status.

    Args:
        case_id: UUID of the case.
        action: One of "start", "answer", "complete", "status".
        answers: Dictionary of question_id → answer (required when action="answer").
        session_id: Interview session ID (required for "answer" and "complete").
    """
    client = get_client()

    if action == "start":
        return await client.post(
            "/api/interview/start",
            json={"case_id": case_id},
        )

    elif action == "answer":
        if not answers or not session_id:
            raise ValueError("answers and session_id are required for action='answer'")
        return await client.post(
            "/api/interview/answers",
            json={"session_id": session_id, "answers": answers, "case_id": case_id},
        )

    elif action == "complete":
        if not session_id:
            raise ValueError("session_id is required for action='complete'")
        return await client.post(
            "/api/interview/complete",
            json={"session_id": session_id, "case_id": case_id},
        )

    elif action == "status":
        return await client.get(
            "/api/interview",
            params={"case_id": case_id},
        )

    else:
        raise ValueError(
            f"Unknown action '{action}'. Must be one of: start, answer, complete, status."
        )
