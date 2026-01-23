import { useState } from "react";
import { Sidebar } from "./Sidebar";
import { MainContent } from "./MainContent";
import { MobileHeader } from "./MobileHeader";

interface DashboardProps {
  children?: React.ReactNode;
  sidebarCollapsed?: boolean;
}

export function Dashboard({ children, sidebarCollapsed = false }: DashboardProps) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  return (
    <div className="flex h-screen w-full flex-col md:flex-row bg-background">
      {/* Mobile Header */}
      <MobileHeader 
        isMenuOpen={isMobileMenuOpen} 
        onMenuToggle={() => setIsMobileMenuOpen(!isMobileMenuOpen)} 
      />

      {/* Mobile Menu Overlay */}
      {isMobileMenuOpen && (
        <div 
          className="fixed inset-0 z-40 bg-black/50 md:hidden"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar - hidden on mobile unless menu is open */}
      <div className={`
        fixed inset-y-0 left-0 z-50 transform transition-transform duration-300 md:relative md:transform-none
        ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
      `}>
        <Sidebar collapsed={sidebarCollapsed} onMobileClose={() => setIsMobileMenuOpen(false)} />
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden flex flex-col min-h-0">
        {children || <MainContent />}
      </div>
    </div>
  );
}

export default Dashboard;
