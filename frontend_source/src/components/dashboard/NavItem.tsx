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
        "flex items-center rounded-md text-sm font-medium transition-colors",
        collapsed 
          ? "w-10 h-10 justify-center mx-auto" 
          : "w-full gap-3 px-3 py-2.5",
        isActive 
          ? "bg-white text-nav-active shadow-sm" 
          : "text-nav-inactive hover:bg-white/50 hover:text-nav-active"
      )}
      title={collapsed ? label : undefined}
    >
      <Icon className="h-5 w-5 shrink-0" />
      {!collapsed && (
        <>
          <span className="flex-1 text-left tracking-tight">{label}</span>
          {badge !== undefined && (
            <span className="flex h-6 w-6 items-center justify-center rounded-full bg-badge-bg text-xs font-medium text-white">
              {badge}
            </span>
          )}
        </>
      )}
    </button>
  );
}
