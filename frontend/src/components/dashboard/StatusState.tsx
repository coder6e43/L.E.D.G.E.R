import { Icon } from "../common/Icon";
import type { IconName } from "../common/Icon";
import { Button } from "../common/Button";
import type { ResultState } from "../../types";

export function StatusState({ type, onAction }: { type: Exclude<ResultState, "idle" | "loading" | "success">; onAction: (next?: ResultState) => void }) {
  const content = {
    clarification: {
      icon: "clock" as IconName,
      eyebrow: "Clarification required",
      title: "Which date range should be used?",
      body: <>“Recently” can mean different things. Choose a range so the result uses the period you intend.</>,
    },
    refusal: {
      icon: "shield" as IconName,
      eyebrow: "Unable to answer",
      title: "This request isn’t supported",
      body: <>This request cannot be answered reliably using the available financial data. No numerical result has been generated.</>,
    },
    empty: {
      icon: "search" as IconName,
      eyebrow: "No matching transactions",
      title: "We couldn’t find any matching records",
      body: <>No Food transactions were found for <strong>August 2026</strong>. Try changing the date range or category.</>,
    },
    error: {
      icon: "warning" as IconName,
      eyebrow: "System error",
      title: "Unable to load result",
      body: <>Something went wrong while processing your request. Your data was not changed.</>,
    },
  }[type];
  return (
    <section className={`state-card state-${type}`}>
      <div className="state-icon"><Icon name={content.icon} size={25} /></div>
      <div className="state-content">
        <p className="state-eyebrow">{content.eyebrow}</p>
        <h3>{content.title}</h3>
        <p>{content.body}</p>
        {type === "clarification" && <div className="state-actions"><Button className="primary" onClick={() => onAction("success")}>This month</Button><Button onClick={() => onAction("success")}>Last 30 days</Button><Button><Icon name="calendar" size={17} /> Choose date range</Button></div>}
        {type === "refusal" && <div className="supported"><span>Try asking about</span><b>Expenses</b><b>Categories</b><b>Date ranges</b><b>Budgets</b></div>}
        {type === "empty" && <Button onClick={() => onAction()}><Icon name="refresh" size={17} /> Change question</Button>}
        {type === "error" && <Button className="primary" onClick={() => onAction()}><Icon name="refresh" size={17} /> Try again</Button>}
      </div>
    </section>
  );
}
