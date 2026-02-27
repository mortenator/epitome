import { useState, useRef, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { Loader2 } from "lucide-react";
import { sendChatMessage, ProjectData, ChatMessage } from "@/lib/api";
import { useProject } from "@/hooks/useProject";
import { toast } from "sonner";

interface Message {
  id: string;
  type: "user" | "ai";
  content: string;
  timestamp: Date;
}

/**
 * Generate a formatted summary of the production shoot.
 * Includes project details, dates, locations, and crew information.
 */
function generateProjectSummary(projectData: ProjectData): string {
  const { project, callSheets, locations } = projectData;
  
  const summary: string[] = [];
  summary.push("Great! Here's your call sheet for this production - please find the details below:\n");
  
  // Project Information
  summary.push("Project Information:");
  summary.push(`• Project Name: ${project?.jobName || "TBD"}`);
  if (project?.jobNumber) {
    summary.push(`• Job Number: ${project.jobNumber}`);
  }
  summary.push(`• Client: ${project?.client || "TBD"}`);
  if (project?.agency) {
    summary.push(`• Agency: ${project.agency}`);
  }
  summary.push("");
  
  // Shoot Schedule
  if (callSheets && callSheets.length > 0) {
    summary.push("Shoot Schedule:");
    const sortedCallSheets = [...callSheets].sort((a, b) => a.dayNumber - b.dayNumber);
    const firstDay = sortedCallSheets[0];
    const lastDay = sortedCallSheets[sortedCallSheets.length - 1];
    
    if (sortedCallSheets.length === 1) {
      const shootDate = firstDay.shootDate ? new Date(firstDay.shootDate).toLocaleDateString('en-US', { 
        weekday: 'long', 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
      }) : "TBD";
      summary.push(`• Shoot Date: ${shootDate}`);
      summary.push(`• Crew Call: ${firstDay.generalCrewCall || "TBD"}`);
    } else {
      const startDate = firstDay.shootDate ? new Date(firstDay.shootDate).toLocaleDateString('en-US', { 
        month: 'long', 
        day: 'numeric',
        year: 'numeric'
      }) : "TBD";
      const endDate = lastDay.shootDate ? new Date(lastDay.shootDate).toLocaleDateString('en-US', { 
        month: 'long', 
        day: 'numeric',
        year: 'numeric'
      }) : "TBD";
      summary.push(`• Shoot Dates: ${startDate} - ${endDate} (${sortedCallSheets.length} days)`);
      summary.push(`• Day 1 Crew Call: ${firstDay.generalCrewCall || "TBD"}`);
    }
    summary.push("");
  }
  
  // Locations
  if (locations && locations.length > 0) {
    summary.push("Locations:");
    const uniqueLocations = locations.filter((loc, index, self) => 
      index === self.findIndex(l => l.id === loc.id)
    );
    uniqueLocations.forEach((location) => {
      const locationParts = [location.name || "Location"];
      if (location.address) locationParts.push(location.address);
      if (location.city || location.state) {
        locationParts.push([location.city, location.state].filter(Boolean).join(", "));
      }
      summary.push(`• ${locationParts.join(" - ")}`);
    });
    summary.push("");
  }
  
  // Crew Information
  const departments = projectData.departments || [];
  const totalCrew = departments.reduce((sum, dept) => sum + dept.count, 0);
  if (totalCrew > 0) {
    summary.push("Crew:");
    summary.push(`• Total Crew Members: ${totalCrew}`);
    if (departments.length > 0) {
      const departmentList = departments
        .filter(dept => dept.count > 0)
        .map(dept => `${dept.name} (${dept.count})`)
        .join(", ");
      if (departmentList) {
        summary.push(`• Departments: ${departmentList}`);
      }
    }
    summary.push("");
  }
  
  // Nearest Hospital
  const firstCallSheet = callSheets?.[0];
  if (firstCallSheet?.hospital?.name) {
    summary.push("Nearest Hospital:");
    summary.push(`• ${firstCallSheet.hospital.name}`);
    if (firstCallSheet.hospital.address) {
      summary.push(`• ${firstCallSheet.hospital.address}`);
    }
    summary.push("");
  }
  
  summary.push("I'm here to help you manage this production. Ask me questions about the project, or tell me to make changes like \"Change the crew call time to 8am\".");
  
  return summary.join("\n");
}

interface ChatPanelProps {
  /** Callback to trigger workbook regeneration after edits */
  onRegenerate?: () => void;
}

export function ChatPanel({ onRegenerate }: ChatPanelProps) {
  const [searchParams] = useSearchParams();
  // Support both project ID (normal) and job ID (fallback when database save fails)
  const projectId = searchParams.get("project") || searchParams.get("job");
  const isJobId = !searchParams.get("project") && !!searchParams.get("job");
  const { data: projectData, refetch } = useProject(projectId, isJobId);
  
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Initialize with welcome message if project data is available
  useEffect(() => {
    if (projectData && messages.length === 0) {
      const summary = generateProjectSummary(projectData);
      setMessages([
        {
          id: "welcome",
          type: "ai",
          content: summary,
          timestamp: new Date(),
        },
      ]);
    }
  }, [projectData, messages.length]);

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    if (!inputValue.trim() || !projectId || isLoading) {
      console.log("HandleSend blocked:", { inputValue: inputValue.trim(), projectId, isLoading });
      return;
    }

    console.log("Sending message:", inputValue.trim(), "to project:", projectId);

    const userMessage: Message = {
      id: Date.now().toString(),
      type: "user",
      content: inputValue.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const messageToSend = inputValue.trim();
    setInputValue("");
    setIsLoading(true);

    try {
      // Build conversation history for multi-turn context
      // Exclude welcome message and only include previous exchanges
      const history: ChatMessage[] = messages
        .filter(m => m.id !== "welcome")
        .map(m => ({
          role: m.type === "user" ? "user" : "assistant",
          content: m.content
        }));

      console.log("Calling sendChatMessage with:", { projectId, message: messageToSend, historyLength: history.length });
      const response = await sendChatMessage(projectId, messageToSend, history);
      console.log("Received response:", response);

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: "ai",
        content: response.response,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, aiMessage]);

      // If it was an edit command, refresh project data and regenerate workbook
      if (response.type === "edit" && response.success) {
        // Wait for data refresh before showing success toast
        // This ensures the UI updates before the user sees confirmation
        await refetch?.();
        toast.success("Changes applied successfully");
        onRegenerate?.(); // Trigger workbook regeneration
      }
    } catch (error) {
      console.error("Error sending chat message:", error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: "ai",
        content: `Sorry, I encountered an error: ${error instanceof Error ? error.message : "Unknown error"}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
      toast.error(`Failed to send message: ${error instanceof Error ? error.message : "Unknown error"}`);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };


  const projectName = projectData?.project?.jobName || "EPITOME SAMPLE";

  return (
    <div className="flex w-full md:w-[400px] flex-col border-r border-border bg-background h-full overflow-hidden">
      {/* Project Header */}
      <div className="flex items-center gap-2 border-b border-border px-4 min-h-[52px] shrink-0">
        <div className="h-4 w-4 rounded bg-orange-400" />
        <span className="text-sm font-medium text-foreground">{projectName.toUpperCase()}</span>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto p-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`mb-4 flex gap-3 ${
              message.type === "user" ? "flex-row" : "flex-row"
            }`}
          >
            {message.type === "user" ? (
              <>
                <div className="h-8 w-8 shrink-0 rounded-full bg-muted" />
                <div className="flex-1">
                  <p className="text-sm text-foreground">{message.content}</p>
                </div>
              </>
            ) : (
              <>
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-blue-400 to-blue-600">
                  <span className="text-xs font-bold text-white">E</span>
                </div>
                <div className="flex-1">
                  <p className="mb-1 font-medium text-foreground">Epitome</p>
                  <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                    {message.content}
                  </p>
                </div>
              </>
            )}
          </div>
        ))}
        
        {isLoading && (
          <div className="mb-4 flex gap-3">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-blue-400 to-blue-600">
              <span className="text-xs font-bold text-white">E</span>
            </div>
            <div className="flex-1">
              <p className="mb-1 font-medium text-foreground">Epitome</p>
              <div className="flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                <p className="text-sm text-muted-foreground">Thinking...</p>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Bottom Input */}
      <div className="border-t border-border p-4 shrink-0">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center gap-3"
        >
          <div className="h-10 w-10 shrink-0 rounded-full bg-muted" />
          <div className="flex flex-1 items-center gap-2">
            <input
              ref={inputRef}
              type="text"
              placeholder="Ask Epitome"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              disabled={isLoading || !projectId}
              className="flex-1 bg-transparent text-sm text-foreground placeholder:text-muted-foreground focus:outline-none disabled:opacity-50"
            />
          </div>
          <button
            type="submit"
            disabled={isLoading || !inputValue.trim() || !projectId}
            className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-500 text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-blue-600 transition-colors"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <svg
                className="h-4 w-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5l7 7-7 7"
                />
              </svg>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
