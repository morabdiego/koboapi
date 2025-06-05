"""Main builder class that orchestrates the data processing."""

from typing import Dict, List, Any, Optional
import pandas as pd
from .models import SurveyStructure
from .structure_parser import StructureParser
from .data_processor import DataProcessor
from .exporter import DataExporter

class XLSFormDataStructureBuilder:
    """
    Main class that orchestrates XLSForm data processing.
    Follows single responsibility principle with clear separation of concerns.
    """

    def __init__(self, xlsform_json: Dict[str, Any]):
        self.parser = StructureParser(xlsform_json)
        self.structure = self.parser.parse()
        self.processor = DataProcessor(self.structure)
        self.exporter = DataExporter(self.structure)

    def process_submissions(self, submissions: List[Dict[str, Any]]) -> List[pd.DataFrame]:
        """Process submissions into DataFrames."""
        return self.processor.process_submissions(submissions)

    def export_to_excel(
            self, dataframes: List[pd.DataFrame], filepath: str,
            survey_name: str = "Survey"
            ) -> None:
        """Export DataFrames to Excel file."""
        self.exporter.to_excel(dataframes, filepath, survey_name)

    def get_structure_summary(self) -> Dict[str, Any]:
        """Get a summary of the form structure."""
        return {
            'total_questions': len(self.structure.questions),
            'repeat_groups': list(self.structure.repeat_groups.keys()),
            'question_types': list(set(q.type for q in self.structure.questions.values()))
        }

    def get_questions_by_type(self, question_type: str) -> Dict[str, Any]:
        """Get questions of specific type."""
        return self.structure.get_questions_by_type(question_type)
