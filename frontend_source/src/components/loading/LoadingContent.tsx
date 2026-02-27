import { useState, useEffect, useRef } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { LoadingStepList } from "./LoadingStepList";
import { BuildingStepList } from "./BuildingStepList";
import { TopBar } from "../shared/TopBar";
import { MessageSquare, FileText } from "lucide-react";
import { subscribeToProgress, ProgressEvent } from "@/lib/api";
import { getStageLabel } from "@/hooks/useGeneration";

export function LoadingContent() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const jobId = searchParams.get("job");
  const prompt = searchParams.get("prompt") || "Create call sheets";

  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"chat" | "preview">("chat");
  const [progress, setProgress] = useState<ProgressEvent | null>(null);
  const [error, setError] = useState<string | null>(null);
  const unsubscribeRef = useRef<(() => void) | null>(null);

  // Subscribe to SSE progress updates
  useEffect(() => {
    if (!jobId) {
      setError("No job ID provided");
      return;
    }

    const unsubscribe = subscribeToProgress(
      jobId,
      // onProgress
      (event) => {
        setProgress(event);
      },
      // onComplete
      (filename, projectId, jobId) => {
        setIsLoading(false);
        // Navigate to call sheet with project ID (or job_id as fallback) and download filename
        const params = new URLSearchParams();
        if (projectId) {
          params.set("project", projectId);
        } else if (jobId) {
          params.set("job", jobId);  // Use job_id as fallback
        }
        if (filename) params.set("download", filename);
        navigate(`/callsheet?${params.toString()}`);
      },
      // onError
      (errorMsg) => {
        setError(errorMsg);
        setIsLoading(false);
      }
    );

    unsubscribeRef.current = unsubscribe;

    return () => {
      if (unsubscribeRef.current) {
        unsubscribeRef.current();
      }
    };
  }, [jobId, navigate]);

  return (
    <main className="flex h-full flex-col md:flex-row overflow-hidden">
      {/* Mobile Tab Bar */}
      <div className="flex md:hidden border-b border-border bg-background">
        <button
          onClick={() => setActiveTab("chat")}
          className={`flex-1 flex items-center justify-center gap-2 py-3 text-sm font-medium transition-colors ${
            activeTab === "chat" 
              ? "text-blue-500 border-b-2 border-blue-500" 
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
              ? "text-blue-500 border-b-2 border-blue-500" 
              : "text-muted-foreground"
          }`}
        >
          <FileText className="h-4 w-4" />
          Preview
        </button>
      </div>

      {/* Left Panel - Chat/Steps */}
      <div className={`${activeTab === "chat" ? "flex" : "hidden"} md:flex w-full md:w-[400px] flex-col border-r border-border bg-sidebar h-full overflow-hidden`}>
        {/* Project Header */}
        <div className="flex items-center gap-2 border-b border-border px-4 min-h-[52px]">
          <div className="h-4 w-4 rounded bg-orange-400" />
          <span className="text-sm font-medium text-foreground">EPITOME SAMPLE</span>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto p-4">
          <h2 className="mb-4 text-lg font-semibold text-foreground">Call Sheet Builder</h2>
          
          {/* User Message */}
          <div className="mb-4 flex gap-3">
            <div className="h-8 w-8 shrink-0 rounded-full bg-muted" />
            <p className="text-sm text-foreground">
              {prompt}
            </p>
          </div>

          {/* AI Response */}
          <div className="mb-4 flex gap-3">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-blue-400 to-blue-600">
              <span className="text-xs font-bold text-white">E</span>
            </div>
            <div className="flex-1">
              <p className="mb-1 font-medium text-foreground">Epitome</p>
              <p className="mb-3 text-sm text-muted-foreground">
                Great, I'll review your crew list and craft a call sheet tailored to that shoot
              </p>
              <LoadingStepList progress={progress} error={error} />
            </div>
          </div>
        </div>

        {/* Bottom Input */}
        <div className={`border-t border-border p-4 ${isLoading ? 'opacity-50 pointer-events-none' : ''}`}>
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 shrink-0 rounded-full bg-muted" />
            <div className="flex flex-1 items-center gap-2">
              <span className="text-muted-foreground">+</span>
              <input
                type="text"
                placeholder="Ask Epitome"
                disabled={isLoading}
                className="flex-1 bg-transparent text-sm text-foreground placeholder:text-muted-foreground focus:outline-none disabled:cursor-not-allowed"
              />
            </div>
            <button 
              disabled={isLoading}
              className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-500 text-white disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Center Panel - Preview Area */}
      <div className={`${activeTab === "preview" ? "flex" : "hidden"} md:flex flex-1 flex-col`}>
        <TopBar />

        {/* Preview Content - Building Steps */}
        <div className="flex flex-1 items-center justify-center bg-background">
          <BuildingStepList progress={progress} error={error} />
        </div>
      </div>
    </main>
  );
}
