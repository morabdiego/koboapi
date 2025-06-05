"""
Toma dataframes, los convierte a excel asignando nombre a cada sheet.
"""
import pandas as pd
from typing import List, Dict, Any, Optional
from .models import SurveyStructure
from .utils import safe_filename

class DataExporter:
    """Handles exporting processed data to various formats."""

    def __init__(self, structure: Optional[SurveyStructure] = None):
        self.structure = structure

    def to_excel(self, dataframes: List[pd.DataFrame], filepath: str,
                survey_name: str = "Survey") -> None:
        """Export DataFrames to Excel with proper sheet naming."""
        if not dataframes:
            raise ValueError("No DataFrames to export")

        sheet_names = self._generate_sheet_names(len(dataframes), survey_name)

        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            for i, df in enumerate(dataframes):
                sheet_name = sheet_names[i]
                clean_name = safe_filename(sheet_name, 31)  # Excel sheet name limit
                df.to_excel(writer, sheet_name=clean_name, index=False)

        print(f"Successfully exported {len(dataframes)} sheets to {filepath}")

    def _generate_sheet_names(self, count: int, base_name: str) -> List[str]:
        """Generate appropriate sheet names."""
        names = [base_name]

        if self.structure:
            sorted_groups = sorted(
                self.structure.repeat_groups.items(),
                key=lambda x: x[1].level
            )
            for _, group in sorted_groups:
                names.append(group.label or group.simple_name.title())

        # Fill remaining with generic names
        while len(names) < count:
            names.append(f'Sheet_{len(names)}')

        return names[:count]
