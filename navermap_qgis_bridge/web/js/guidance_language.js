// SPDX-License-Identifier: GPL-2.0-or-later
// Display-only translation of NAVER's Korean instruction templates. Never mutate
// saved guides or request a new (potentially different) traffic-dependent route.
// Maneuver terminology: https://api.ncloud-docs.com/docs/application-maps-directions5
const englishManeuvers = {
  "직진": "Continue straight", "직진 방향": "Continue straight", "좌회전": "Turn left", "우회전": "Turn right",
  "유턴": "Make a U-turn", "비보호 좌회전": "Make an unprotected left turn",
  "좌측방향": "Keep left", "우측방향": "Keep right",
  "좌측 방향": "Keep left", "우측 방향": "Keep right",
  "왼쪽 방향": "Keep left", "오른쪽 방향": "Keep right",
  "왼쪽": "Keep left", "오른쪽": "Keep right",
  "경유지": "Waypoint", "경유지 도착": "Arrive at the waypoint",
  "목적지": "Destination", "목적지 도착": "Arrive at the destination",
  "도착지": "Destination", "도착": "Arrive at the destination",
  "톨게이트": "Tollgate", "요금소": "Tollgate",
  "하이패스 전용 톨게이트": "Hi-pass-only tollgate",
  "하이패스 전용 요금소": "Hi-pass-only tollgate",
  "무정차 톨게이트": "One-tolling tollgate",
  "톨게이트 통과": "Pass through the tollgate", "요금소 통과": "Pass through the tollgate",
  "하이패스 전용 톨게이트 통과": "Pass through the Hi-pass-only tollgate"
};

function englishManeuver(text) {
  if (Object.prototype.hasOwnProperty.call(englishManeuvers, text)) return englishManeuvers[text];
  const combined = text.match(/^(.+?)\s+후\s+(.+)$/);
  if (combined) {
    const first = englishManeuver(combined[1]), next = englishManeuver(combined[2]);
    if (first && next) return `${first}, then ${next.charAt(0).toLowerCase()}${next.slice(1)}`;
  }
  const clock = text.match(/^(?:(왼쪽|오른쪽|좌측|우측)\s+)?(\d{1,2})시(?:\s*방향)?\s*(좌회전|우회전|방향)?$/);
  if (clock && Number(clock[2]) >= 1 && Number(clock[2]) <= 12) {
    const left = clock[3] === "좌회전" || ["왼쪽", "좌측"].includes(clock[1]);
    const right = clock[3] === "우회전" || ["오른쪽", "우측"].includes(clock[1]);
    return `${left ? "Turn left" : right ? "Turn right" : "Head"} at ${clock[2]} o'clock`;
  }
  const roundabout = text.match(/^(회전\s*교차로|로터리)(?:에서)?\s+(.+)$/);
  if (roundabout) {
    const action = englishManeuver(roundabout[2]);
    return action ? `${action} at the roundabout` : null;
  }
  const sideRoad = text.match(/^(?:(고가차도|고가도로|지하차도|지하도로)\s+)?(왼쪽|오른쪽|좌측|우측)\s+옆길(?:로|으로)?(?:\s*진입)?$/);
  if (sideRoad) {
    const side = ["왼쪽", "좌측"].includes(sideRoad[2]) ? "left" : "right";
    const structure = sideRoad[1] ? ` beside the ${sideRoad[1].startsWith("고가") ? "overpass" : "underpass"}` : "";
    return `Take the side road on the ${side}${structure}`;
  }
  const transition = text.match(/^(?:(왼쪽|오른쪽|좌측|우측|전방|정면)\s+)?(고속도로|도시고속도로|자동차전용도로|고가차도|고가도로|지하차도|지하도로|고가차도 옆길|지하차도 옆길|도로|옆길|본선|휴게소|페리항로|분기점|갈림길)(?:로|으로)?\s*(진입|진출|합류|입구|출구)$/);
  if (transition) {
    const roads = {"고속도로":"expressway", "도시고속도로":"urban expressway",
      "자동차전용도로":"motorway", "고가차도":"overpass", "고가도로":"overpass",
      "지하차도":"underpass", "지하도로":"underpass", "고가차도 옆길":"side road beside the overpass",
      "지하차도 옆길":"side road beside the underpass", "본선":"main road", "휴게소":"rest area",
      "페리항로":"ferry route", "분기점":"branch road", "갈림길":"branch road",
      "도로":"road", "옆길":"side road"};
    const side = {"왼쪽":" on the left", "좌측":" on the left", "오른쪽":" on the right",
      "우측":" on the right", "전방":" ahead", "정면":" ahead"}[transition[1]] || "";
    const verb = {"진입":"Enter", "입구":"Enter", "진출":"Exit", "출구":"Exit", "합류":"Merge onto"}[transition[3]];
    return `${verb} the ${roads[transition[2]]}${side}`;
  }
  return null;
}

function localizedGuidance(guide) {
  const original = String(guide.guidance || guide.name || "").trim();
  if (!original) return uiText("경로 안내");
  if (mapLanguage !== "en") return original;
  // Already-English and unfamiliar instructions stay intact. Only recognized
  // templates are rewritten; names are opaque text, including quoted names.
  const direct = englishManeuver(original);
  if (direct) return direct;
  const context = original.match(/^(?:(.+?)에서\s+)?(?:(.+?)\s+방면으로\s+)?(.+)$/);
  if (context && (context[1] || context[2])) {
    const action = englishManeuver(context[3]);
    const place = /^(회전\s*교차로|로터리)$/.test(context[1] || "") ? "the roundabout" : context[1];
    if (action) return action + (place ? ` at ${place}` : "") + (context[2] ? ` towards ${context[2]}` : "");
  }
  return original;
}
