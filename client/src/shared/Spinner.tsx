export default function Spinner({ label = "LOADING DATA..." }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 w-full h-full min-h-[300px] font-mono">
      <div className="w-8 h-8 border-2 border-[var(--border-dim)] border-t-[var(--profit)] rounded-full animate-spin mb-4" />
      <span
        className="text-[11px] text-[var(--text-muted)] tracking-wider"
        style={{ marginTop: "8px" }}
      >
        {label}
      </span>
    </div>
  );
}
