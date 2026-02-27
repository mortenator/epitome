/**
 * callTimes.ts — Call time auto-calculation utilities
 *
 * Industry standard structure (from Epitome dev notes):
 *   Production call  = General Crew call − 60 min
 *   Breakfast RTS    = General Crew call − 30 min  (= Production + 30 min)
 *   General Crew     = anchor / primary call time
 *   Talent call      = independently set (not auto-derived)
 */

/** Parse a time string like "7:00 AM", "07:00", "7a" into total minutes from midnight. Returns null if unparseable. */
export function parseTime(raw?: string): number | null {
  if (!raw || raw.toUpperCase() === "TBD" || raw.trim() === "") return null;

  // Normalize shorthand: "7a" → "7 AM", "7p" → "7 PM"
  const cleaned = raw.trim().toUpperCase()
    .replace(/^(\d{1,2}(?::\d{2})?)\s*A$/, "$1 AM")
    .replace(/^(\d{1,2}(?::\d{2})?)\s*P$/, "$1 PM");

  // Match formats: "7:30 AM", "7:30AM", "07:30", "730 AM", "7 AM"
  const patterns: RegExp[] = [
    /^(\d{1,2}):(\d{2})\s*(AM|PM)$/,   // 7:30 AM
    /^(\d{1,2})(\d{2})\s*(AM|PM)$/,    // 730 AM
    /^(\d{1,2})\s*(AM|PM)$/,           // 7 AM
    /^(\d{1,2}):(\d{2})$/,             // 07:30 (24h)
    /^(\d{1,2})$/,                      // "7" alone
  ];

  for (const re of patterns) {
    const m = cleaned.match(re);
    if (!m) continue;

    let hours   = parseInt(m[1], 10);
    const mins  = m[2] && m[2].length === 2 ? parseInt(m[2], 10) : 0;
    const ampm  = m[3] || (m[2] === "AM" || m[2] === "PM" ? m[2] : undefined);

    if (ampm === "PM" && hours < 12) hours += 12;
    if (ampm === "AM" && hours === 12) hours = 0;

    // Heuristic for 24h bare numbers: 0–6 = PM, 7+ = AM
    if (!ampm && hours <= 6) hours += 12;

    return hours * 60 + mins;
  }

  return null;
}

/** Format total minutes from midnight to a display string like "6:30 AM" */
export function formatTime(totalMins: number): string {
  const normalized = ((totalMins % 1440) + 1440) % 1440; // wrap around midnight
  const h24 = Math.floor(normalized / 60);
  const m   = normalized % 60;
  const ampm = h24 >= 12 ? "PM" : "AM";
  const h12  = h24 % 12 === 0 ? 12 : h24 % 12;
  const mm   = m.toString().padStart(2, "0");
  return `${h12}:${mm} ${ampm}`;
}

export interface DerivedCallTimes {
  productionCall:  { value: string; derived: boolean };
  breakfastCall:   { value: string; derived: boolean };
  generalCrewCall: { value: string; derived: boolean };
}

/**
 * Given whatever call times the API returned, fill in the missing ones.
 * Returns each time with a `derived` flag so the UI can show a visual indicator.
 */
export function deriveCallTimes(
  generalCrewCall?: string,
  productionCall?: string,
  breakfastCall?: string
): DerivedCallTimes | null {

  // We need at least one anchor to work with
  const crewMins  = parseTime(generalCrewCall);
  const prodMins  = parseTime(productionCall);
  const bfastMins = parseTime(breakfastCall);

  // Priority: general crew is the canonical anchor; production is second
  let anchor: number | null = null;
  let anchorType: "crew" | "production" | "breakfast" | null = null;

  if (crewMins !== null) {
    anchor = crewMins;
    anchorType = "crew";
  } else if (prodMins !== null) {
    anchor = prodMins + 60; // derive crew from production (+60)
    anchorType = "production";
  } else if (bfastMins !== null) {
    anchor = bfastMins + 30; // derive crew from breakfast (+30)
    anchorType = "breakfast";
  }

  if (anchor === null) return null; // can't derive anything without any anchor

  const computedCrew  = anchor;
  const computedProd  = anchor - 60;
  const computedBfast = anchor - 30;

  return {
    generalCrewCall: {
      value:   crewMins !== null ? generalCrewCall! : formatTime(computedCrew),
      derived: crewMins === null,
    },
    productionCall: {
      value:   prodMins !== null ? productionCall! : formatTime(computedProd),
      derived: prodMins === null,
    },
    breakfastCall: {
      value:   bfastMins !== null ? breakfastCall! : formatTime(computedBfast),
      derived: bfastMins === null,
    },
  };
}
