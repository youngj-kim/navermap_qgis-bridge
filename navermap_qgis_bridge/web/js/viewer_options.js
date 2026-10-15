// SPDX-License-Identifier: GPL-2.0-or-later
// Explicit dependencies keep map appearance independent of navigation and routing.
function createNaverViewerOptions({getMap, getMaps, relayout, onError}) {
  const explorer = document.getElementById("explorer-body");
  const explorerButton = document.getElementById("explorer-toggle");
  const type = document.getElementById("map-type");
  const street = document.getElementById("street-toggle");
  let streetLayer = null;
  let showStreet = false;
  explorerButton.addEventListener("click", () => {
    explorer.hidden = !explorer.hidden;
    explorerButton.setAttribute("aria-expanded", String(!explorer.hidden));
    explorerButton.textContent = explorer.hidden ? "탐색창 펼치기 ▾" : "탐색창 접기 ▴";
    relayout();
  });
  type.addEventListener("change", () => {
    if (!getMap()) return;
    const name = ["NORMAL", "SATELLITE", "HYBRID"].includes(type.value) ? type.value : "NORMAL";
    getMap().setMapTypeId(getMaps().MapTypeId[name]);
  });
  street.addEventListener("click", () => {
    if (!getMap()) return;
    try {
      if (!streetLayer) streetLayer = new (getMaps().StreetLayer)();
      streetLayer.setMap(showStreet ? null : getMap());
      showStreet = !showStreet;
      street.setAttribute("aria-pressed", String(showStreet));
      street.textContent = showStreet ? "로드뷰 도로 숨기기" : "로드뷰 도로 표시";
    } catch (_error) {
      onError("로드뷰 촬영 도로를 표시하지 못했습니다.");
    }
  });
  return {
    initialize() {
      type.disabled = !getMap();
      street.disabled = !getMap() || typeof getMaps().StreetLayer !== "function";
    }
  };
}
