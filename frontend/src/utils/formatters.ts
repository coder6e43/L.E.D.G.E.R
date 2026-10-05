export function formatMoney(
  value: number,
  currencyOrCompact: string | boolean = false,
  compact = false
) {
  const currency = typeof currencyOrCompact === "string" ? currencyOrCompact : "INR";
  const useCompact = typeof currencyOrCompact === "boolean" ? currencyOrCompact : compact;
  if (currency === "INR") {
    if (useCompact && Math.abs(value) >= 100000) return `${value < 0 ? "−" : ""}₹${(Math.abs(value) / 100000).toFixed(2)}L`;
    return `${value < 0 ? "−" : ""}₹${Math.abs(Math.round(value)).toLocaleString("en-IN")}`;
  }
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    notation: useCompact ? "compact" : "standard",
    maximumFractionDigits: 2,
  }).format(value);
}

export function percentChange(
  current: number,
  previous: number
) {
  return previous
    ? ((current - previous) / previous) * 100
    : 0;
}
