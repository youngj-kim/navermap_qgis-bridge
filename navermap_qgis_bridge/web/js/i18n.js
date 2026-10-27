// SPDX-License-Identifier: GPL-2.0-or-later
// Translate application-owned strings only. Place names, addresses, user input
// are data and are never rewritten by this dictionary. Guidance templates have
// their own display-only translator in guidance_language.js.
const englishUi = {
  "표시할 경로 안내가 없습니다.": "No route instructions to display.",
  "경로 안내 없음": "No route instructions",
  "파일 불러오기": "Import files", "전체 선택": "Select all", "선택": "Select",
  "선택 삭제 ({0})": "Delete selected ({0})",
  "탐색창 접기 ▴": "Hide panel ▴", "탐색창 펼치기 ▾": "Show panel ▾",
  "지도와 로드뷰 배치": "Map and Street View layout",
  "지도 위 / 로드뷰 아래": "Map above / Street View below",
  "로드뷰 위 / 지도 아래": "Street View above / Map below",
  "지도 좌 / 로드뷰 우": "Map left / Street View right",
  "로드뷰 좌 / 지도 우": "Street View left / Map right",
  "영문 지도로 전환": "Switch to English", "한국어 지도로 전환": "Switch to Korean",
  "전체화면 전환": "Toggle full screen", "장소, 주소 또는 좌표 검색": "Search places, addresses or coordinates",
  "장소, 주소 또는 경도,위도 검색": "Place, address or lon,lat",
  "장소, 주소 또는 경도,위도": "Place, address or lon,lat",
  "검색": "Search", "검색 지우기": "Clear search", "지도": "Map",
  "일반지도": "Standard", "위성영상": "Satellite", "위성영상+지명": "Hybrid",
  "로드뷰 도로 표시": "Show coverage", "로드뷰 도로 숨기기": "Hide coverage",
  "역방향 대기": "Waiting for sync", "경로 탐색": "Route planner", "경로": "Route",
  "경로 유형": "Route type", "실시간 최적": "Real-time optimal", "실시간 빠른길": "Real-time fastest",
  "실시간 편한길": "Real-time comfortable", "회피 0": "Avoid 0", "차량": "Vehicle",
  "경로 회피 옵션": "Route avoidance", "차량 설정": "Vehicle settings", "경유지 추가": "Add stop",
  "+ 경유지": "+ Stop", "하나만 선택할 수 있으며, 선택 시 위 경로 유형을 대체합니다.": "Choose one option. It replaces the route type above.",
  "무료 우선": "Prefer toll-free", "자동차전용도로 회피": "Avoid motorways", "차종": "Type", "유종": "Fuel",
  "소형": "Small", "중형": "Medium", "대형": "Large", "대형 화물": "Heavy truck",
  "특수 화물": "Special truck", "경차": "Mini", "이륜차": "Motorcycle",
  "휘발유": "Gasoline", "고급 휘발유": "Premium gasoline", "경유": "Diesel",
  "공개 경로 API에 하이패스 보유 여부를 지정하는 옵션이 없습니다. 하이패스 전용 톨게이트 안내는 응답에 포함될 수 있습니다.": "The public routing API has no Hi-Pass ownership option. Guidance may include Hi-Pass-only toll gates.",
  "하이패스 경로 설정 (API 미지원)": "Hi-Pass routing (unsupported)",
  "출발": "From", "도착": "To", "출발지": "Origin", "도착지": "Destination",
  "현재 위치": "Map center", "현재 지도 중심을 출발지로 사용": "Use map center as origin",
  "현재 지도 중심을 도착지로 사용": "Use map center as destination", "경유지 목록": "Stops",
  "경로 생성": "Get route", "취소": "Cancel", "이력": "History", "경로 이력 열기": "Open route history",
  "출발지와 도착지 바꾸기": "Swap origin and destination", "경로 입력 초기화": "Reset route inputs",
  "경로 안내": "Directions", "경로 정보": "Route information", "안내": "Directions",
  "경로 안내 접기": "Collapse directions", "경로 안내 펼치기": "Expand directions",
  "순서별 경로 안내": "Turn-by-turn directions", "경로 이력": "Route history", "검색 결과": "Search results",
  "지도와 로드뷰 크기 조절": "Resize map and Street View", "지도와 로드뷰 위치 전환": "Swap map and Street View",
  "촬영일 정보 없음": "Capture date unavailable", "네이버 지도에서 열기": "Open in NAVER Maps",
  " (기존 복수 설정)": " (legacy multiple options)",
  ", 과거 하이패스 설정 (계산 미반영)": ", legacy Hi-Pass setting (not used in routing)",
  "JS 보류: QGIS 동기화 중": "JS deferred: syncing QGIS", "JS 실패: QGIS bridge 없음": "JS failed: no QGIS bridge",
  "JS 실패: 지도 위치 전달 오류": "JS failed: map position delivery", "JS 이벤트 수신": "JS event received",
  "NAVER dragend 감지": "NAVER dragend detected", "지도 pointerdown 감지": "Map pointerdown detected",
  "지도 pointerup 감지": "Map pointerup detected", "Naver Directions 경로를 탐색하고 있습니다...": "Finding a route with NAVER Directions...",
  "POI 검색 응답 시간이 초과되었습니다.": "Place search timed out.",
  "POI 검색 응답을 해석하지 못했습니다.": "Could not read the place search response.",
  "POI 검색에 실패했습니다.": "Place search failed.", "POI/주소 검색 결과가 없습니다.": "No places or addresses found.",
  "QGIS bridge 연결 중...": "Connecting to QGIS...", "QGIS bridge 연결을 다시 시도하고 있습니다...": "Retrying QGIS connection...",
  "QGIS 경로 이력 연결이 준비되지 않았습니다.": "The QGIS route history connection is not ready.",
  "QGIS 연결이 준비된 뒤 지도 언어를 전환하세요.": "Wait for the QGIS connection before switching languages.",
  "검색 결과가 없습니다.": "No results found.", "검색이 끝난 뒤 지도 언어를 전환하세요.": "Wait for the search to finish before switching languages.",
  "출": "S", "도": "E", "경": "W",
  "경로 안내 목록을 표시하지 못했습니다.": "Could not display directions.",
  "경로 요청을 전달하지 못했습니다. 연결을 확인하세요.": "Could not send the route request. Check the connection.",
  "경로 응답을 받지 못했습니다. 연결을 확인한 뒤 다시 조회하세요.": "No route response received. Check the connection and retry.",
  "경로 이력 목록을 표시하지 못했습니다.": "Could not display route history.",
  "경로 이력을 열었습니다.": "Route history opened.", "경로 이력을 입력창으로 불러오지 못했습니다.": "Could not load route history into the inputs.",
  "경로 이력을 확인하고 있습니다.": "Loading route history...", "경로 지점을 초기화했습니다.": "Route points reset.",
  "경로 탐색을 취소했습니다.": "Route search cancelled.", "경로 회피 옵션 없음": "No avoidance options",
  "경유지를 삭제했습니다.": "Stop removed.", "불러오기": "Load", "삭제": "Delete", "내보내기": "Export",
  "선택한 이력을 경로 입력창으로 불러왔습니다.": "Selected history loaded into route inputs.",
  "아직 경로 이력이 없습니다.": "No route history yet.", "영문 지도로 전환했습니다.": "Switched to English.",
  "한국어 지도로 전환했습니다.": "Switched to Korean.", "외부 브라우저 연동 모드로 QGIS와 연결했습니다.": "Connected to QGIS in external browser mode.",
  "이력 입력 정보를 찾지 못했습니다.": "Could not find the saved route inputs.",
  "이전 이력의 복수 회피 설정은 당시 요청에 적용된 무료 우선으로 불러왔습니다.": "Legacy avoidance options loaded as toll-free preference, matching the original request.",
  "입력 좌표": "Input coordinates", "입력값을 좌표나 장소로 해석할 수 없습니다.": "Enter valid coordinates or a place.",
  "전체화면 전환을 사용할 수 없습니다.": "Full screen is unavailable.", "주소 검색 결과": "Address result",
  "주소 검색 중 오류가 발생했습니다.": "An error occurred during address search.",
  "지도 위치를 전달하지 못했습니다. 다시 이동해 주세요.": "Could not send the map position. Move the map again.",
  "지도 확대 비율을 맞추지 못했습니다.": "Could not match the map scale.", "지도 확대 비율을 전달하지 못했습니다.": "Could not send the map scale.",
  "출발지, 경유지, 도착지를 확인하고 있습니다...": "Checking origin, stops and destination...",
  "출발지와 도착지를 바꿨습니다.": "Origin and destination swapped.",
  "프로젝트가 전환되어 현재 경로를 초기화했습니다. 세션 이력은 유지됩니다.": "Project changed. Current route cleared; session history retained.",
  "프로젝트가 전환되었습니다.": "Project changed.", "현재 NAVER 지도 중심을 읽지 못했습니다.": "Could not read the NAVER map center.",
  "현재 화면을 보관하지 못해 언어 전환을 중단했습니다.": "Could not save the current view. Language switch cancelled.",
  "검색어를 입력하세요.": "Enter a search query.", "Naver API HUB Client ID가 필요합니다.": "A NAVER API HUB Client ID is required.",
  "Naver API HUB Client Secret이 필요합니다.": "A NAVER API HUB Client Secret is required.",
  "Naver Client Secret이 필요합니다.": "A NAVER Client Secret is required.",
  "POI 검색 응답에 사용할 수 있는 좌표가 없습니다.": "The place search response has no usable coordinates.",
  "POI 검색 요청 시간이 초과되었습니다.": "Place search timed out.",
  "경로 응답 시간이 초과되었습니다. 다시 조회하세요.": "Route request timed out. Try again.",
  "경로 응답 처리 또는 이력 저장에 실패했습니다.": "Could not process the route response or save history.",
  "경로를 찾지 못했습니다.": "No route found.", "경로 탐색 결과가 없습니다.": "No route results found.",
  "경로 선형 좌표를 찾지 못했습니다.": "Route geometry is missing.",
  "{0}초": "{0} s", "{0}분": "{0} min", "{0} 지정: {1}, {2}": "{0} set: {1}, {2}",
  "{0}번째 경유지를 추가했습니다.": "Added stop {0}.", "JS 좌표 오류: {0}": "JS coordinate error: {0}",
  "JS 호출: {0}, {1}": "JS call: {0}, {1}", "QGIS bridge 준비 중: {0}": "Waiting for QGIS bridge: {0}",
  "경로 유형: {0}": "Route type: {0}", "경로 이력 {0}건": "Route history: {0}",
  "경로 회피 옵션 {0}개 선택": "Selected {0} avoidance option(s)", "경로 회피: {0}": "Avoidance: {0}",
  "경유 {0}": "Stop {0}", "경유지 {0}": "Stop {0}", "경유지 {0} 삭제": "Remove stop {0}",
  "경유지 {0} 아래로 이동": "Move stop {0} down", "경유지 {0} 위로 이동": "Move stop {0} up",
  "경유지 {0}: {1}, ": "Stop {0}: {1}, ", "경유지 {0}개를 포함한 경로를 탐색하고 있습니다...": "Finding a route with {0} stop(s)...",
  "경유지 {0} 순서로 이동했습니다.": "Moved to stop position {0}.", "경유지는 최대 {0}개까지 추가할 수 있습니다.": "You can add up to {0} stops.",
  "도착지: {0}, {1}": "Destination: {0}, {1}", "출발지: {0}, {1}": "Origin: {0}, {1}",
  "안내 {0}개": "{0} instructions", "위치를 찾지 못했습니다: {0}": "Location not found: {0}",
  "차량: {0}, {1}{2}": "Vehicle: {0}, {1}{2}", "촬영일: {0}": "Captured: {0}",
  "현재 지도 중심을 경유지 {0}로 사용": "Use map center as stop {0}", "회피 {0}": "Avoid {0}"
};

// Tagged templates keep interpolated data separate from translation keys.
function uiText(source, ...values) {
  const template = Array.isArray(source);
  const key = template ? source.reduce((text, part, index) => text + (index ? `{${index - 1}}` : "") + part, "") : source;
  const translated = mapLanguage === "en" && Object.prototype.hasOwnProperty.call(englishUi, key) ? englishUi[key] : key;
  return template ? translated.replace(/\{(\d+)\}/g, (_match, index) => String(values[Number(index)])) : translated;
}

function translateViewerStatus(message) {
  const text = String(message);
  if (mapLanguage !== "en") return text;
  if (Object.prototype.hasOwnProperty.call(englishUi, text)) return englishUi[text];
  // This backend summary contains enum labels and numbers, never place names.
  const route = text.match(/^(.*?) 경로 생성 완료: (.*?), 예상 (\d+)분(.*)$/);
  if (route) {
    let details = route[4].replace(/, 경유지 (\d+)개/, ", stops: $1")
      .replace(", 회피: ", ", avoidance: ").replace(", 차량: ", ", vehicle: ");
    details = details.replace(/무료 우선|자동차전용도로 회피|특수 화물|대형 화물|고급 휘발유|휘발유|경유|소형|중형|대형|경차/g, label => englishUi[label] || label);
    return `${uiText(route[1])} route ready: ${route[2]}, estimated ${route[3]} min${details}`;
  }
  const prefixes = {
    "경로 탐색 실패: ": "Route search failed: ", "POI 검색 실패: ": "Place search failed: ",
    "POI 검색 응답 처리 실패: ": "Could not process place search response: "
  };
  for (const [prefix, translation] of Object.entries(prefixes)) {
    if (text.startsWith(prefix)) return translation + text.slice(prefix.length);
  }
  return text;
}

function translateViewerUi() {
  document.documentElement.lang = mapLanguage;
  // Called once before rendering search results, route history or user inputs.
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) {
    const node = walker.currentNode;
    if (node.parentElement.closest("script, style")) continue;
    const key = node.textContent.trim();
    if (Object.prototype.hasOwnProperty.call(englishUi, key)) node.textContent = node.textContent.replace(key, uiText(key));
  }
  document.querySelectorAll("[placeholder], [title], [aria-label]").forEach(element => {
    ["placeholder", "title", "aria-label"].forEach(attribute => {
      if (element.hasAttribute(attribute)) element.setAttribute(attribute, uiText(element.getAttribute(attribute)));
    });
  });
}
