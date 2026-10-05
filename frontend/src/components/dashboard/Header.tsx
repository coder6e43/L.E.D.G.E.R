import { Icon } from "../common/Icon";
import { Button } from "../common/Button";
import { Brand } from "../common/Brand";
import type { LedgerUser } from "../../services/api";
import { Link, useLocation } from "react-router";

type HeaderProps = {
  onLogout: () => void;
  theme: "light" | "dark";
  onTheme: () => void;
  user: LedgerUser;
};

export function Header({
  onLogout,
  theme,
  onTheme,
  user,
}: HeaderProps) {
  const location = useLocation();
  const isAdmin = user.role === "Admin";
  return (
    <header className="app-header">
      <div className="header-inner">
        <Brand />

        <nav className={isAdmin ? "primary-nav has-admin" : "primary-nav"} aria-label="Primary navigation">
          <Link className={location.pathname === "/" ? "nav-active" : "nav-link"} to="/">
            <Icon name="grid" size={17} />
            Dashboard
          </Link>
          <Link className={location.pathname === "/analytics" ? "nav-active" : "nav-link"} to="/analytics">Analytics</Link>
          <Link className={location.pathname === "/expenses/new" ? "nav-active" : "nav-link"} to="/expenses/new">Add Expense</Link>
          {isAdmin && <Link className={`nav-admin-link ${location.pathname === "/admin" ? "nav-active" : "nav-link"}`} to="/admin">Admin Portal</Link>}
        </nav>

        <div className="header-actions">
          <Button
            className="theme-toggle"
            onClick={onTheme}
          >
            <Icon
              name={
                theme === "dark"
                  ? "sun"
                  : "moon"
              }
              size={16}
            />

            <span>
              {theme === "dark"
                ? "Light"
                : "Dark"}
            </span>

            <small>
              {theme === "dark"
                ? "Dark mode on"
                : "Light mode on"}
            </small>
          </Button>

          <div className="user-block">
          <span className="avatar">{user.name.split(/\s+/).map((part) => part[0]).slice(0, 2).join("").toUpperCase()}</span>

            <span>
              <strong>{user.name}</strong>
              <small>{user.role} · {user.cost_centre}</small>
            </span>
          </div>

          <Button
            className="icon-button"
            onClick={onLogout}
          >
            <Icon
              name="logout"
              size={19}
            />

            <span className="sr-only">
              Log out
            </span>
          </Button>
        </div>
      </div>
    </header>
  );
}
