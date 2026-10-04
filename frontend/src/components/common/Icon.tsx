import type { ReactNode } from "react";

export type IconName =
  | "arrow"
  | "budget"
  | "calendar"
  | "chart"
  | "check"
  | "chevron"
  | "clock"
  | "food"
  | "grid"
  | "info"
  | "logout"
  | "moon"
  | "receipt"
  | "refresh"
  | "search"
  | "shield"
  | "spark"
  | "sun"
  | "user"
  | "wallet"
  | "warning"
  | "x";

const PATHS: Record<IconName, ReactNode> = {
  arrow: (
    <>
      <path d="M5 12h14M13 6l6 6-6 6" />
    </>
  ),

  budget: (
    <>
      <path d="M4 7h16v11H4z" />
      <path d="M16 11h4v4h-4a2 2 0 0 1 0-4ZM7 7V5h10v2" />
    </>
  ),

  calendar: (
    <>
      <rect x="3" y="5" width="18" height="16" rx="2" />
      <path d="M16 3v4M8 3v4M3 10h18" />
    </>
  ),

  chart: (
    <>
      <path d="M4 19V9M10 19V5M16 19v-7M22 19H2" />
    </>
  ),

  check: (
    <>
      <path d="m5 12 4 4L19 6" />
    </>
  ),

  chevron: (
    <>
      <path d="m9 18 6-6-6-6" />
    </>
  ),

  clock: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3 2" />
    </>
  ),

  food: (
    <>
      <path d="M7 3v8M4 3v5a3 3 0 0 0 6 0V3M7 11v10M16 3v18M16 3c3 2 4 5 4 9h-4" />
    </>
  ),

  grid: (
    <>
      <rect x="3" y="3" width="7" height="7" rx="1" />
      <rect x="14" y="3" width="7" height="7" rx="1" />
      <rect x="3" y="14" width="7" height="7" rx="1" />
      <rect x="14" y="14" width="7" height="7" rx="1" />
    </>
  ),

  info: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 11v6M12 7h.01" />
    </>
  ),

  logout: (
    <>
      <path d="M10 5H5v14h5M14 8l4 4-4 4M18 12H9" />
    </>
  ),

  moon: (
    <>
      <path d="M20 15.2A8.5 8.5 0 0 1 8.8 4a8.5 8.5 0 1 0 11.2 11.2Z" />
    </>
  ),

  receipt: (
    <>
      <path d="M6 3h12v18l-3-2-3 2-3-2-3 2zM9 8h6M9 12h6" />
    </>
  ),

  refresh: (
    <>
      <path d="M20 7v5h-5M4 17v-5h5M6 8a7 7 0 0 1 12-2l2 6M18 16a7 7 0 0 1-12 2l-2-6" />
    </>
  ),

  search: (
    <>
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-4-4" />
    </>
  ),

  shield: (
    <>
      <path d="M12 3 5 6v5c0 5 3 8 7 10 4-2 7-5 7-10V6z" />
      <path d="m9 12 2 2 4-4" />
    </>
  ),

  spark: (
    <>
      <path d="m12 3 1.3 4.2L17 9l-3.7 1.8L12 15l-1.3-4.2L7 9l3.7-1.8zM19 15l.7 2.3L22 18l-2.3.7L19 21l-.7-2.3L16 18l2.3-.7z" />
    </>
  ),

  sun: (
    <>
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M4.93 4.93l1.42 1.42M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.42-1.42M17.66 6.34l1.41-1.41" />
    </>
  ),

  user: (
    <>
      <circle cx="12" cy="8" r="4" />
      <path d="M4 21a8 8 0 0 1 16 0" />
    </>
  ),

  wallet: (
    <>
      <path d="M3 6h16v14H3zM3 8V5a2 2 0 0 1 2-2h11v3M15 12h6v4h-6a2 2 0 0 1 0-4Z" />
    </>
  ),

  warning: (
    <>
      <path d="M12 4 3 20h18zM12 9v5M12 17h.01" />
    </>
  ),

  x: (
    <>
      <path d="m6 6 12 12M18 6 6 18" />
    </>
  ),
};

type IconProps = {
  name: IconName;
  size?: number;
};

export function Icon({
  name,
  size = 20,
}: IconProps) {
  return (
    <svg
      className="icon"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {PATHS[name]}
    </svg>
  );
}