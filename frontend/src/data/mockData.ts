import type {
  AccountKey,
  CategoryDatum,
  PeriodKey,
  Transaction,
} from "../types";

export const periodOptions: PeriodKey[] = [
  "Today",
  "This Week",
  "This Month",
  "Last Month",
  "Last 3 Months",
  "This Year",
  "Custom Range",
];

export const accountOptions: AccountKey[] = [
  "All Accounts",
  "Checking",
  "Savings",
  "Credit Card",
  "Investment",
];

export const periodData = {
  Today: {
    label: "Sep 28, 2026",
    income: 7200,
    expenses: 2860,
    previousIncome: 6800,
    previousExpenses: 3100,
    balance: 1248500,
  },

  "This Week": {
    label: "Sep 22 – Sep 28, 2026",
    income: 35500,
    expenses: 21800,
    previousIncome: 32700,
    previousExpenses: 22900,
    balance: 1248500,
  },

  "This Month": {
    label: "Sep 1 – Sep 30, 2026",
    income: 142000,
    expenses: 84250,
    previousIncome: 141448,
    previousExpenses: 88405,
    balance: 1248500,
  },

  "Last Month": {
    label: "Aug 1 – Aug 31, 2026",
    income: 141448,
    expenses: 88405,
    previousIncome: 132200,
    previousExpenses: 91700,
    balance: 1197700,
  },

  "Last 3 Months": {
    label: "Jul 1 – Sep 30, 2026",
    income: 417600,
    expenses: 258900,
    previousIncome: 389200,
    previousExpenses: 271400,
    balance: 1248500,
  },

  "This Year": {
    label: "Jan 1 – Sep 30, 2026",
    income: 1264800,
    expenses: 751200,
    previousIncome: 1170000,
    previousExpenses: 782500,
    balance: 1248500,
  },

  "Custom Range": {
    label: "Sep 1 – Sep 28, 2026",
    income: 132400,
    expenses: 79350,
    previousIncome: 128900,
    previousExpenses: 81800,
    balance: 1248500,
  },
} satisfies Record<
  PeriodKey,
  {
    label: string;
    income: number;
    expenses: number;
    previousIncome: number;
    previousExpenses: number;
    balance: number;
  }
>;

export const accountFactors: Record<
  AccountKey,
  {
    income: number;
    expenses: number;
    balance: number;
  }
> = {
  "All Accounts": {
    income: 1,
    expenses: 1,
    balance: 1,
  },

  Checking: {
    income: 0.62,
    expenses: 0.54,
    balance: 0.48,
  },

  Savings: {
    income: 0,
    expenses: 0.08,
    balance: 0.38,
  },

  "Credit Card": {
    income: 0,
    expenses: 0.31,
    balance: -0.04,
  },

  Investment: {
    income: 0.38,
    expenses: 0.07,
    balance: 0.18,
  },
};

export const categoryBase: CategoryDatum[] = [
  {
    name: "Housing",
    amount: 28000,
    count: 4,
  },

  {
    name: "Food",
    amount: 12450,
    count: 37,
  },

  {
    name: "Shopping",
    amount: 9200,
    count: 11,
  },

  {
    name: "Transport",
    amount: 6840,
    count: 19,
  },

  {
    name: "Entertainment",
    amount: 4320,
    count: 8,
  },

  {
    name: "Utilities",
    amount: 3150,
    count: 6,
  },

    {
    name: "Subscriptions",
    amount: 1299,
    count: 1,
  },
];

export const workspaceTransactions: Transaction[] = [
  {
    id: "txn-001",
    merchant: "Fresh Market",
    category: "Food",
    account: "Credit Card",
    date: "Sep 28, 2026",
    time: "10:32 AM",
    amount: -2450,
    status: "Completed",
    type: "expense",
    method: "Credit Card",
    note: "Weekly groceries",
  },

  {
    id: "txn-002",
    merchant: "Acme Technologies",
    category: "Income",
    account: "Checking",
    date: "Sep 27, 2026",
    time: "9:00 AM",
    amount: 142000,
    status: "Completed",
    type: "income",
    method: "Bank Transfer",
    note: "Monthly salary",
  },

  {
    id: "txn-003",
    merchant: "Urban Living",
    category: "Housing",
    account: "Checking",
    date: "Sep 26, 2026",
    time: "8:15 AM",
    amount: -28000,
    status: "Completed",
    type: "expense",
    method: "Bank Transfer",
    note: "September rent",
  },

  {
    id: "txn-004",
    merchant: "Metro Transit",
    category: "Transport",
    account: "Credit Card",
    date: "Sep 25, 2026",
    time: "7:42 PM",
    amount: -850,
    status: "Completed",
    type: "expense",
    method: "Credit Card",
    note: "Monthly transit",
  },

  {
    id: "txn-005",
    merchant: "StreamFlix",
    category: "Subscriptions",
    account: "Credit Card",
    date: "Sep 24, 2026",
    time: "12:10 PM",
    amount: -649,
    status: "Completed",
    type: "expense",
    method: "Credit Card",
    note: "Monthly subscription",
  },

  {
    id: "txn-006",
    merchant: "Tech World",
    category: "Shopping",
    account: "Credit Card",
    date: "Sep 23, 2026",
    time: "3:26 PM",
    amount: -4200,
    status: "Pending",
    type: "expense",
    method: "Credit Card",
    note: "Electronics purchase",
  },
];

export const examples = [
  "How much did I spend on food this month?",
  "What was my biggest expense last month?",
  "How much did I save this year?",
  "Show my income versus expenses",
];