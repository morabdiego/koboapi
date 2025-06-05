"""Data models for KoboAPI."""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional

@dataclass
class Question:
    """Represents a survey question."""
    name: str
    type: str
    label: str
    sequence: int
    required: bool = False
    list_name: Optional[str] = None
    path: str = ""

    @property
    def original_name(self) -> str:
        """Get the original question name without path."""
        return self.name.split('/')[-1] if '/' in self.name else self.name

@dataclass
class RepeatGroup:
    """Represents a repeat group in the survey."""
    name: str
    label: str
    sequence: int
    path: str = ""
    level: int = 0

    @property
    def simple_name(self) -> str:
        """Get the simple name without path."""
        return self.name.split('/')[-1] if '/' in self.name else self.name

    @property
    def parent_path(self) -> Optional[str]:
        """Get the parent path."""
        return '/'.join(self.name.split('/')[:-1]) if '/' in self.name else None

@dataclass
class SurveyStructure:
    """Represents the complete survey structure."""
    questions: Dict[str, Question]
    repeat_groups: Dict[str, RepeatGroup]

    def get_questions_by_type(self, question_type: str) -> Dict[str, Question]:
        """Get all questions of a specific type."""
        return {name: q for name, q in self.questions.items() if q.type == question_type}

    def get_questions_by_path(self, path: str = "") -> Dict[str, Question]:
        """Get all questions in a specific path."""
        return {name: q for name, q in self.questions.items() if q.path == path}
