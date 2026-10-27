# SPDX-License-Identifier: GPL-2.0-or-later
"""Qt HTTP boundary; no dialogs, settings access or QGIS layer operations."""

from qgis.PyQt.QtCore import QUrl, QUrlQuery
from qgis.PyQt.QtNetwork import QNetworkRequest

from .credential_validation import validated_credential

from .api_protocol import (
    LOCAL_SEARCH_ENDPOINT, ROUTE_ENDPOINT,
    local_search_parameters, route_parameters,
)


def _request(endpoint, parameters, headers):
    url = QUrl(endpoint)
    query = QUrlQuery()
    for name, value in parameters:
        query.addQueryItem(name, value)
    url.setQuery(query)
    request = QNetworkRequest(url)
    for name, value in headers:
        request.setRawHeader(name, value)
    return request


def local_search_request(query, client_id, client_secret):
    return _request(LOCAL_SEARCH_ENDPOINT, local_search_parameters(query), [
        (b"X-NCP-APIGW-API-KEY-ID", validated_credential(client_id).encode("ascii")),
        (b"X-NCP-APIGW-API-KEY", validated_credential(client_secret).encode("ascii")),
    ])


def route_request(origin, destination, priority, waypoints, avoid_options,
                  car_type, car_fuel, client_id, client_secret, language="ko"):
    return _request(ROUTE_ENDPOINT, route_parameters(
        origin, destination, priority, waypoints, avoid_options, car_type, car_fuel, language
    ), [
        (b"x-ncp-apigw-api-key-id", validated_credential(client_id).encode("ascii")),
        (b"x-ncp-apigw-api-key", validated_credential(client_secret).encode("ascii")),
        (b"Content-Type", b"application/json"),
    ])


def read_reply(reply):
    """Read then schedule deletion; the caller retains request/cancellation state."""
    status_code = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
    raw_data = bytes(reply.readAll())
    network_error = reply.error()
    network_message = reply.errorString()
    reply.deleteLater()
    return status_code, raw_data, network_error, network_message
