from typing import Protocol, List, Dict

from term_resolver.templates import sparql
from term_resolver.commons import SearchParameters
from SPARQLWrapper import SPARQLWrapper, JSON


class TermResolver(Protocol):
    """An interface class for retrieving URIs for (a) given term(s)."""

    def get_uris_for_terms(
        self, search_parameters: SearchParameters
    ) -> Dict[str, List[str]]:
        """Returns the URIs for the given SearchParameters.
        If there is no corresponding URI, the list is empty.
        The response has the format:
        {
            'Fagus': ['https://www.biofid.de/ontologies/1234],
            ...
        }
        """
        ...


class GraphDatabaseTermResolver:
    """Resolves a term by calling a SPARQL graph database."""

    TERM_VARIABLE_STRING = sparql.TERM_VARIABLE_STRING.strip("?")
    URI_VARIABLE_STRING = sparql.URI_VARIABLE_STRING.strip("?")

    def __init__(self, graph_db_url: str):
        self.graph_db_url = graph_db_url
        self.graph_endpoint = None

    def get_uris_for_terms(
        self, search_parameters: SearchParameters
    ) -> Dict[str, List[str]]:
        """Returns the URIs for the given SearchParameters.
        If there is no corresponding URI, the list is empty.
        """
        sparql_query = sparql.compile_term_to_uri_query_from_search_parameters(
            search_parameters
        )
        graph_response = self._query(sparql_query)
        bindings = get_bindings(graph_response)

        response_data = self._extract_uris_from_response(bindings)

        if search_parameters.recursive:
            # Iterate only over the respective URI lists of each term
            for parent_uris in response_data.values():
                children_limit = max(search_parameters.limit - len(parent_uris), 0)
                children_term_to_uri_data = self.get_children_uris_and_terms(
                    parent_uris, max_number_of_results=children_limit, page=search_parameters.page
                )
                parent_uris.extend(children_term_to_uri_data)

        return response_data

    def get_children_uris_and_terms(
        self, parent_uris: List[str], max_number_of_results: int, page: int
    ) -> List[str]:
        children_sparql_query = sparql.compile_uri_children_query(parent_uris, max_number_of_results, page)
        graph_response = self._query(children_sparql_query)
        bindings = get_bindings(graph_response)
        return [get_value(row, self.URI_VARIABLE_STRING) for row in bindings]

    def _query(self, sparql_query_string: str) -> dict:
        if self.graph_endpoint is None:
            self.graph_endpoint = self._create_connection_to_graph_database()

        self.graph_endpoint.setQuery(sparql_query_string)
        return self.graph_endpoint.query().convert()

    def _extract_uris_from_response(self, graph_bindings: list) -> Dict[str, List[str]]:
        term_to_uri_mapping = {}

        for binding in graph_bindings:
            term = get_value(binding, self.TERM_VARIABLE_STRING)
            uri = get_value(binding, self.URI_VARIABLE_STRING)
            term_to_uri_mapping.setdefault(term, []).append(uri)

        return term_to_uri_mapping

    def _create_connection_to_graph_database(self):
        sparql_endpoint = SPARQLWrapper(endpoint=self.graph_db_url)
        sparql_endpoint.setReturnFormat(JSON)

        return sparql_endpoint


def get_value(graph_binding: dict, variable_name: str):
    return graph_binding[variable_name]["value"]


def get_bindings(graph_response: dict) -> List[dict]:
    return graph_response["results"]["bindings"]
