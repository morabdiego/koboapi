"""Main wrapper for KoboAPI interactions."""

import os
from typing import Any, Dict, List, Optional
import pandas as pd
from .client import Client
from .builder import XLSFormDataStructureBuilder
from .utils import safe_filename, ensure_directory
from .exceptions import KoboAPIError

class Kobo:
    """
    Main interface for KoBoToolbox API interactions.
    Simplified and optimized for better maintainability.
    """

    ENDPOINTS = {
        'default': 'https://kf.kobotoolbox.org/',
        'humanitarian': 'https://kc.humanitarianresponse.info/'
    }

    def __init__(self, token: str, endpoint: str = 'default',
                 debug: bool = False, **client_kwargs):
        """Initialize Kobo client with improved configuration."""
        resolved_endpoint = self.ENDPOINTS.get(endpoint, endpoint)
        self.client = Client(token, resolved_endpoint, debug, **client_kwargs)
        self.debug = debug

    # Asset management methods
    def list_assets(self) -> List[Dict[str, Any]]:
        """List all assets."""
        response = self.client.get('/assets.json')
        return response.get('results', [])

    def get_asset(self, asset_uid: str) -> Dict[str, Any]:
        """Get asset details."""
        return self.client.get(f'/assets/{asset_uid}.json')

    def list_uid(self) -> Dict[str, str]:
        """Get mapping of asset names to UIDs."""
        return {
            asset.get('name', ''): asset.get('uid', '')
            for asset in self.list_assets()
        }

    # Data retrieval methods
    def get_data(self, asset_uid: str, **params) -> Dict[str, Any]:
        """Get survey data with flexible parameters."""
        # Handle special parameter combinations
        if 'query' in params and 'submitted_after' in params:
            if self.debug:
                print("Ignoring 'submitted_after' because 'query' is specified.")
            params.pop('submitted_after')
        elif 'submitted_after' in params:
            submitted_after = params.pop('submitted_after')
            params['query'] = f'{{"_submission_time": {{"$gt": "{submitted_after}"}}}}'

        return self.client.get(f'/assets/{asset_uid}/data.json', params)

    # Structure extraction methods
    def get_questions(self, asset: Dict[str, Any]) -> Dict[str, Any]:
        """Extract questions structure from asset."""
        return self._parse_survey_content(asset.get('content', {}))

    def get_choices(self, asset: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Extract choices from asset content."""
        return self._parse_choices_content(asset.get('content', {}))

    # Main processing methods
    def data_to_dataframes(self, asset_uid: str) -> List[pd.DataFrame]:
        """Convert survey data to DataFrames."""
        asset = self.get_asset(asset_uid)
        questions_structure = self.get_questions(asset)

        builder = XLSFormDataStructureBuilder(questions_structure)

        data = self.get_data(asset_uid)
        submissions = data.get('results', [])

        return builder.process_submissions(submissions)

    def data_to_xlsx(self, asset_uid: str, filepath: str) -> None:
        """Export survey data directly to Excel."""
        asset = self.get_asset(asset_uid)
        survey_name = asset.get('name', 'Survey')

        dataframes = self.data_to_dataframes(asset_uid)
        self._export_to_xlsx(dataframes, filepath)

    # File operations
    def download_xlsform(self, asset_uid: str, download_dir: str = "src") -> str:
        """Download XLS form file."""
        asset = self.get_asset(asset_uid)

        # Find XLS download URL
        xls_url = self._find_download_url(asset, 'xls')
        if not xls_url:
            raise KoboAPIError(f"XLS format not available for asset {asset_uid}")

        # Prepare file path
        ensure_directory(download_dir)
        filename = f"xlsform_{safe_filename(asset.get('name', asset_uid))}.xlsx"
        filepath = os.path.join(download_dir, filename)

        # Download
        self.client.download_file(xls_url, filepath)
        return filepath

    # Private helper methods
    def _parse_survey_content(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Parse survey content into questions structure."""
        sequence = 0
        root_group = {'questions': {}, 'groups': {}}
        group_stack = [root_group]
        current_group = root_group

        for item in content.get('survey', []):
            item_type = item.get('type', '')

            if item_type in ['begin_group', 'begin_repeat']:
                new_group = {
                    'label': self._extract_label(item),
                    'sequence': sequence,
                    'repeat': item_type == 'begin_repeat',
                    'questions': {},
                    'groups': {}
                }
                name = item.get('name') or item.get('$autoname')
                current_group['groups'][name] = new_group
                group_stack.append(current_group)
                current_group = new_group
                sequence += 1

            elif item_type in ['end_group', 'end_repeat']:
                current_group = group_stack.pop()

            else:
                name = item.get('name') or item.get('$autoname')
                if name:
                    question = {
                        'type': item_type,
                        'sequence': sequence,
                        'label': self._extract_label(item) or name,
                        'required': item.get('required', False)
                    }

                    if 'select_from_list_name' in item:
                        question['list_name'] = item['select_from_list_name']

                    current_group['questions'][name] = question
                    sequence += 1

        return root_group

    def _parse_choices_content(self, content: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Parse choices from content."""
        choice_lists = {}
        sequence = 0

        for choice_data in content.get('choices', []):
            list_name = choice_data['list_name']
            if list_name not in choice_lists:
                choice_lists[list_name] = {}

            label = self._extract_label(choice_data) or choice_data['name']

            choice_lists[list_name][choice_data['name']] = {
                'name': choice_data['name'],
                'label': label,
                'list_name': list_name,
                'sequence': sequence
            }
            sequence += 1

        return choice_lists

    def _extract_label(self, item: Dict[str, Any]) -> str:
        """Extract label from item, handling different formats."""
        label = item.get('label', '')
        if isinstance(label, list) and label:
            return label[0]
        return str(label) if label else ''

    def _find_download_url(self, asset: Dict[str, Any], format_type: str) -> Optional[str]:
        """Find download URL for specific format."""
        downloads = asset.get('downloads', [])
        for download in downloads:
            if download.get('format') == format_type:
                return download.get('url')
        return None

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
