import { useEffect, useState } from "react";
import { Icon } from "../common/Icon";

type Period =
  | "This Month"
  | "Last Month"
  | "This Week"
  | "Year to Date"
  | "Custom Range";

type FilterBarProps = {
  onDateRangeChange: (start: string, end: string) => void;
};

function formatDate(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function getDatesForPeriod(period: Period): { start: string; end: string } | null {
  const now = new Date();

  if (period === "This Month") {
    return {
      start: formatDate(new Date(now.getFullYear(), now.getMonth(), 1)),
      end: formatDate(now),
    };
  }

  if (period === "Last Month") {
    return {
      start: formatDate(new Date(now.getFullYear(), now.getMonth() - 1, 1)),
      end: formatDate(new Date(now.getFullYear(), now.getMonth(), 0)),
    };
  }

  if (period === "This Week") {
    const day = now.getDay();
    const mondayOffset = day === 0 ? -6 : 1 - day;

    const start = new Date(now);
    start.setDate(now.getDate() + mondayOffset);

    return {
      start: formatDate(start),
      end: formatDate(now),
    };
  }

  if (period === "Year to Date") {
    return {
      start: formatDate(new Date(now.getFullYear(), 0, 1)),
      end: formatDate(now),
    };
  }

  return null;
}

function formatPeriodLabel(start: string, end: string): string {
  if (!start || !end) return "Select a date range";

  const startDate = new Date(`${start}T00:00:00`);
  const endDate = new Date(`${end}T00:00:00`);

  const sameMonth =
    startDate.getFullYear() === endDate.getFullYear() &&
    startDate.getMonth() === endDate.getMonth();

  if (sameMonth) {
    return startDate.toLocaleDateString("en-IN", {
      month: "long",
      year: "numeric",
    });
  }

  return `${startDate.toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  })} – ${endDate.toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  })}`;
}

export function FilterBar({ onDateRangeChange }: FilterBarProps) {
  const [period, setPeriod] = useState<Period>("This Month");
  const initialRange = getDatesForPeriod("This Month");

  const [startDate, setStartDate] = useState(initialRange?.start ?? "");
  const [endDate, setEndDate] = useState(initialRange?.end ?? "");
  const [validation, setValidation] = useState("");

  useEffect(() => {
    if (initialRange) {
      onDateRangeChange(initialRange.start, initialRange.end);
    }
    // Intentionally run once when the filter mounts.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function handlePeriodChange(nextPeriod: Period) {
    setPeriod(nextPeriod);
    setValidation("");

    const range = getDatesForPeriod(nextPeriod);

    if (!range) {
      return;
    }

    setStartDate(range.start);
    setEndDate(range.end);
    onDateRangeChange(range.start, range.end);
  }

  function handleCustomDateChange(
    type: "start" | "end",
    value: string,
  ) {
    setPeriod("Custom Range");
    setValidation("");

    const nextStart = type === "start" ? value : startDate;
    const nextEnd = type === "end" ? value : endDate;

    if (nextStart && nextEnd && nextStart > nextEnd) {
      setValidation("The start date cannot be after the end date.");
    }

    if (type === "start") {
      setStartDate(value);
    } else {
      setEndDate(value);
    }

    if (
      nextStart &&
      nextEnd &&
      nextStart <= nextEnd
    ) {
      onDateRangeChange(nextStart, nextEnd);
    }
  }

  return (
    <section className="workspace-filters" aria-label="Dashboard date filters">
      <div className="active-period">
        <Icon name="calendar" size={18} />
        <span>
          <small>Reporting period</small>
          <strong>{formatPeriodLabel(startDate, endDate)}</strong>
        </span>
      </div>

      <label className="select-control">
        <span>Date range</span>
        <select
          value={period}
          onChange={(event) =>
            handlePeriodChange(event.target.value as Period)
          }
        >
          <option value="This Month">This Month</option>
          <option value="Last Month">Last Month</option>
          <option value="This Week">This Week</option>
          <option value="Year to Date">Year to Date</option>
          <option value="Custom Range">Custom Range</option>
        </select>
      </label>

      {period === "Custom Range" && (
        <div className="custom-dates">
          <label>
            <span>From</span>
            <input
              type="date"
              value={startDate}
              onChange={(event) =>
                handleCustomDateChange("start", event.target.value)
              }
            />
          </label>

          <label>
            <span>To</span>
            <input
              type="date"
              value={endDate}
              onChange={(event) =>
                handleCustomDateChange("end", event.target.value)
              }
            />
          </label>
        </div>
      )}

      {validation && (
        <p className="validation" role="alert">
          {validation}
        </p>
      )}
    </section>
  );
}