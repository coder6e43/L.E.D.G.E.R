type BrandProps = {
  light?: boolean;
};

export function Brand({ light = false }: BrandProps) {
  return (
    <div className={`brand ${light ? "brand-light" : ""}`}>
      <span className="brand-mark">
        <span />
        <span />
        <span />
      </span>
      <span className="brand-name">LEDGER</span>
    </div>
  );
}