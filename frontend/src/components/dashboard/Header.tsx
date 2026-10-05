import { Icon } from "../common/Icon";
import { Button } from "../common/Button";
import { Brand } from "../common/Brand";

type HeaderProps = {
  onLogout: () => void;
  theme: "light" | "dark";
  onTheme: () => void;
};

export function Header({
  onLogout,
  theme,
  onTheme,
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
          <span className="mock-badge">
            Mock data
          </span>

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
            <span className="avatar">
              AK
            </span>

            <span>
              <strong>Alex Kumar</strong>
              <small>
                Personal workspace
              </small>
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