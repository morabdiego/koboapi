"""Main wrapper for KoboAPI interactions."""

import os
from typing import Any, Dict, List, Optional
import pandas as pd
from collections import defaultdict
from .client import Client
from .builder import XLSFormDataStructureBuilder, create_dataframes_from_submissions, get_columns_by_level

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

        self.client = Client(token, resolved_endpoint, debug)
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
                'name': choice_data['name'],
                'label': label,
                'list_name': list_name,
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

    def download_xlsform(self, asset_uid: str, download_dir: str = "src") -> str:
        """Download the XLS form for a given asset.

        Args:
            asset_uid: The UID of the asset to download
            download_dir: Directory to save the file (default: "src")

        Returns:
            str: Path to the downloaded file

        Raises:
            Exception: If XLS format is not available or download fails
        """
        # Get asset information
        asset = self.get_asset(asset_uid)

        # Find XLS download URL
        downloads = asset.get('downloads', [])
        xls_url = None

        for download in downloads:
            if download.get('format') == 'xls':
                xls_url = download.get('url')
                break

        if not xls_url:
            raise Exception(f"XLS format not available for asset {asset_uid}")

        # Create downloads directory if it doesn't exist
        os.makedirs(download_dir, exist_ok=True)

        # Generate filename using asset name
        asset_name = asset.get('name', asset_uid)
        # Clean filename to be filesystem-safe
        safe_name = "".join(c for c in asset_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_name = safe_name.replace(' ', '_') if safe_name else asset_uid
        filename = f"xlsform_{safe_name}.xlsx"
        filepath = os.path.join(download_dir, filename)

        # Download the file
        self.client.download_file(xls_url, filepath)

        return filepath

    def data_to_dataframes(self, asset_uid: str) -> List[pd.DataFrame]:
        """Convert survey data to list of DataFrames by repeat groups.

        Args:
            asset_uid: The UID of the asset to process

        Returns:
            List of pandas DataFrames for each repeat group level
        """
        # Get asset information to extract questions structure
        asset = self.get_asset(asset_uid)

        # Get questions structure as schema
        questions_structure = self.get_questions(asset)
        builder = XLSFormDataStructureBuilder(questions_structure)

        # Get submission data
        data = self.get_data(asset_uid)
        submissions = data.get('results', [])

        return create_dataframes_from_submissions(submissions, builder)

    def data_to_xlsx(self, asset_uid: str, file_path: str) -> None:
        """Convert survey data and export directly to Excel file.

        Args:
            asset_uid: The UID of the asset to process
            file_path: Path where to save the Excel file
        """
        dataframes = self.data_to_dataframes(asset_uid)
        self._export_to_xlsx(dataframes, file_path)

    def _export_to_xlsx(self, dataframes: List[pd.DataFrame], file_path: str) -> None:
        """Export list of DataFrames to Excel file with separate sheets"""
        if not dataframes:
            print("No DataFrames to export")
            return

        # Sheet names for each DataFrame level
        sheet_names = ['General', 'Hogar', 'Individuo']

        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            for i, df in enumerate(dataframes):
                sheet_name = sheet_names[i] if i < len(sheet_names) else f'Sheet_{i+1}'
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                if self.debug:
                    print(f"Exported {sheet_name} sheet with shape {df.shape}")

        if self.debug:
            print(f"Successfully exported {len(dataframes)} sheets to {file_path}")
