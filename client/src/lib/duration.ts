/**
 * Format a duration in minutes for display.
 *
 * Long waits (overnight chilling, marinating, proofing) would otherwise render
 * as "480 min", so anything an hour or over is shown in hours.
 */
export function formatDuration(minutes: number): string {
  if (minutes < 60) return `${minutes} min`;

  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;

  if (rest === 0) return `${hours} ${hours === 1 ? 'hour' : 'hours'}`;
  return `${hours} h ${rest} min`;
}
