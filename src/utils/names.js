/**
 * Strip the costume bracket prefix from a trainee name.
 * e.g. "[Red Strife] Gold Ship" -> "Gold Ship"
 */
export function getBaseName(traineeName) {
  return traineeName.replace(/\[.*?\]\s*/, '').trim()
}

/**
 * Return display name for a trainee, keeping the costume tag only
 * when another slide shares the same base character name.
 * Format: "Gold Ship [Red Strife]" instead of "[Red Strife] Gold Ship"
 */
export function getDisplayName(traineeName, allTraineeNames) {
  const base = getBaseName(traineeName)
  const siblings = allTraineeNames.filter(n => getBaseName(n) === base)
  if (siblings.length <= 1) return base
  const match = traineeName.match(/\[.*?\]/)
  const tag = match ? match[0] : ''
  return tag ? `${base} ${tag}` : base
}
