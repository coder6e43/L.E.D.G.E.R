import { Icon } from "../common/Icon";
import { Button } from "../common/Button";
import { Brand } from "../common/Brand";
import type { LedgerUser } from "../../services/api";

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
  return (
    <header className="app-header">
      <div className="header-inner">
        <Brand />

        <nav aria-label="Primary navigation">
          <span className="nav-active">
            <Icon name="grid" size={17} />
            Dashboard
          </span>
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
