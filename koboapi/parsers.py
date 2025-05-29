"""Parsers for processing Kobo survey data."""

from typing import Dict, List, Any, Optional
from .models import Choice, Question

class SurveyParser:
    """Parser for survey structure and metadata."""

    @staticmethod
    def parse_choices(asset_content: Dict[str, Any]) -> Dict[str, Dict[str, Choice]]:
        """Parse choices from asset content."""
        choice_lists = {}
        sequence = 0

        for choice_data in asset_content.get('choices', []):
            list_name = choice_data['list_name']
            if list_name not in choice_lists:
                choice_lists[list_name] = {}

            label = choice_data.get('label', [''])[0] if 'label' in choice_data else choice_data['name']

            choice = Choice(
                name=choice_data['name'],
                label=label,
                list_name=list_name,
                sequence=sequence
            )

            choice_lists[list_name][choice_data['name']] = choice
            sequence += 1

        return choice_lists

    @staticmethod
    def parse_questions(asset_content: Dict[str, Any], unpack_multiples: bool = False) -> Dict[str, Any]:
        """Parse questions from asset content with improved structure."""
        choices = SurveyParser.parse_choices(asset_content) if unpack_multiples else {}

        sequence = 0
        root_group = {'questions': {}, 'groups': {}}
        group_stack = [root_group]
        current_group = root_group

        for item in asset_content.get('survey', []):
            if SurveyParser._is_group_start(item):
                new_group = SurveyParser._create_group(item, sequence)
                current_group['groups'][SurveyParser._get_name(item)] = new_group
                group_stack.append(current_group)
                current_group = new_group
                sequence += 1

            elif SurveyParser._is_group_end(item):
                current_group = group_stack.pop()

            else:
                question = SurveyParser._create_question(item, sequence, choices, unpack_multiples)
                if question:
                    current_group['questions'][SurveyParser._get_name(item)] = question
                    sequence = question.get('next_sequence', sequence + 1)

        return root_group

    @staticmethod
    def _is_group_start(item: Dict[str, Any]) -> bool:
        return item['type'] in ['begin_group', 'begin_repeat']

    @staticmethod
    def _is_group_end(item: Dict[str, Any]) -> bool:
        return item['type'] in ['end_group', 'end_repeat']

    @staticmethod
    def _get_name(item: Dict[str, Any]) -> Optional[str]:
        return item.get('name') or item.get('$autoname')

    @staticmethod
    def _create_group(item: Dict[str, Any], sequence: int) -> Dict[str, Any]:
        return {
            'label': item.get('label', [''])[0] if 'label' in item else '',
            'sequence': sequence,
            'repeat': item['type'] == 'begin_repeat',
            'questions': {},
            'groups': {}
        }

    @staticmethod
    def _create_question(item: Dict[str, Any], sequence: int, choices: Dict, unpack_multiples: bool) -> Optional[Dict[str, Any]]:
        name = SurveyParser._get_name(item)
        if not name:
            return None

        question = {
            'type': item['type'],
            'sequence': sequence,
            'label': item.get('label', [''])[0] if 'label' in item else name,
            'required': item.get('required', False)
        }

        if 'select_from_list_name' in item:
            question['list_name'] = item['select_from_list_name']

        next_sequence = sequence + 1

        if unpack_multiples and item['type'] == 'select_multiple' and 'select_from_list_name' in item:
            list_name = item['select_from_list_name']
            if list_name in choices:
                question['choices'] = {}
                sorted_choices = sorted(choices[list_name].items(), key=lambda x: x[1].sequence)

                for choice_name, choice in sorted_choices:
                    question['choices'][choice_name] = {
                        'label': choice.label,
                        'type': 'select_multiple_option',
                        'sequence': next_sequence
                    }
                    next_sequence += 1

        question['next_sequence'] = next_sequence
        return question

class ResponseParser:
    """Parser for survey responses."""

    @staticmethod
    def sort_by_submission_time(responses: List[Dict[str, Any]], reverse: bool = False) -> List[Dict[str, Any]]:
        """Sort responses by submission time."""
        return sorted(responses, key=lambda r: r.get('_submission_time', ''), reverse=reverse)

    @staticmethod
    def extract_metadata(response: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from response."""
        meta_prefixes = ('_', 'meta/', 'formhub/', 'simserial', 'phonenumber', 'start', 'end', 'today', 'username', 'deviceid', 'subscriberid')
        return {k: v for k, v in response.items() if k.startswith(meta_prefixes)}

    @staticmethod
    def extract_answers(response: Dict[str, Any]) -> Dict[str, Any]:
        """Extract actual answers from response."""
        meta_prefixes = ('_', 'meta/', 'formhub/', 'simserial', 'phonenumber', 'start', 'end', 'today', 'username', 'deviceid', 'subscriberid')
        return {k: v for k, v in response.items() if not k.startswith(meta_prefixes)}
