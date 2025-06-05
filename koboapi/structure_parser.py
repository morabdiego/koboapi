"""Parser for XLSForm structure."""

from typing import Dict, List, Any, Optional
from .models import Question, RepeatGroup, SurveyStructure

class StructureParser:
    """Parses XLSForm JSON structure into structured models."""

    def __init__(self, xlsform_json: Dict[str, Any]):
        self.xlsform = xlsform_json
        self._sequence = 0

    def parse(self) -> SurveyStructure:
        """Parse the XLSForm structure."""
        questions = {}
        repeat_groups = {}

        self._parse_level(
            self.xlsform.get('questions', {}),
            self.xlsform.get('groups', {}),
            questions,
            repeat_groups,
            prefix=""
        )

        return SurveyStructure(questions=questions, repeat_groups=repeat_groups)

    def _parse_level(self, questions: Dict, groups: Dict,
                    all_questions: Dict[str, Question],
                    all_groups: Dict[str, RepeatGroup],
                    prefix: str) -> None:
        """Parse questions and groups at current level."""
        # Parse questions
        for q_name, q_data in questions.items():
            full_name = f"{prefix}{q_name}" if prefix else q_name
            question = Question(
                name=full_name,
                type=q_data.get('type', ''),
                label=q_data.get('label', q_name),
                sequence=q_data.get('sequence', self._sequence),
                required=q_data.get('required', False),
                list_name=q_data.get('list_name'),
                path=prefix.rstrip('/')
            )
            all_questions[full_name] = question
            self._sequence += 1

        # Parse groups
        for g_name, g_data in groups.items():
            full_name = f"{prefix}{g_name}" if prefix else g_name
            new_prefix = f"{full_name}/"

            if g_data.get('repeat', False):
                repeat_group = RepeatGroup(
                    name=full_name,
                    label=g_data.get('label', g_name),
                    sequence=g_data.get('sequence', self._sequence),
                    path=prefix.rstrip('/'),
                    level=full_name.count('/')
                )
                all_groups[full_name] = repeat_group
                self._sequence += 1

            # Recursively parse nested content
            if 'questions' in g_data or 'groups' in g_data:
                self._parse_level(
                    g_data.get('questions', {}),
                    g_data.get('groups', {}),
                    all_questions,
                    all_groups,
                    new_prefix
                )
