from dataclasses import dataclass
from typing import Union, List


@dataclass
class SearchParameters:
    """Holds all data for a single term resolving request."""

    terms: Union[str, List[str]]
    recursive: bool  # Whether to look up child URIs (True) or not (False)
    limit: int  # The maximum number of URIs to return
    page: int = 1  # The current page, if necessary
