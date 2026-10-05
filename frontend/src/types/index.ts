export type PeriodKey =
  | "Today"
  | "This Week"
  | "This Month"
  | "Last Month"
  | "Last 3 Months"
  | "This Year"
  | "Custom Range";

export type AccountKey =
  | "All Accounts"
  | "Checking"
  | "Savings"
  | "Credit Card"
  | "Investment";

export type TransactionStatus =
  | "Completed"
  | "Pending"
  | "Failed";

export type TransactionType =
  | "income"
  | "expense";

export type Transaction = {
  id: string;
  merchant: string;
  category: string;
  account: Exclude<AccountKey, "All Accounts">;
  date: string;
  time: string;
  amount: number;
  status: TransactionStatus;
  type: TransactionType;
  method: string;
  note: string;
};

export type ResultState =
  | "idle"
  | "loading"
  | "success"
  | "clarification"
  | "refusal"
  | "empty"
  | "error";

export type Analytics = {
  periodLabel: string;
  income: number;
  expenses: number;
  net: number;
  balance: number;
  savingsRate: number;
  previousIncome: number;
  previousExpenses: number;
  previousNet: number;
  previousSavingsRate: number;
};

export type DrillFilter =
  | "all"
  | "income"
  | "expenses"
  | "savings"
  | string;

export type CategoryDatum = {
  name: string;
  amount: number;
  count: number;
  currency?: string;
};

export type Theme = "light" | "dark";
