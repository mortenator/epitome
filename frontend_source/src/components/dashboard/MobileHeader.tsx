import { Menu, X } from "lucide-react";
import { EpitomeLogo } from "./EpitomeLogo";

interface MobileHeaderProps {
  isMenuOpen: boolean;
  onMenuToggle: () => void;
}

export function MobileHeader({ isMenuOpen, onMenuToggle }: MobileHeaderProps) {
  return (
    <header className="flex md:hidden items-center justify-between px-4 py-3 bg-sidebar border-b border-border">
      <EpitomeLogo collapsed={false} />
      <button
        onClick={onMenuToggle}
        className="p-2 rounded-lg hover:bg-sidebar-accent transition-colors"
        aria-label={isMenuOpen ? "Close menu" : "Open menu"}
      >
        {isMenuOpen ? (
          <X className="h-6 w-6 text-foreground" />
        ) : (
          <Menu className="h-6 w-6 text-foreground" />
        )}
      </button>
    </header>
  );
}
