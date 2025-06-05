import json
from typing import Dict, List, Any, Optional
import pandas as pd
from collections import defaultdict

class XLSFormDataStructureBuilder:
    """
    Builds data structures for processing KoBo survey submissions
    based on XLSForm JSON structure.
    """

    def __init__(self, xlsform_json: Dict[str, Any]):
        self.xlsform = xlsform_json
        self.flat_questions = {}
        self.repeat_groups = {}
        self.question_hierarchy = {}
        self._build_structure()

    def _build_structure(self):
        """Build the internal structure from XLSForm JSON"""
        self._process_questions(self.xlsform.get('questions', {}), '')
        self._process_groups(self.xlsform.get('groups', {}), '')

    def _process_questions(self, questions: Dict, prefix: str):
        """Process questions at current level"""
        for q_name, q_data in questions.items():
            full_name = f"{prefix}{q_name}" if prefix else q_name
            self.flat_questions[full_name] = {
                'type': q_data.get('type'),
                'label': q_data.get('label'),
                'required': q_data.get('required', False),
                'sequence': q_data.get('sequence'),
                'list_name': q_data.get('list_name'),
                'original_name': q_name,
                'path': prefix.rstrip('/')
            }

    def _process_groups(self, groups: Dict, prefix: str):
        """Process groups recursively"""
        for g_name, g_data in groups.items():
            full_name = f"{prefix}{g_name}" if prefix else g_name
            new_prefix = f"{full_name}/"

            # Track repeat groups
            if g_data.get('repeat', False):
                self.repeat_groups[full_name] = {
                    'label': g_data.get('label'),
                    'sequence': g_data.get('sequence'),
                    'path': prefix.rstrip('/')
                }

            # Process questions in this group
            if 'questions' in g_data:
                self._process_questions(g_data['questions'], new_prefix)

            # Process nested groups
            if 'groups' in g_data:
                self._process_groups(g_data['groups'], new_prefix)

    def get_submission_schema(self) -> Dict[str, Any]:
        """Generate schema for submission data validation"""
        schema = {
            'flat_questions': self.flat_questions,
            'repeat_groups': self.repeat_groups,
            'expected_columns': list(self.flat_questions.keys())
        }
        return schema

    def process_submission(self, submission_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single submission according to the structure"""
        processed = {
            'main_data': {},
            'repeat_data': defaultdict(list)
        }

        # Flatten the submission data
        flattened = self._flatten_submission(submission_data)

        # Separate main data from repeat data
        for key, value in flattened.items():
            if any(key.startswith(repeat_group) for repeat_group in self.repeat_groups):
                # This belongs to a repeat group
                repeat_group = self._find_repeat_group(key)
                if repeat_group:
                    processed['repeat_data'][repeat_group].append({key: value})
            else:
                processed['main_data'][key] = value

        return processed

    def _flatten_submission(self, data: Dict[str, Any], prefix: str = '') -> Dict[str, Any]:
        """Flatten nested submission data"""
        flattened = {}

        for key, value in data.items():
            full_key = f"{prefix}{key}" if prefix else key

            if isinstance(value, dict):
                flattened.update(self._flatten_submission(value, f"{full_key}/"))
            elif isinstance(value, list):
                # Handle repeat groups
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        flattened.update(self._flatten_submission(item, f"{full_key}[{i}]/"))
                    else:
                        flattened[f"{full_key}[{i}]"] = item
            else:
                flattened[full_key] = value

        return flattened

    def _find_repeat_group(self, key: str) -> Optional[str]:
        """Find which repeat group a key belongs to"""
        for repeat_group in self.repeat_groups:
            if key.startswith(repeat_group):
                return repeat_group
        return None

    def create_dataframes(self, submissions: List[Dict[str, Any]]) -> Dict[str, pd.DataFrame]:
        """Create DataFrames for main data and each repeat group"""
        all_main_data = []
        all_repeat_data = defaultdict(list)

        for submission in submissions:
            processed = self.process_submission(submission)
            all_main_data.append(processed['main_data'])

            for repeat_group, repeat_items in processed['repeat_data'].items():
                all_repeat_data[repeat_group].extend(repeat_items)

        # Create DataFrames
        dataframes = {}

        # Main DataFrame
        if all_main_data:
            dataframes['main'] = pd.DataFrame(all_main_data)

        # Repeat group DataFrames
        for repeat_group, data in all_repeat_data.items():
            if data:
                dataframes[repeat_group] = pd.DataFrame(data)

        return dataframes

    def get_question_info(self, question_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific question"""
        return self.flat_questions.get(question_name)

    def get_questions_by_type(self, question_type: str) -> Dict[str, Any]:
        """Get all questions of a specific type"""
        return {
            name: info for name, info in self.flat_questions.items()
            if info['type'] == question_type
        }

    def export_structure_summary(self) -> Dict[str, Any]:
        """Export a summary of the form structure"""
        return {
            'total_questions': len(self.flat_questions),
            'repeat_groups': list(self.repeat_groups.keys()),
            'question_types': list(set(q['type'] for q in self.flat_questions.values())),
            'questions_by_group': self._group_questions_by_path(),
            'structure_map': self._create_structure_map()
        }

    def _group_questions_by_path(self) -> Dict[str, List[str]]:
        """Group questions by their path/group"""
        grouped = defaultdict(list)
        for q_name, q_info in self.flat_questions.items():
            path = q_info['path'] or 'root'
            grouped[path].append(q_name)
        return dict(grouped)

    def _create_structure_map(self) -> Dict[str, Any]:
        """Create a hierarchical map of the form structure"""
        structure = {}

        # Add main questions
        for q_name, q_info in self.flat_questions.items():
            if not q_info['path']:
                structure[q_name] = q_info['type']

        # Add groups
        for group_name, group_info in self.repeat_groups.items():
            structure[group_name] = {
                'type': 'repeat_group',
                'questions': [
                    q_name for q_name, q_info in self.flat_questions.items()
                    if q_info['path'] and q_info['path'].startswith(group_name)
                ]
            }

        return structure

    def get_structure_as_dataframes(self) -> List[pd.DataFrame]:
        """Return the form structure as a list of DataFrames"""
        dataframes = []

        # Main questions DataFrame
        if self.flat_questions:
            questions_df = pd.DataFrame.from_dict(self.flat_questions, orient='index')
            questions_df.index.name = 'question_name'
            questions_df.reset_index(inplace=True)
            dataframes.append(questions_df)

        # Repeat groups DataFrame
        if self.repeat_groups:
            groups_df = pd.DataFrame.from_dict(self.repeat_groups, orient='index')
            groups_df.index.name = 'group_name'
            groups_df.reset_index(inplace=True)
            dataframes.append(groups_df)

        return dataframes

def load_xlsform_from_kobo(kobo_client, asset_uid: str) -> List[pd.DataFrame]:
    """Load submission data from Kobo API and return list of DataFrames by repeat groups"""
    # Get asset information to extract questions structure
    asset = kobo_client.get_asset(asset_uid)

    # Get questions structure as schema
    questions_structure = kobo_client.get_questions(asset)
    builder = XLSFormDataStructureBuilder(questions_structure)

    # Get submission data
    data = kobo_client.get_data(asset_uid)
    submissions = data.get('results', [])

    return create_dataframes_from_submissions(submissions, builder)

def load_xlsform_from_file(file_path: str, schema_path: str = 'questions.json') -> List[pd.DataFrame]:
    """Load submission data from file and return list of DataFrames by repeat groups"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Load schema from questions.json
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_data = json.load(f)
        builder = XLSFormDataStructureBuilder(schema_data)
    except FileNotFoundError:
        print(f"Schema file {schema_path} not found, creating DataFrames without schema")
        builder = None

    # Extract submissions from the API response format
    submissions = data.get('results', [data] if 'results' not in data else [])

    return create_dataframes_from_submissions(submissions, builder)

def create_dataframes_from_submissions(submissions: List[Dict[str, Any]], builder: Optional[XLSFormDataStructureBuilder] = None, survey_name: str = "General") -> List[pd.DataFrame]:
    """Create separate DataFrames for each repeat group level using schema"""
    dataframes = []

    if not submissions:
        return dataframes

    # Get repeat groups and their hierarchy from builder
    repeat_groups_info = {}
    all_columns = {}

    if builder:
        repeat_groups_info = _get_repeat_groups_hierarchy(builder)
        all_columns = _get_columns_by_level_dynamic(builder, repeat_groups_info)

    # DataFrame 1: General/Main data (non-repeat fields)
    main_data = []

    # Hardcoded metadata columns that always appear
    metadata_columns = [
        '_id', 'formhub/uuid', '__version__', 'meta/instanceID', '_xform_id_string',
        '_uuid', 'meta/rootUuid', '_attachments', '_status', '_geolocation',
        '_submission_time', '_tags', '_notes', '_validation_status', '_submitted_by'
    ]

    for submission in submissions:
        main_row = {}

        # Initialize with metadata columns
        for col in metadata_columns:
            main_row[col] = None

        # Initialize with all possible main columns from schema
        if 'main' in all_columns:
            for col in all_columns['main']:
                main_row[col] = None

        # Fill with actual data
        for key, value in submission.items():
            if not isinstance(value, list):
                # Handle nested groups by extracting original name
                if '/' in str(key):
                    original_name = key.split('/')[-1]
                    main_row[original_name] = value
                else:
                    main_row[key] = value

        main_data.append(main_row)

    if main_data:
        main_df = pd.DataFrame(main_data)
        dataframes.append(main_df)

    # Create DataFrames for each repeat group dynamically
    if repeat_groups_info:
        _create_repeat_group_dataframes(submissions, repeat_groups_info, all_columns, dataframes)

    return dataframes

def _get_repeat_groups_hierarchy(builder: XLSFormDataStructureBuilder) -> Dict[str, Dict[str, Any]]:
    """Extract repeat groups and their hierarchy from the builder"""
    hierarchy = {}

    for group_name, group_info in builder.repeat_groups.items():
        # Get the group level (how many levels deep it is)
        level = group_name.count('/')
        parent_path = '/'.join(group_name.split('/')[:-1]) if '/' in group_name else None
        group_simple_name = group_name.split('/')[-1]

        hierarchy[group_name] = {
            'simple_name': group_simple_name,
            'level': level,
            'parent_path': parent_path,
            'label': group_info.get('label', group_simple_name),
            'sequence': group_info.get('sequence', 0)
        }

    return hierarchy

def _get_columns_by_level_dynamic(builder: XLSFormDataStructureBuilder, repeat_groups_info: Dict[str, Dict[str, Any]]) -> Dict[str, List[str]]:
    """Extract column names by level dynamically from the XLSForm structure"""
    columns_by_level = {'main': []}

    # Initialize columns for each repeat group
    for group_name in repeat_groups_info.keys():
        simple_name = repeat_groups_info[group_name]['simple_name']
        columns_by_level[simple_name] = []

    for question_path, question_info in builder.flat_questions.items():
        original_name = question_info['original_name']
        path = question_info['path']

        if not path:
            # Main level questions
            columns_by_level['main'].append(original_name)
        else:
            # Find which repeat group this question belongs to
            assigned = False
            for group_name, group_info in repeat_groups_info.items():
                if path == group_name or path.startswith(f"{group_name}/"):
                    simple_name = group_info['simple_name']
                    columns_by_level[simple_name].append(original_name)
                    assigned = True
                    break

            # If not assigned to any repeat group, it's a regular group (like vivienda)
            if not assigned:
                columns_by_level['main'].append(original_name)

    return columns_by_level

def _create_repeat_group_dataframes(submissions: List[Dict[str, Any]], repeat_groups_info: Dict[str, Dict[str, Any]], all_columns: Dict[str, List[str]], dataframes: List[pd.DataFrame]) -> None:
    """Create DataFrames for repeat groups dynamically"""
    # Sort repeat groups by level to process them in order
    sorted_groups = sorted(repeat_groups_info.items(), key=lambda x: x[1]['level'])

    for group_path, group_info in sorted_groups:
        group_name = group_info['simple_name']
        level = group_info['level']

        group_data = []

        for submission in submissions:
            submission_id = submission.get('_id', submission.get('meta/instanceID', ''))

            if level == 0:
                # First level repeat group
                _process_first_level_repeat(submission, submission_id, group_name, group_path, all_columns, group_data)
            else:
                # Nested repeat groups
                _process_nested_repeat(submission, submission_id, group_name, group_path, sorted_groups[:sorted_groups.index((group_path, group_info))], all_columns, group_data)

        if group_data:
            group_df = pd.DataFrame(group_data)
            dataframes.append(group_df)

def _process_first_level_repeat(submission: Dict[str, Any], submission_id: str, group_name: str, group_path: str, all_columns: Dict[str, List[str]], group_data: List[Dict[str, Any]]) -> None:
    """Process first level repeat group"""
    group_list = submission.get(group_name, [])

    for group_idx, group_item in enumerate(group_list):
        group_row = {'_parent_id': submission_id}

        # Initialize with all possible columns for this group
        if group_name in all_columns:
            for col in all_columns[group_name]:
                group_row[col] = None

        # Fill with actual data
        for key, value in group_item.items():
            if not isinstance(value, list):  # Skip nested repeats
                original_name = key.split('/')[-1] if '/' in key else key
                group_row[original_name] = value

        group_data.append(group_row)

def _process_nested_repeat(submission: Dict[str, Any], submission_id: str, group_name: str, group_path: str, parent_groups: List[tuple], all_columns: Dict[str, List[str]], group_data: List[Dict[str, Any]]) -> None:
    """Process nested repeat groups"""
    # Split the group path to understand the hierarchy
    path_parts = group_path.split('/')

    # Navigate through the submission data following the path
    current_level_data = []

    # Start with the submission
    if len(path_parts) == 1:
        # This shouldn't happen for nested repeats, but handle it anyway
        return

    # Get the first level repeat data
    first_level_name = path_parts[0]
    first_level_items = submission.get(first_level_name, [])

    for first_idx, first_item in enumerate(first_level_items):
        first_level_id = f"{submission_id}_{first_idx + 1}"

        if len(path_parts) == 2:
            # Second level repeat group
            second_level_name = path_parts[1]
            second_level_items = first_item.get(f"{first_level_name}/{second_level_name}", [])

            for second_item in second_level_items:
                group_row = {
                    '_parent_id': submission_id,
                    f'_{first_level_name}_id': first_level_id
                }

                # Initialize with all possible columns for this group
                if group_name in all_columns:
                    for col in all_columns[group_name]:
                        group_row[col] = None

                # Fill with actual data
                for key, value in second_item.items():
                    if not isinstance(value, list):  # Skip further nested repeats
                        original_name = key.split('/')[-1] if '/' in key else key
                        group_row[original_name] = value

                group_data.append(group_row)

        elif len(path_parts) == 3:
            # Third level repeat group (nested within second level)
            second_level_name = path_parts[1]
            third_level_name = path_parts[2]

            # Look for the second level repeat data
            second_level_items = first_item.get(f"{first_level_name}/{second_level_name}", [])

            for second_idx, second_item in enumerate(second_level_items):
                second_level_id = f"{first_level_id}_{second_idx + 1}"

                # Look for the third level repeat data
                third_level_key = f"{first_level_name}/{second_level_name}/{third_level_name}"
                third_level_items = second_item.get(third_level_key, [])

                for third_item in third_level_items:
                    group_row = {
                        '_parent_id': submission_id,
                        f'_{first_level_name}_id': first_level_id,
                        f'_{second_level_name}_id': second_level_id
                    }

                    # Initialize with all possible columns for this group
                    if group_name in all_columns:
                        for col in all_columns[group_name]:
                            group_row[col] = None

                    # Fill with actual data
                    for key, value in third_item.items():
                        original_name = key.split('/')[-1] if '/' in key else key
                        group_row[original_name] = value

                    group_data.append(group_row)

def get_columns_by_level(builder: XLSFormDataStructureBuilder) -> Dict[str, List[str]]:
    """DEPRECATED: Use _get_columns_by_level_dynamic instead"""
    import warnings
    warnings.warn("get_columns_by_level is deprecated, functionality moved to internal methods",
                 DeprecationWarning, stacklevel=2)

    repeat_groups_info = _get_repeat_groups_hierarchy(builder)
    return _get_columns_by_level_dynamic(builder, repeat_groups_info)

def export_to_xlsx(dataframes: List[pd.DataFrame], file_path: str, survey_name: str = "Survey", repeat_groups_info: Optional[Dict[str, Dict[str, Any]]] = None) -> None:
    """Export list of DataFrames to Excel file with separate sheets"""
    if not dataframes:
        print("No DataFrames to export")
        return

    # Generate sheet names dynamically
    sheet_names = [survey_name]  # First sheet uses survey name

    if repeat_groups_info:
        # Sort repeat groups by level and add their labels/names as sheet names
        sorted_groups = sorted(repeat_groups_info.items(), key=lambda x: x[1]['level'])
        for group_path, group_info in sorted_groups:
            sheet_name = group_info.get('label') or group_info['simple_name']
            sheet_names.append(sheet_name.title())
    else:
        # Fallback to generic names if no repeat groups info
        for i in range(1, len(dataframes)):
            sheet_names.append(f'RepeatGroup_{i}')

    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        for i, df in enumerate(dataframes):
            sheet_name = sheet_names[i] if i < len(sheet_names) else f'Sheet_{i+1}'
            # Clean sheet name for Excel compatibility
            clean_sheet_name = "".join(c for c in sheet_name if c.isalnum() or c in (' ', '-', '_'))[:31]
            df.to_excel(writer, sheet_name=clean_sheet_name, index=False)
            print(f"Exported {clean_sheet_name} sheet with shape {df.shape}")

    print(f"Successfully exported {len(dataframes)} sheets to {file_path}")

def export_to_xlsx_from_kobo(kobo_client, asset_uid: str, file_path: str) -> None:
    """Load data from Kobo and export directly to Excel file"""
    dataframes = load_xlsform_from_kobo(kobo_client, asset_uid)
    export_to_xlsx(dataframes, file_path)
