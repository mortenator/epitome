import { Dashboard } from "@/components/dashboard/Dashboard";
import { CallSheetContent } from "@/components/callsheet/CallSheetContent";

export default function CallSheet() {
  return (
    <Dashboard sidebarCollapsed>
      <CallSheetContent />
    </Dashboard>
  );
}
