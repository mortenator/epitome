import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { ChatPanel } from "./ChatPanel";
import { CallSheetPreview } from "./CallSheetPreview";
import { MessageSquare, FileText } from "lucide-react";
import { useWorkbookRegeneration } from "@/hooks/useWorkbookRegeneration";

export function CallSheetContent() {
  const [searchParams] = useSearchParams();
  // Support both project ID (normal) and job ID (fallback when database save fails)
  const projectId = searchParams.get("project") || searchParams.get("job");
  const isJobId = !searchParams.get("project") && !!searchParams.get("job");
  const initialDownloadFilename = searchParams.get("download");

  const [activeTab, setActiveTab] = useState<"chat" | "preview">("preview");

  // Shared workbook regeneration state
  const { isRegenerating, downloadFilename, regenerate } = useWorkbookRegeneration(
    projectId,
    initialDownloadFilename
  );

  return (
    <main className="flex h-full flex-col md:flex-row overflow-hidden">
      {/* Mobile Tab Bar */}
      <div className="flex md:hidden border-b bg-background">
        <button
          onClick={() => setActiveTab("chat")}
          className={`flex-1 flex items-center justify-center gap-2 py-3 text-sm font-medium transition-colors ${
            activeTab === "chat"
              ? "text-primary border-b-2 border-primary"
              : "text-muted-foreground"
          }`}
        >
          <MessageSquare className="h-4 w-4" />
          Chat
        </button>
        <button
          onClick={() => setActiveTab("preview")}
          className={`flex-1 flex items-center justify-center gap-2 py-3 text-sm font-medium transition-colors ${
            activeTab === "preview"
              ? "text-primary border-b-2 border-primary"
              : "text-muted-foreground"
          }`}
        >
          <FileText className="h-4 w-4" />
          Preview
        </button>
      </div>

      {/* Chat Panel - visible on desktop, toggleable on mobile */}
      <div className={`${activeTab === "chat" ? "flex" : "hidden"} md:flex flex-1 md:flex-none`}>
        <ChatPanel onRegenerate={regenerate} />
      </div>

      {/* Preview Panel - visible on desktop, toggleable on mobile */}
      <div className={`${activeTab === "preview" ? "flex" : "hidden"} md:flex flex-1`}>
        <CallSheetPreview
          isRegenerating={isRegenerating}
          downloadFilename={downloadFilename}
          onRegenerate={regenerate}
        />
      </div>
    </main>
  );
}
