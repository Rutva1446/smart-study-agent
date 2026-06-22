import os
from google.adk.tools import ToolContext
from pypdf import PdfReader

def read_syllabus_file(file_path: str, tool_context: ToolContext) -> dict:
    """Reads a local syllabus file (PDF, TXT, or MD) and returns the raw content.

    Args:
        file_path: The absolute or relative path to the local syllabus file.

    Returns:
        A dictionary with the file reading status and content preview.
    """
    if not os.path.exists(file_path):
        return {
            "status": "error",
            "message": f"File not found at: {file_path}. Please make sure the path is correct and the file exists."
        }

    try:
        _, ext = os.path.splitext(file_path.lower())
        text = ""

        if ext == ".pdf":
            reader = PdfReader(file_path)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        else:
            # Default to text file reading
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()

        text = text.strip()
        if not text:
            return {"status": "error", "message": "The file was successfully read but appears to be empty."}

        # Store in session state for agent reference
        tool_context.state["syllabus_raw"] = text

        return {
            "status": "success",
            "file_path": file_path,
            "char_count": len(text),
            "preview": text[:800] + "\n... [TRUNCATED] ..." if len(text) > 800 else text
        }
    except Exception as e:
        return {"status": "error", "message": f"An error occurred while reading the file: {str(e)}"}


def save_syllabus_topics(topics: list[str], tool_context: ToolContext) -> dict:
    """Saves the extracted list of syllabus topics to the study progress tracker.

    Args:
        topics: A list of main topic names/titles extracted from the syllabus.

    Returns:
        A dictionary confirming the topics are saved.
    """
    tool_context.state["syllabus_topics"] = topics
    
    # Initialize progress dict for these topics if not already set
    progress = tool_context.state.get("progress", {})
    for topic in topics:
        if topic not in progress:
            progress[topic] = "Not Started"
    tool_context.state["progress"] = progress

    return {
        "status": "success",
        "message": f"Saved {len(topics)} syllabus topics to progress tracker.",
        "topics": topics
    }


def save_study_plan(plan: str, tool_context: ToolContext) -> dict:
    """Saves the generated exam preparation study plan/schedule.

    Args:
        plan: The markdown or text description of the exam preparation study plan.

    Returns:
        A dictionary confirming the study plan is saved.
    """
    tool_context.state["study_plan"] = plan
    return {
        "status": "success",
        "message": "Study plan saved successfully."
    }


def update_topic_progress(topic_name: str, status: str, tool_context: ToolContext) -> dict:
    """Updates the study progress status of a specific syllabus topic.

    Args:
        topic_name: The name of the topic to update.
        status: The new status of the topic (must be one of: 'Not Started', 'In Progress', 'Completed').

    Returns:
        A dictionary showing the updated progress for the topic.
    """
    valid_statuses = ["Not Started", "In Progress", "Completed"]
    if status not in valid_statuses:
        return {
            "status": "error",
            "message": f"Invalid status '{status}'. Must be one of {valid_statuses}."
        }

    progress = tool_context.state.get("progress", {})
    
    # Find matching topic case-insensitively if not found exactly
    target_topic = topic_name
    if topic_name not in progress:
        found = False
        for t in progress.keys():
            if t.lower() == topic_name.lower():
                target_topic = t
                found = True
                break
        if not found:
            # If not in syllabus, add it dynamically
            progress[topic_name] = status
            target_topic = topic_name
    
    progress[target_topic] = status
    tool_context.state["progress"] = progress

    return {
        "status": "success",
        "topic": target_topic,
        "new_status": status,
        "all_progress": progress
    }


def record_quiz_result(topic_name: str, score: int, total_questions: int, tool_context: ToolContext) -> dict:
    """Records the results of a self-assessment quiz for a topic.

    Args:
        topic_name: The topic the quiz was on.
        score: The number of correct answers.
        total_questions: The total number of questions in the quiz.

    Returns:
        A dictionary confirming the quiz result registration.
    """
    quizzes = tool_context.state.get("quizzes_taken", [])
    result = {
        "topic": topic_name,
        "score": score,
        "total": total_questions,
        "percentage": round((score / total_questions) * 100, 2) if total_questions > 0 else 0
    }
    quizzes.append(result)
    tool_context.state["quizzes_taken"] = quizzes

    # If they scored 80% or higher, suggest updating progress to Completed
    auto_complete = result["percentage"] >= 80

    return {
        "status": "success",
        "quiz_result": result,
        "suggest_completion": auto_complete
    }


def get_study_progress(tool_context: ToolContext) -> dict:
    """Retrieves the current state of study progress, study plan, and quizzes taken.

    Returns:
        A dictionary containing the current syllabus topics, completion status, saved study plan, and quiz history.
    """
    return {
        "status": "success",
        "syllabus_topics": tool_context.state.get("syllabus_topics", []),
        "progress": tool_context.state.get("progress", {}),
        "study_plan": tool_context.state.get("study_plan", "No study plan created yet."),
        "quizzes_taken": tool_context.state.get("quizzes_taken", [])
    }
