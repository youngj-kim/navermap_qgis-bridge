// SPDX-License-Identifier: GPL-2.0-or-later
    function normalizeAddressResult(address) {
      if (address.point) {
        const detail = address.address || "주소 검색 결과";
        return {
          title: detail,
          address: detail,
          lon: Number(address.point.x),
          lat: Number(address.point.y)
        };
      }

      const detail = address.roadAddress || address.jibunAddress || address.englishAddress || "주소 검색 결과";

      return {
        title: detail,
        address: detail,
        lon: Number(address.x),
        lat: Number(address.y)
      };
    }

    function geocodeAddress(query) {
      function requestGeocode(options) {
        if (!geocoderService) {
          return Promise.resolve([]);
        }

        return new Promise((resolve) => {
          let settled = false;
          const timer = window.setTimeout(() => {
            if (!settled) {
              settled = true;
              resolve([]);
            }
          }, 5000);

          geocoderService.geocode(options, (status, response) => {
            if (settled) {
              return;
            }
            settled = true;
            window.clearTimeout(timer);
            const v2 = response && response.v2 ? response.v2 : {};
            const legacyItems =
              response &&
              response.result &&
              Array.isArray(response.result.items)
                ? response.result.items
                : [];
            const addresses = Array.isArray(v2.addresses) ? v2.addresses : [];
            const ok =
              status === naver.maps.Service.Status.OK ||
              v2.status === "OK" ||
              legacyItems.length > 0;

            if (!ok) {
              resolve([]);
              return;
            }

            resolve([...addresses, ...legacyItems].map(normalizeAddressResult));
          });
        });
      }

      function requestPoiSearch() {
        lastLocalSearchError = "";
        if (!qgisBridge || typeof qgisBridge.requestLocalSearch !== "function") {
          return Promise.resolve([]);
        }

        const requestId = `local:${Date.now()}:${nextLocalSearchRequestId++}`;
        return new Promise((resolve, reject) => {
          const timer = window.setTimeout(() => {
            localSearchRequests.delete(requestId);
            reject(new Error("POI 검색 응답 시간이 초과되었습니다."));
          }, 8000);

          localSearchRequests.set(requestId, {
            resolve(results) {
              window.clearTimeout(timer);
              resolve(results);
            },
            reject(error) {
              window.clearTimeout(timer);
              reject(error);
            }
          });
          qgisBridge.requestLocalSearch(requestId, query);
        }).catch((error) => {
          console.warn("Naver API HUB local search failed", error);
          lastLocalSearchError =
            error && error.message ? error.message : "POI 검색에 실패했습니다.";
          return [];
        });
      }

      const baseOptions = {
        count: 20
      };
      const coordinate = currentMapCoordinate();
      if (coordinate) {
        baseOptions.coordinate = `${coordinate.lon},${coordinate.lat}`;
      }

      return requestPoiSearch().then((poiResults) => {
        if (poiResults.length) {
          return poiResults;
        }
        return requestGeocode({ ...baseOptions, query }).then((results) => {
          if (results.length) {
            return results;
          }
          return requestGeocode({ ...baseOptions, address: query });
        });
      });
    }

    function selectSearchResult(result) {
      map.setZoom(16);
      moveViewer(result.lon, result.lat, { suppressBridge: true });
      searchResults.hidden = true;

      if (qgisBridge) {
        qgisBridge.moveQgisCenter(result.lon, result.lat);
      }
      setStatus(`Search -> QGIS EPSG:4326 ${result.lat.toFixed(6)}, ${result.lon.toFixed(6)}.`);
    }

    function renderSearchResults(results, onSelect = selectSearchResult) {
      searchResults.textContent = "";

      if (!results.length) {
        const empty = document.createElement("div");
        empty.className = "search-empty";
        empty.textContent = "검색 결과가 없습니다.";
        searchResults.appendChild(empty);
        searchResults.hidden = false;
        return;
      }

      results.slice(0, 20).forEach((result) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "search-result";
        button.setAttribute("role", "option");

        const title = document.createElement("span");
        title.className = "search-result-title";
        title.textContent = result.title;

        const address = document.createElement("span");
        address.className = "search-result-address";
        address.textContent = result.address;

        button.appendChild(title);
        button.appendChild(address);
        button.addEventListener("click", () => onSelect(result));
        searchResults.appendChild(button);
      });

      searchResults.hidden = false;
    }

    function searchLocal(
      query,
      onSelect = selectSearchResult,
      manageSearchButton = true,
      selectFirst = false
    ) {
      const coordinate = parseCoordinateInput(query);
      if (coordinate) {
        const result = {
          title: "입력 좌표",
          address: formatCoordinate(coordinate),
          lon: coordinate.lon,
          lat: coordinate.lat,
          source: "coordinate"
        };
        searchResults.hidden = true;
        onSelect(result);
        return;
      }

      if (!qgisBridge && !geocoderService) {
        setStatus("Naver POI/address search is not ready.");
        return;
      }

      const requestId = ++searchRequestId;
      const collected = [];
      let failed = false;
      lastLocalSearchError = "";

      if (manageSearchButton) {
        searchSubmit.disabled = true;
      }
      setStatus(`Searching Naver POI/address: ${query}`);

      geocodeAddress(query)
        .then((resultsFromGeocoder) => {
          if (requestId !== searchRequestId) {
            return;
          }
          collected.push(...resultsFromGeocoder);
          if (!resultsFromGeocoder.length) {
            failed = true;
          }

          const unique = new Map();
          collected.forEach((result) => {
            if (!Number.isFinite(result.lon) || !Number.isFinite(result.lat)) {
              return;
            }
            const key = `${result.lon.toFixed(7)},${result.lat.toFixed(7)},${result.title}`;
            if (!unique.has(key)) {
              unique.set(key, result);
            }
          });

          const results = Array.from(unique.values());
          if (selectFirst && results.length) {
            searchResults.hidden = true;
            onSelect(results[0]);
            return;
          }
          renderSearchResults(results, onSelect);
          setStatus(failed && !results.length
            ? (lastLocalSearchError || "POI/주소 검색 결과가 없습니다.")
            : `Naver POI/address search results: ${results.length}`);
        })
        .catch((error) => {
          if (requestId === searchRequestId) {
            renderSearchResults([]);
            setStatus(error && error.message ? error.message : "주소 검색 중 오류가 발생했습니다.");
          }
        })
        .finally(() => {
          if (requestId === searchRequestId && manageSearchButton) {
            searchSubmit.disabled = false;
          }
        });
    }
