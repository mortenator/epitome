import { cn } from "@/lib/utils";
import { LucideIcon } from "lucide-react";
import { ComponentType } from "react";

interface NavItemProps {
  icon: LucideIcon | ComponentType<{ className?: string }>;
  label: string;
  isActive?: boolean;
  badge?: number;
  onClick?: () => void;
  collapsed?: boolean;
}

export function NavItem({ icon: Icon, label, isActive = false, badge, onClick, collapsed = false }: NavItemProps) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "relative flex items-center rounded-md text-sm font-medium transition-colors",
        collapsed 
          ? "w-10 h-10 justify-center" 
          : "w-full gap-3 px-3 py-3", // Increased py
        isActive 
          ? "bg-sidebar-accent text-nav-active" 
          : "text-nav-inactive hover:bg-sidebar-accent/50 hover:text-nav-active"
      )}
      title={collapsed ? label : undefined}
    >
      {/* Active state indicator bar */}
      {isActive && !collapsed && (
        <div className="absolute left-0 h-5 w-1 bg-primary rounded-r-full" />
      )}

      <Icon className="h-5 w-5 shrink-0" />
      
      {!collapsed && (
        <>
          <span className="flex-1 text-left tracking-tight">{label}</span>
          {badge !== undefined && (
            <span className="flex h-6 w-6 items-center justify-center rounded-full bg-badge-bg text-xs font-medium text-sidebar-foreground">
              {badge}
            </span>
          )}
        </>
      )}
    </button>
  );
}
