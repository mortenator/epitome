import { Dashboard } from "@/components/dashboard/Dashboard";
import { LoadingContent } from "@/components/loading/LoadingContent";

export default function Loading() {
  return (
    <Dashboard sidebarCollapsed>
      <LoadingContent />
    </Dashboard>
  );
}
