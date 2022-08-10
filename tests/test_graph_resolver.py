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
            (  # Scenario - Single genus with all children
                {"terms": ["Fagus"], "recursive": True, "limit": 10},
                {
                    "Fagus": [
                        "https://www.biofid.de/ontology/fagus",
                        "https://www.biofid.de/ontology/fagus_non_sylvatica",
                        "https://www.biofid.de/ontology/fagus_sylvatica",
                        "https://www.biofid.de/ontology/fagus_sylvatica_sylvatica",
                    ]
                },
            ),
            (  # Scenario - Single species with all children
                {"terms": ["Fagus sylvatica"], "recursive": True, "limit": 10},
                {
                    "Fagus sylvatica": [
                        "https://www.biofid.de/ontology/fagus_sylvatica",
                        "https://www.biofid.de/ontology/fagus_non_sylvatica",
                        "https://www.biofid.de/ontology/fagus_sylvatica_sylvatica",
                    ]
                },
            ),
            (  # Scenario - Single term without any children
                {"terms": ["Fagus"], "recursive": False, "limit": 10},
                {"Fagus": ["https://www.biofid.de/ontology/fagus"]},
            ),
            (  # Scenario - Multiple terms with their children
                {"terms": ["Fagus", "Quercus L."], "recursive": True, "limit": 10},
                {
                    "Fagus": [
                        "https://www.biofid.de/ontology/fagus",
                        "https://www.biofid.de/ontology/fagus_non_sylvatica",
                        "https://www.biofid.de/ontology/fagus_sylvatica",
                        "https://www.biofid.de/ontology/fagus_sylvatica_sylvatica",
                    ],
                    "Quercus L.": ["https://www.biofid.de/ontology/quercus"],
                },
            ),
            (  # Scenario - Filter for present URIs
                {
                    "terms": ["Ulmus L."],
                    "limit": 10,
                    "recursive": True,
                    "isInCorpus": True,
                },
                {
                    "Ulmus L.": [
                        "https://www.biofid.de/ontology/ulmus",
                        "https://www.biofid.de/ontology/ulmus_glabra_sub",
                    ]
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
        assert uris_per_term == expected_uris_per_term

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
            ({"terms": ["Fagus"], "recursive": True, "limit": 3, "page": 1}, 3),
            ({"terms": ["Fagus"], "recursive": True, "limit": 3, "page": 2}, 1),
            ({"terms": ["Fagus"], "recursive": True, "limit": 3, "page": 3}, 0),
        ],
        indirect=["search_parameters"],
    )
    def test_term_paging(
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
        data = dict(request.param)

        if "isInCorpus" in data:
            data.setdefault("filters", {})["isInCorpus"] = data["isInCorpus"]
            del data["isInCorpus"]

        return SearchParameters(**data)

    @pytest.fixture
    def rdf_data_file_path(self, resources_directory_path):
        return resources_directory_path / "rdf/mock-plant-ontology.nt"


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
