"""
Prompts package for the Text-to-SQL service.

This package contains all prompts used throughout the application:
- system.py: System prompts for different modes
- user.py: User message templates
- validation.py: SQL validation prompts
- helpers.py: Utility prompts for explanations and test data
"""

from .helpers import (
    SIMILAR_QUESTIONS_PROMPT,
    SQL_EXPLANATION_PROMPT,
    TEST_DATA_PROMPT,
    get_explanation_prompt,
    get_similar_questions_prompt,
    get_test_data_prompt,
)
from .system import (
    READONLY_TEXT_TO_SQL_SYSTEM_PROMPT,
    TEXT_TO_SQL_SYSTEM_PROMPT,
    get_text_to_sql_prompt,
)
from .user import (
    BASIC_TEXT_TO_SQL_USER_PROMPT,
    READONLY_TEXT_TO_SQL_USER_PROMPT,
    get_user_prompt,
)
from .validation import (
    READONLY_SQL_VALIDATION_PROMPT,
    SQL_VALIDATION_PROMPT,
    get_validation_prompt,
)

__all__ = [
    # System prompts
    "get_text_to_sql_prompt",
    "TEXT_TO_SQL_SYSTEM_PROMPT",
    "READONLY_TEXT_TO_SQL_SYSTEM_PROMPT",
    # User prompts
    "get_user_prompt",
    "BASIC_TEXT_TO_SQL_USER_PROMPT",
    "READONLY_TEXT_TO_SQL_USER_PROMPT",
    # Validation prompts
    "get_validation_prompt",
    "SQL_VALIDATION_PROMPT",
    "READONLY_SQL_VALIDATION_PROMPT",
    # Helper prompts
    "get_explanation_prompt",
    "get_similar_questions_prompt",
    "get_test_data_prompt",
    "SQL_EXPLANATION_PROMPT",
    "SIMILAR_QUESTIONS_PROMPT",
    "TEST_DATA_PROMPT",
]
