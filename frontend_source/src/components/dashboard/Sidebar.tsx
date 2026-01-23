import { Home, Users, Folder, Bell, Settings, X } from "lucide-react";
import { EpitomeLogo } from "./EpitomeLogo";
import { NavItem } from "./NavItem";
import { UpgradeCard } from "./UpgradeCard";
import { AiPenIcon } from "./AiPenIcon";
import { useState } from "react";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";

const navItems = [
  { id: "home", icon: Home, label: "Home" },
  { id: "crew-list", icon: AiPenIcon, label: "Crew list builder" },
  { id: "crew", icon: Users, label: "Crew" },
  { id: "projects", icon: Folder, label: "Projects" },
  { id: "notifications", icon: Bell, label: "Notifications", badge: 6 },
  { id: "settings", icon: Settings, label: "Settings" },
];

interface SidebarProps {
  collapsed?: boolean;
  onMobileClose?: () => void;
  animate?: boolean;
}

export function Sidebar({ collapsed = false, onMobileClose, animate = true }: SidebarProps) {
  const [activeItem, setActiveItem] = useState("crew-list");

  const sidebarContent = (
    <>
      {/* Logo with close button on mobile */}
      <div className={cn("py-5 flex items-center justify-between", collapsed ? "px-0" : "px-3")}>
        <EpitomeLogo collapsed={collapsed} />
        {onMobileClose && !collapsed && (
          <button 
            onClick={onMobileClose}
            className="md:hidden p-1 rounded-lg hover:bg-sidebar-accent"
          >
            <X className="h-5 w-5 text-muted-foreground" />
          </button>
        )}
      </div>

      {/* Navigation */}
      <nav className={cn("flex-1 space-y-1", collapsed ? "px-0 w-full" : "px-1")}>
        {navItems.map((item, index) => (
          <motion.div
            key={item.id}
            initial={animate ? { x: -20, opacity: 0 } : false}
            animate={{ x: 0, opacity: 1 }}
            transition={{ 
              duration: 0.3, 
              delay: animate ? 0.1 + index * 0.05 : 0,
              ease: "easeOut"
            }}
          >
            <NavItem
              icon={item.icon}
              label={item.label}
              isActive={activeItem === item.id}
              badge={item.badge}
              onClick={() => {
                setActiveItem(item.id);
                onMobileClose?.();
              }}
              collapsed={collapsed}
            />
          </motion.div>
        ))}
      </nav>

      {/* Upgrade Card */}
      <motion.div 
        className="mt-auto"
        initial={animate ? { y: 20, opacity: 0 } : false}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.4, delay: animate ? 0.5 : 0 }}
      >
        <UpgradeCard
          userName="Allison Lipshutz"
          userRole="Producer"
          collapsed={collapsed}
        />
      </motion.div>
    </>
  );

  if (animate) {
    return (
      <motion.aside 
        className={cn(
          "flex h-full shrink-0 flex-col bg-sidebar p-4 transition-all duration-300",
          collapsed ? "w-[72px] items-center" : "w-[280px] md:w-[320px]"
        )}
        initial={{ x: -100, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ 
          duration: 0.4, 
          ease: [0.25, 0.46, 0.45, 0.94]
        }}
      >
        {sidebarContent}
      </motion.aside>
    );
  }

  return (
    <aside className={cn(
      "flex h-full shrink-0 flex-col bg-sidebar p-4 transition-all duration-300",
      collapsed ? "w-[72px] items-center" : "w-[280px] md:w-[320px]"
    )}>
      {sidebarContent}
    </aside>
  );
}
