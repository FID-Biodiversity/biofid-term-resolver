import json
import pathlib

import pytest

from term_resolver.commons import SearchParameters
from term_resolver.resolvers import GraphDatabaseTermResolver
import rdflib


class TestGraphDatabaseTermResolver:
    @pytest.mark.parametrize(
        ["search_parameters", "expected_uris_per_term"],
        [
            (
                {"terms": ["Fagus"], "recursive": True, "limit": 10},
                {
                    "Fagus": [
                        "https://www.biofid.de/ontology/fagus",
                        "https://www.biofid.de/ontology/fagus_sylvatica_sylvatica",
                        "https://www.biofid.de/ontology/fagus_non_sylvatica",
                        "https://www.biofid.de/ontology/fagus_sylvatica",
                    ]
                },
            ),
            (
                {"terms": ["Fagus sylvatica"], "recursive": True, "limit": 10},
                {
                    "Fagus sylvatica": [
                        "https://www.biofid.de/ontology/fagus_sylvatica",
                        "https://www.biofid.de/ontology/fagus_sylvatica_sylvatica",
                        "https://www.biofid.de/ontology/fagus_non_sylvatica",
                    ]
                },
            ),
            (
                {"terms": ["Fagus"], "recursive": False, "limit": 10},
                {"Fagus": ["https://www.biofid.de/ontology/fagus"]},
            ),
            (
                {"terms": ["Fagus", "Quercus L."], "recursive": True, "limit": 10},
                {
                    "Fagus": [
                        "https://www.biofid.de/ontology/fagus",
                        "https://www.biofid.de/ontology/fagus_sylvatica_sylvatica",
                        "https://www.biofid.de/ontology/fagus_non_sylvatica",
                        "https://www.biofid.de/ontology/fagus_sylvatica",
                    ],
                    "Quercus L.": ["https://www.biofid.de/ontology/quercus"],
                },
            ),
        ],
        indirect=["search_parameters"],
    )
    def test_term_resolving(
        self,
        resolver,
        search_parameters: SearchParameters,
        expected_uris_per_term,
    ):
        uris_per_term = resolver.get_uris_for_terms(search_parameters)
        assert_equal_dicts(uris_per_term, expected_uris_per_term)

    @pytest.mark.parametrize(
        ["search_parameters", "expected_number_of_uris"],
        [
            ({"terms": ["Fagus"], "recursive": True, "limit": 2}, 2),
        ],
        indirect=["search_parameters"],
    )
    def test_term_resolving_limit(
        self, resolver, search_parameters: SearchParameters, expected_number_of_uris
    ):
        uris_per_term = resolver.get_uris_for_terms(search_parameters)
        assert len(uris_per_term["Fagus"]) == expected_number_of_uris

    @pytest.mark.parametrize(
        ["search_parameters", "expected_number_of_uris"],
        [
            ({"terms": ["Fagus"], "recursive": True, "limit": 3, 'page': 1}, 3),
            ({"terms": ["Fagus"], "recursive": True, "limit": 3, 'page': 2}, 1),
        ],
        indirect=["search_parameters"],
    )
    def test_term_resolving_limit(
            self, resolver, search_parameters: SearchParameters, expected_number_of_uris
    ):
        uris_per_term = resolver.get_uris_for_terms(search_parameters)
        assert len(uris_per_term["Fagus"]) == expected_number_of_uris

    @pytest.fixture
    def resolver(self, rdf_data_file_path):
        resolver = RequestMockedGraphDatabaseTermResolver()
        resolver.load_data_to_graph(rdf_data_file_path)
        return resolver

    @pytest.fixture
    def search_parameters(self, request):
        return SearchParameters(**request.param)

    @pytest.fixture
    def rdf_data_file_path(self, resources_directory_path):
        return resources_directory_path / "rdf/mock-plant-ontology.nt"


def assert_equal_dicts(dict1: dict, dict2: dict) -> None:
    assert set(dict1.keys()) == set(dict2.keys())

    for key in dict1.keys():
        assert set(dict1[key]) == set(dict2[key])


class RequestMockedGraphDatabaseTermResolver(GraphDatabaseTermResolver):
    def __init__(self):
        super(RequestMockedGraphDatabaseTermResolver, self).__init__("localhost:1234")
        self.received_queries = []

        self.mock_db = rdflib.Graph()

    def load_data_to_graph(self, rdf_file_name: pathlib.Path) -> None:
        self.mock_db.parse(str(rdf_file_name))

    def _query(self, sparql_query: str) -> dict:
        self.received_queries.append(sparql_query)
        result = self.mock_db.query(sparql_query)

        return json.loads(result.serialize(format="json").decode("utf-8"))
