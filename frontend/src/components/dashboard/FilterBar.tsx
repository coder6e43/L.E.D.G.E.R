import { Icon } from "../common/Icon";
import { periodData, periodOptions, accountOptions } from "../../data/mockData";
import type { PeriodKey, AccountKey } from "../../types";

export function FilterBar({
  period,
  account,
  onPeriod,
  onAccount,
}: {
  period: PeriodKey;
  account: AccountKey;
  onPeriod: (period: PeriodKey) => void;
  onAccount: (account: AccountKey) => void;
}) {
  return (
    <section className="workspace-filters" aria-label="Dashboard filters">
      <div className="active-period"><Icon name="calendar" size={18} /><span><small>Reporting period</small><strong>{periodData[period].label}</strong></span></div>
      <label className="select-control"><span>Date range</span><select value={period} onChange={(event) => onPeriod(event.target.value as PeriodKey)}>{periodOptions.map((option) => <option key={option}>{option}</option>)}</select></label>
      <label className="select-control"><span>Account</span><select value={account} onChange={(event) => onAccount(event.target.value as AccountKey)}>{accountOptions.map((option) => <option key={option}>{option}</option>)}</select></label>
      {period === "Custom Range" && <div className="custom-dates"><label><span>From</span><input type="date" defaultValue="2026-09-01" /></label><label><span>To</span><input type="date" defaultValue="2026-09-28" /></label></div>}
    </section>
  );
}
