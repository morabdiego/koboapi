"""Main wrapper for KoboAPI interactions."""

from typing import Any, Dict, List, Optional
from .http_client import HTTPClient

class Kobo:
    """Extracts collected data from KoBoToolbox with improved architecture."""

    # Predefined endpoints
    ENDPOINTS = {
        'default': 'https://kf.kobotoolbox.org/',
        'humanitarian': 'https://kc.humanitarianresponse.info/'
    }

    def __init__(self, token: str, endpoint: str = 'default', debug: bool = False) -> None:
        """Initialize the Kobo client.

        Args:
            token: Your authentication token
            endpoint: The KoBoToolbox API endpoint. Options:
                    - 'default': https://kf.kobotoolbox.org/ (default)
                    - 'humanitarian': https://kc.humanitarianresponse.info/
                    - Custom URL string
            debug: Enable debugging output
        """
        # Resolve endpoint
        if endpoint in self.ENDPOINTS:
            resolved_endpoint = self.ENDPOINTS[endpoint]
        else:
            resolved_endpoint = endpoint

        self.client = HTTPClient(token, resolved_endpoint, debug)
        self.debug = debug

    def list_assets(self) -> List[Dict[str, Any]]:
        """List all assets as dictionaries."""
        response = self.client.get('/assets.json')
        return response.get('results', [])

    def list_uid(self) -> Dict[str, str]:
        """Return a dictionary mapping asset names to their UIDs."""
        assets = self.list_assets()
        return {asset.get('name', ''): asset.get('uid', '') for asset in assets}

    def get_asset(self, asset_uid: str) -> Dict[str, Any]:
        """Get detailed asset information."""
        return self.client.get(f'/assets/{asset_uid}.json')

    def get_data(self,
                asset_uid: str,
                query: Optional[str] = None,
                start: Optional[int] = None,
                limit: Optional[int] = None,
                submitted_after: Optional[str] = None) -> Dict[str, Any]:
        """Get survey data with improved parameter handling."""
        params = {}

        if query:
            params['query'] = query
            if self.debug and submitted_after:
                print("Ignoring 'submitted_after' because 'query' is specified.")
        elif submitted_after:
            params['query'] = f'{{"_submission_time": {{"$gt": "{submitted_after}"}}}}'

        if start is not None:
            params['start'] = start
        if limit is not None:
            params['limit'] = limit

        return self.client.get(f'/assets/{asset_uid}/data.json', params)

    def get_choices(self, asset: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Get choices from asset content."""
        content = asset.get('content', {})
        choice_lists = {}
        sequence = 0

        for choice_data in content.get('choices', []):
            list_name = choice_data['list_name']
            if list_name not in choice_lists:
                choice_lists[list_name] = {}

            label = choice_data.get('label', [''])[0] if 'label' in choice_data else choice_data['name']

            choice_lists[list_name][choice_data['name']] = {
                'label': label,
                'sequence': sequence
            }
            sequence += 1

        return choice_lists

    def get_questions(self, asset: Dict[str, Any], unpack_multiples: bool = False) -> Dict[str, Any]:
        """Get questions from asset content."""
        content = asset.get('content', {})
        choices = self.get_choices(asset) if unpack_multiples else {}

        sequence = 0
        root_group = {'questions': {}, 'groups': {}}
        group_stack = [root_group]
        current_group = root_group

        for item in content.get('survey', []):
            if item['type'] in ['begin_group', 'begin_repeat']:
                new_group = {
                    'label': item.get('label', [''])[0] if 'label' in item else '',
                    'sequence': sequence,
                    'repeat': item['type'] == 'begin_repeat',
                    'questions': {},
                    'groups': {}
                }
                name = item.get('name') or item.get('$autoname')
                current_group['groups'][name] = new_group
                group_stack.append(current_group)
                current_group = new_group
                sequence += 1

            elif item['type'] in ['end_group', 'end_repeat']:
                current_group = group_stack.pop()

            else:
                name = item.get('name') or item.get('$autoname')
                if name:
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
                            sorted_choices = sorted(choices[list_name].items(),
                                                  key=lambda x: x[1]['sequence'])

                            for choice_name, choice in sorted_choices:
                                question['choices'][choice_name] = {
                                    'label': choice['label'],
                                    'type': 'select_multiple_option',
                                    'sequence': next_sequence
                                }
                                next_sequence += 1

                    current_group['questions'][name] = question
                    sequence = next_sequence

        return root_group
