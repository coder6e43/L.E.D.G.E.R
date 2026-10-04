export function formatMoney(
  value: number,
  compact = false
) {
  if (compact && Math.abs(value) >= 100000) {
    return `₹${(value / 100000).toFixed(2)}L`;
  }

  return `${value < 0 ? "−" : ""}₹${Math.abs(
    Math.round(value)
  ).toLocaleString("en-IN")}`;
}

export function percentChange(
  current: number,
  previous: number
) {
  return previous
    ? ((current - previous) / previous) * 100
    : 0;
}