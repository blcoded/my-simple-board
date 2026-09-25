import { Moon, Sun } from "lucide-react";
import { useTheme } from "@/hooks/use-theme";
import { Button } from "@/components/ui/button";

export function ThemeToggle({ className }: { className?: string }) {
  const { resolvedTheme, toggleTheme } = useTheme();

  return (
    <Button
      variant="ghost"
      size="sm"
      type="button"
      onClick={toggleTheme}
      className={`h-8 px-2.5 rounded-full border border-border bg-card/60 text-muted-foreground hover:text-foreground hover:bg-accent transition-colors flex items-center gap-1.5 shadow-sm ${className || ""}`}
      title={resolvedTheme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
      aria-label={resolvedTheme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
      data-testid="theme-toggle"
    >
      {resolvedTheme === "dark" ? (
        <Sun className="size-4 text-amber-400 transition-transform duration-200" />
      ) : (
        <Moon className="size-4 text-slate-700 transition-transform duration-200" />
      )}
      <span className="text-xs font-semibold capitalize tracking-wide">
        {resolvedTheme === "dark" ? "Dark" : "Light"}
      </span>
    </Button>
  );
}
