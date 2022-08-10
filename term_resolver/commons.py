from dataclasses import dataclass, field
from typing import Union, List
from enum import Enum


class Filter(Enum):
    """ A list of filters that can be applied to the TermResolver. """
    is_in_corpus = 'isInCorpus'


@dataclass
class SearchParameters:
    """Holds all data for a single term resolving request."""

    terms: Union[str, List[str]]
    recursive: bool  # Whether to look up child URIs (True) or not (False)
    limit: int  # The maximum number of URIs to return
    page: int = 1  # The current page, if necessary
    filters: dict = field(default_factory=dict)
