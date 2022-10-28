import requests
from requests.exceptions import HTTPError
from requests.adapters import HTTPAdapter
from urllib3 import Retry
from pydantic import validate_arguments
from typing import Dict

from giga.utils.logging import LOGGER

DEFAULT_RETRIES = 5
DEFAULT_BACKOFF = 0.3

# retry on all status codes that are 300+
DEFAULT_FORCELIST = [x for x in requests.status_codes._codes if x >= 300]


def session_with_retries(max_retries: int = DEFAULT_RETRIES,
                         backoff_factor: float = DEFAULT_BACKOFF,
                         status_forcelist: list = DEFAULT_FORCELIST,
                         **kwargs
                         ) -> requests.Session:
    """Creates a new Session with `max_retries` retry attempts
    """
    new_session = requests.Session()
    retries = Retry(
        total=max_retries,
        status_forcelist=frozenset(status_forcelist),
        backoff_factor=backoff_factor,
        # ensure a response is returned:
        raise_on_status=False,
    )
    retry_adapter = HTTPAdapter(max_retries=retries)
    new_session.mount('http://', retry_adapter)
    new_session.mount('https://', retry_adapter)
    return new_session

@validate_arguments
def get(url: str, header: Dict,
                  exception: Exception = requests.exceptions.ConnectionError,
                  **kwargs) -> requests.Response:
    """
        http REST GET helper: allows some customization with retries and expected status codes at calltime
    """
    sess = session_with_retries(**kwargs)
    res = sess.get(url, headers=header)
    try:
        res.raise_for_status()
        return res
    except HTTPError:
        LOGGER.warning(f'The request failed with code: {res.status_code} to {url}')
        raise exception()
