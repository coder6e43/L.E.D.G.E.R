export function formatMoney(
  value: number,
  currencyOrCompact: string | boolean = "INR",
  compact = false
) {
  const currency = typeof currencyOrCompact === "string" ? currencyOrCompact : "INR";
  const useCompact = typeof currencyOrCompact === "boolean" ? currencyOrCompact : compact;
  const locale = currency === "INR" ? "en-IN" : "en-US";
  return new Intl.NumberFormat(locale, { style: "currency", currency, notation: useCompact ? "compact" : "standard", maximumFractionDigits: 2 }).format(value);
}

export function percentChange(
  current: number,
  previous: number
) {
  return previous
    ? ((current - previous) / previous) * 100
    : 0;
}
