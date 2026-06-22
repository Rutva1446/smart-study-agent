# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

import os
import google.auth

# Import Memory Bank tools and callback context
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.adk.agents.callback_context import CallbackContext

# Import our custom tools
from app.tools import (
    read_syllabus_file,
    save_syllabus_topics,
    save_study_plan,
    update_topic_progress,
    record_quiz_result,
    get_study_progress,
)

from dotenv import load_dotenv
from google.auth.exceptions import DefaultCredentialsError

load_dotenv()

use_vertex = os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "True").lower() == "true"

if use_vertex:
    try:
        _, project_id = google.auth.default()
        os.environ["GOOGLE_CLOUD_PROJECT"] = project_id or ""
        os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
    except DefaultCredentialsError:
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"



# Callback to persist memories to Memory Bank
async def generate_memories_callback(callback_context: CallbackContext):
    """Sends the session's events to Memory Bank for memory generation."""
    await callback_context.add_session_to_memory()
    return None


INSTRUCTION = """You are a Smart Study Assistant AI Agent. Your goal is to help students study smarter by:
1. Finding syllabus topics from local files:
   - Ask the student to provide the absolute or relative file path to their syllabus (PDF, TXT, or MD).
   - Use the `read_syllabus_file` tool to read the file and extract the raw syllabus.
   - Analyze the raw syllabus, extract the main topics, and suggest them to the student.
   - Once the student agrees on the topics, call the `save_syllabus_topics` tool to save them.

2. Planning exam preparation:
   - Ask the student about their target exam date, study hours per day, and any topics they find difficult.
   - Create a realistic study plan/schedule.
   - Use the `save_study_plan` tool to save the plan.

3. Identifying important questions:
   - For any topic, analyze the syllabus details and suggest key concepts and sample/important questions.

4. Tracking study progress:
   - Provide status updates of the student's progress using the `get_study_progress` tool.
   - Update the status of topics (e.g., 'Completed', 'In Progress') using the `update_topic_progress` tool when the student completes them or passes a quiz.

5. Creating quizzes for self-assessment:
   - Offer to test the student's knowledge on specific topics.
   - Generate multiple-choice or short-answer questions one-by-one.
   - Evaluate the student's answers, provide constructive feedback, and call `record_quiz_result` to save the score.
   - If they score 80% or more, suggest marking the topic as "Completed".

Rules and Safety Constraints:
- Be encouraging and academic.
- NEVER give direct exam answers to cheat on assignments. Instead, guide the user through concepts step-by-step.
- Keep responses clear, concise, and structured.
- Always use the tools to save plans and progress so that they are remembered across sessions using your Memory Bank.
"""

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=INSTRUCTION,
    tools=[
        read_syllabus_file,
        save_syllabus_topics,
        save_study_plan,
        update_topic_progress,
        record_quiz_result,
        get_study_progress,
        PreloadMemoryTool(),
    ],
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)

