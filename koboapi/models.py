"""Data models for KoboAPI responses."""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from datetime import datetime

@dataclass
class Asset:
    """Represents a Kobo asset (survey).

    Note: The list_assets() method now returns raw dictionaries instead of Asset objects.
    This class is available for manual conversion if needed using Asset.from_dict().
    """
    uid: str
    name: str
    asset_type: str
    owner: str
    date_created: datetime
    date_modified: datetime
    deployment_active: bool
    has_deployment: bool
    deployment_count: int
    submission_count: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Asset':
        """Create Asset from API response data.

        Args:
            data: Dictionary containing asset data from the API

        Returns:
            Asset object with parsed data
        """
        return cls(
            uid=data['uid'],
            name=data['name'],
            asset_type=data['asset_type'],
            owner=data['owner'],
            date_created=datetime.fromisoformat(data['date_created'].replace('Z', '+00:00')),
            date_modified=datetime.fromisoformat(data['date_modified'].replace('Z', '+00:00')),
            deployment_active=data.get('deployment__active', False),
            has_deployment=data.get('has_deployment', False),
            deployment_count=data.get('deployment_count', 0),
            submission_count=data.get('deployment__submission_count', 0)
        )

@dataclass
class Choice:
    """Represents a choice option in a survey."""
    name: str
    label: str
    list_name: str
    sequence: int

@dataclass
class Question:
    """Represents a survey question."""
    name: str
    type: str
    label: str
    sequence: int
    list_name: Optional[str] = None
    choices: Optional[Dict[str, Choice]] = None
    required: bool = False
