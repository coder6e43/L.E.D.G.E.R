import { useState } from "react";
import { useNavigate } from "react-router";
import { Icon } from "../common/Icon";
import { Button } from "../common/Button";
import { Brand } from "../common/Brand";
import { useTheme } from "../../App";

export function LandingHeader() {
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <header className="landing-header">
      <div className="landing-nav">
        <button
          className="brand-button"
          onClick={() => navigate("/")}
          aria-label="Ledger home"
        >
          <Brand />
        </button>

        <nav
          className={menuOpen ? "open" : ""}
          aria-label="Public navigation"
        >
          <a
            href="#home"
            onClick={() => setMenuOpen(false)}
          >
            Home
          </a>

          <a
            href="#about"
            onClick={() => setMenuOpen(false)}
          >
            About
          </a>

          <a
            href="#how-it-works"
            onClick={() => setMenuOpen(false)}
          >
            How It Works
          </a>

          <a
            href="#security"
            onClick={() => setMenuOpen(false)}
          >
            Security
          </a>

          <a
            href="#features"
            onClick={() => setMenuOpen(false)}
          >
            Features
          </a>
        </nav>

        <div className="landing-actions">
          <Button
            className="landing-theme"
            onClick={toggleTheme}
          >
            <Icon
              name={
                theme === "dark"
                  ? "sun"
                  : "moon"
              }
              size={17}
            />

            <span className="sr-only">
              Switch to{" "}
              {theme === "dark"
                ? "light"
                : "dark"}{" "}
              mode
            </span>
          </Button>

          <Button
            className="login-link"
            onClick={() => navigate("/login")}
          >
            Log In
          </Button>

          <Button
            className="primary"
            onClick={() => navigate("/signup")}
          >
            Get Started
            <Icon name="arrow" size={16} />
          </Button>

          <Button
            className="menu-toggle"
            onClick={() => setMenuOpen(!menuOpen)}
          >
            <span />
            <span />
            <span />

            <span className="sr-only">
              Toggle menu
            </span>
          </Button>
        </div>
      </div>
    </header>
  );
}