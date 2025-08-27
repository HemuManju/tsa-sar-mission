import os

try:
    import google.generativeai as genai
    _GENAI_AVAILABLE = True
except Exception as _e:
    _GENAI_AVAILABLE = False
    _GENAI_IMPORT_ERR = _e

__all__ = ["get_sar_advice"]

def get_sar_advice(user_question: str, situation: str = "", history: list[str] = None, model_name: str = "gemini-1.5-flash") -> str:
    """
    Query Gemini for SAR mission guidance based on a user's question.
    Returns a short suggestion string or an informative error.
    
    Args:
        user_question (str): The player's question, e.g., "Should I go north or south?"
        situation (str): The current game situation description.
        history (list[str]): Optional list of previous conversation lines.
        model_name (str): The Gemini model to use, e.g., "gemini-1.5-flash".
    
    Returns:
        str: The AI-generated response or an error message.
    """
    if not _GENAI_AVAILABLE:
        return f"Error: google-generativeai is not installed ({_GENAI_IMPORT_ERR})."

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return "Error: GOOGLE_API_KEY is not set. In PowerShell: $env:GOOGLE_API_KEY = \"YOUR_KEY\""

    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        return f"Error configuring Gemini: {e}"

    prompt = (
        "You are a SAR (Search and Rescue) mission assistant in a grid-based game. "
        "The player is navigating a grid to find victims (colored red, yellow, purple) while avoiding walls. "
        "Answer the player's question to help them make smart moves, adhering to these rules:\n\n"
        "RULES:\n"
        "1) Never reveal exact tile coordinates or step counts.\n"
        "2) Describe nearby structure if relevant: walls, bottlenecks, open corridors, dead-ends, safer channels.\n"
        "3) Prioritize victims: RED > YELLOW > PURPLE.\n"
        "4) Balance risk vs payoff; avoid trapped pockets.\n"
        "5) Be specific but non-prescriptive: e.g., 'edge of the open corridor toward the north side'.\n"
        "6) If the 5x5 local view is mentioned as cramped, suggest repositioning to a more open area.\n"
        "7) Keep answers to 1–3 lines, followed by one brief reasoning line.\n\n"
    )

    if history:
        prompt += "Previous conversation:\n" + "\n".join(history) + "\n\n"
    
    prompt += f"Current situation: {situation}\n\n"
    prompt += f"Player's question: {user_question}\n\n"
    prompt += "If the question is vague or lacks context, provide general advice based on the SAR mission goals."

    try:
        model = genai.GenerativeModel(model_name)
        resp = model.generate_content(prompt)
        return (resp.text or "").strip() or "No response text returned."
    except Exception as e:
        return f"Error querying Gemini: {e}"