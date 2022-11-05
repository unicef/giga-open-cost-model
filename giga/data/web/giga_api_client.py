import requests
from typing import Callable
from pydantic import validate_arguments

import giga.utils.requests as giga_requests
from giga.utils.logging import LOGGER


DEFAULT_SCHOOL_ID_MAP = {"Brazil": 144, "Rwanda": 32}


class GigaAPIClient:
    def __init__(self, auth_token: str, **kwargs):
        """
        Interacts with the Giga project connect APIs to retrieve school data
        Giga provisions non-expiring auth tokens as a means of granting access
        Client must be configured with the provisioning token
        """
        self.auth_token = auth_token
        self.school_id_map = kwargs.get("school_id_map", DEFAULT_SCHOOL_ID_MAP)

    @property
    def auth_header(self):
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.auth_token}",
        }

    def _get_document_pages(
        self,
        base_url: str,
        start_page: int = 1,
        docs_per_request: int = 50_000,
        max_number_of_documents: int = 500_000,
        document_formatter: Callable = lambda x: x["data"],
        **kwargs,
    ):
        """
        Iteratively fetches documents from a REST API endpoint
        """
        found_in_prev_request = docs_per_request
        doc_page = start_page
        documents = []
        while (
            len(documents) < max_number_of_documents
            and 0 < found_in_prev_request  # fetch until we reach target
            and found_in_prev_request == docs_per_request  # or we get no documents
        ):  # or we get less documents than desired per request
            try:
                url = f"{base_url}?page={doc_page}&size={docs_per_request}"
                r = giga_requests.get(
                    url,
                    self.auth_header,
                    exception=requests.exceptions.ConnectionError,
                    **kwargs,
                )
                returned = document_formatter(r.json())
                doc_page += len(returned)
                found_in_prev_request = len(returned)
                documents += returned
            except requests.exceptions.ConnectionError:
                LOGGER.warning(f"Unable to fetch documents from {base_url}")
                return documents
        return documents

    @validate_arguments
    def get_schools(self, country: str, **kwargs):
        """
        Fetches school data from the project connect API
        Schools are organized by document pages
        """
        assert country in self.school_id_map, f"Country {country} is not supported"
        school_url = kwargs.get(
            "school_url",
            "https://uni-connect-services-dev.azurewebsites.net/api/v1/schools/country",
        )
        country_id = self.school_id_map[country]
        base_url = f"{school_url}/{country_id}"
        schools = self._get_document_pages(
            base_url,
            docs_per_request=500_000,  # fetch all schools at once
            document_formatter=lambda x: x[
                "data"
            ],  # school info is found in {'data': <>}
            max_retries=3,
            **kwargs,
        )
        return schools
