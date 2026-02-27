import { useState, useEffect } from "react";
import { Check, ChevronRight, FileText, List, Lightbulb, Key, Sparkles, LayoutGrid, MapPin, Cloud, Building2 } from "lucide-react";
import { ProgressEvent } from "@/lib/api";
import { getStageLabel } from "@/hooks/useGeneration";

interface Step {
  id: string;
  label: string;
  icon: React.ReactNode;
}

// Map backend stage IDs to step definitions
const steps: Step[] = [
  { id: "analyzing_file", label: "Reviewing your files", icon: <FileText className="h-4 w-4" /> },
  { id: "understanding_prompt", label: "Understanding your request", icon: <Lightbulb className="h-4 w-4" /> },
  { id: "preparing_extraction", label: "Preparing AI prompt", icon: <Key className="h-4 w-4" /> },
  { id: "sending_to_ai", label: "Sending to AI", icon: <List className="h-4 w-4" /> },
  { id: "ai_processing", label: "AI is analyzing your data", icon: <List className="h-4 w-4" /> },
  { id: "parsing_response", label: "Processing AI response", icon: <List className="h-4 w-4" /> },
  { id: "extraction_complete", label: "Extraction complete", icon: <List className="h-4 w-4" /> },
  { id: "enriching_location", label: "Finding location info", icon: <MapPin className="h-4 w-4" /> },
  { id: "enriching_weather", label: "Getting weather forecast", icon: <Cloud className="h-4 w-4" /> },
  { id: "enriching_logo", label: "Looking up company logos", icon: <Building2 className="h-4 w-4" /> },
  { id: "enrichment_complete", label: "Data enrichment complete", icon: <MapPin className="h-4 w-4" /> },
  { id: "generating", label: "Building your call sheet", icon: <LayoutGrid className="h-4 w-4" /> },
  { id: "saving_file", label: "Saving workbook", icon: <FileText className="h-4 w-4" /> },
  { id: "saving_database", label: "Saving to database", icon: <LayoutGrid className="h-4 w-4" /> },
  { id: "ready", label: "Ready!", icon: <Sparkles className="h-4 w-4" /> },
];

interface LoadingStepListProps {
  progress: ProgressEvent | null;
  error: string | null;
}

export function LoadingStepList({ progress, error }: LoadingStepListProps) {
  const [completedSteps, setCompletedSteps] = useState<string[]>([]);
  const [startTime] = useState(() => Date.now());
  const [elapsedTime, setElapsedTime] = useState(0);

  // Track elapsed time
  useEffect(() => {
    const interval = setInterval(() => {
      setElapsedTime(Math.floor((Date.now() - startTime) / 1000));
    }, 1000);
    return () => clearInterval(interval);
  }, [startTime]);

  // Track completed steps based on progress
  useEffect(() => {
    if (!progress) return;

    const currentStepIndex = steps.findIndex((s) => s.id === progress.stage_id);
    if (currentStepIndex > 0) {
      // Mark all previous steps as complete
      const completed = steps.slice(0, currentStepIndex).map((s) => s.id);
      setCompletedSteps(completed);
    }

    // If we hit 100% on a step, mark it complete too
    if (progress.percent >= 100 && progress.stage_id !== "complete") {
      setCompletedSteps((prev) =>
        prev.includes(progress.stage_id) ? prev : [...prev, progress.stage_id]
      );
    }
  }, [progress]);

  const currentStageId = progress?.stage_id || steps[0].id;

  // If there's an error, show it
  if (error) {
    return (
      <div className="space-y-1">
        <div className="mb-2 flex items-center gap-2 rounded-lg bg-red-950/40 border border-red-800/50 px-3 py-2">
          <div className="h-4 w-4 rounded-full bg-red-500" />
          <span className="text-sm text-red-400">Error</span>
        </div>
        <p className="text-sm text-red-400 px-3">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-1">
      {/* Thinking indicator */}
      <div className="mb-2 flex items-center gap-2 rounded-lg bg-orange-50 px-3 py-2">
        <div className="h-4 w-4 animate-spin rounded-full border-2 border-orange-400 border-t-transparent" />
        <span className="text-sm text-foreground">Thinking</span>
        <span className="text-sm text-muted-foreground">{elapsedTime}s</span>
        <ChevronRight className="ml-auto h-4 w-4 text-muted-foreground" />
      </div>

      {steps.map((step) => {
        const isCompleted = completedSteps.includes(step.id);
        const isActive = currentStageId === step.id && !isCompleted;

        return (
          <div
            key={step.id}
            className={`flex items-center gap-2 rounded-lg px-3 py-2 transition-all ${
              isActive ? "bg-orange-50" : ""
            }`}
          >
            <span className={isCompleted ? "text-muted-foreground" : "text-muted-foreground"}>
              {step.icon}
            </span>
            <span className={`text-sm ${isCompleted || isActive ? "text-foreground" : "text-muted-foreground"}`}>
              {isActive && progress?.message ? progress.message : step.label}
            </span>
            {isCompleted && <Check className="ml-auto h-4 w-4 text-green-500" />}
            {isActive && progress && (
              <>
                <span className="ml-auto text-sm text-muted-foreground">{progress.percent}%</span>
                <ChevronRight className="h-4 w-4 text-muted-foreground" />
              </>
            )}
          </div>
        );
      })}
    </div>
  );
}
