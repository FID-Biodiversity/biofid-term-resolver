from typing import List, Any

from term_resolver.commons import SearchParameters

namespaces = {
    "terms": "https://dwc.tdwg.org/terms/#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
}

label_values = ["rdfs:label", "terms:scientificName", "terms:vernacularName"]
systematics_values = [
    "terms:phylum",
    "terms:kingdom",
    "terms:class",
    "terms:order",
    "terms:family",
    "terms:genus",
    "terms:acceptedNameUsageID",
    "terms:parentNameUsageID",
]

filter_translations = {
    "isInCorpus": "https://www.biofid.de/bio-ontologies#is_in_corpus"
}

TERM_VARIABLE_STRING = "?term"
URI_VARIABLE_STRING = "?uri"

order_by_statement = f"ORDER BY {URI_VARIABLE_STRING}"


def compile_term_to_uri_query_from_search_parameters(
    search_parameters: SearchParameters,
) -> str:
    terms = search_parameters.terms

    label_variable_string = "?hasLabel"

    sparql_select_base = (
        f"SELECT DISTINCT {TERM_VARIABLE_STRING} {URI_VARIABLE_STRING}\nWHERE {{"
    )

    label_values_string = create_values_string(label_variable_string, label_values)
    term_values_string = create_values_string(
        TERM_VARIABLE_STRING, [f'"{term}"^^xsd:string' for term in terms]
    )

    term_to_uri_base_sparql = (
        f"{URI_VARIABLE_STRING} {label_variable_string} {TERM_VARIABLE_STRING} ."
    )

    limit_statement = f"LIMIT {search_parameters.limit}"

    sparql_statements = [
        sparql_select_base,
        label_values_string,
        term_values_string,
        term_to_uri_base_sparql,
        "}",
        order_by_statement,
        limit_statement,
    ]

    sparql_string = "\n".join(sparql_statements)

    return prepend_required_namespaces(sparql_string)


def compile_uri_children_query(
    uris: List[str], max_number_of_results: int, search_parameters: SearchParameters
) -> str:
    systematics_variable_string = "?isPartOfSystematics"
    parent_uris_variable_string = "?parents"

    select_base_statement = f"""SELECT DISTINCT {URI_VARIABLE_STRING}\nWHERE {{"""
    systematics_values_string = create_values_string(
        systematics_variable_string, systematics_values
    )
    parent_uris_values = create_values_string(parent_uris_variable_string, uris)

    children_query_statement = f"{URI_VARIABLE_STRING} {systematics_variable_string} {parent_uris_variable_string} ."

    limit_statement = f"LIMIT {max_number_of_results}"

    offset_statement = create_offset_string(
        max_number_of_results, search_parameters.page
    )

    filter_statements = [
        f"{URI_VARIABLE_STRING} {wrap_uri_in_brackets(filter_translations[filter_name])} {value_to_sparql(filter_value)} ."
        for filter_name, filter_value in search_parameters.filters.items()
    ]

    sparql_statements = [
        select_base_statement,
        systematics_values_string,
        parent_uris_values,
        children_query_statement,
        *filter_statements,
        "}",
        order_by_statement,
        limit_statement,
        offset_statement,
    ]

    sparql_query = "\n".join(sparql_statements)

    return prepend_required_namespaces(sparql_query)


def prepend_required_namespaces(sparql_query_string: str) -> str:
    return f"{create_namespaces(sparql_query_string)}\n\n{sparql_query_string}"


def create_offset_string(limit: int, page: int) -> str:
    offset = limit * (page - 1)
    return f"OFFSET {offset}"


def create_values_string(values_name: str, values: List[str]) -> str:
    values = [
        v if not v.startswith("http") else f"{wrap_uri_in_brackets(v)}" for v in values
    ]
    return f'VALUES {values_name} {{ {" ".join(values)} }}'


def create_namespaces(sparql_statement: str) -> str:
    namespace_strings = []
    for name, uri in namespaces.items():
        if name in sparql_statement:
            ns_string = f"PREFIX {name}: {wrap_uri_in_brackets(uri)}"
            namespace_strings.append(ns_string)

    return "\n".join(namespace_strings)


def wrap_uri_in_brackets(uri: str) -> str:
    return uri if uri.startswith("<") else f"<{uri}>"


def value_to_sparql(value: Any) -> str:
    if isinstance(value, bool):
        sparql_value = (
            f'"{str(value).lower()}"^^<http://www.w3.org/2001/XMLSchema#boolean>'
        )
    else:
        raise NotImplementedError(
            "The given value type is not not impolemented for a SPARQL conversion!"
        )

    return sparql_value
