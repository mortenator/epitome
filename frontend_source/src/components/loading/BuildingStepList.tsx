import { FileText, LayoutGrid, FileEdit, Pencil, Sparkles, AlertCircle } from "lucide-react";
import { ProgressEvent } from "@/lib/api";
import { getStageLabel } from "@/hooks/useGeneration";

interface BuildingStep {
  id: string;
  label: string;
  icon: React.ReactNode;
}

// Map backend stages to building visual steps
const buildingSteps: BuildingStep[] = [
  { id: "analyzing_file", label: "Analyzing your input", icon: <FileText className="h-5 w-5" /> },
  { id: "extracting_data", label: "Extracting project details", icon: <LayoutGrid className="h-5 w-5" /> },
  { id: "enriching", label: "Enriching with real data...", icon: <FileEdit className="h-5 w-5" /> },
  { id: "generating", label: "Building your call sheet", icon: <Pencil className="h-5 w-5" /> },
  { id: "complete", label: "Finishing the final polish", icon: <Sparkles className="h-5 w-5" /> },
];

// Map backend stage IDs to building step indices
function getStepIndexForStage(stageId: string): number {
  if (stageId === "analyzing_file" || stageId === "understanding_prompt") return 0;
  // All extraction-related stages map to step 1
  if (stageId === "extracting_data" ||
      stageId === "preparing_extraction" ||
      stageId === "sending_to_ai" ||
      stageId === "ai_processing" ||
      stageId === "parsing_response" ||
      stageId === "extraction_complete") return 1;
  // All enrichment stages map to step 2
  if (stageId.startsWith("enriching") || stageId === "enrichment_complete") return 2;
  // Generating and saving stages map to step 3
  if (stageId === "generating" || stageId === "saving_file" || stageId === "saving_database") return 3;
  // Final stages
  if (stageId === "ready" || stageId === "complete" || stageId === "download_ready") return 4;
  return 0;
}

interface BuildingStepListProps {
  progress: ProgressEvent | null;
  error: string | null;
}

export function BuildingStepList({ progress, error }: BuildingStepListProps) {
  const activeStep = progress ? getStepIndexForStage(progress.stage_id) : 0;

  if (error) {
    return (
      <div className="flex flex-col items-center gap-4">
        <AlertCircle className="h-12 w-12 text-red-500" />
        <p className="text-sm text-red-600 text-center max-w-xs">{error}</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      {buildingSteps.map((step, index) => {
        const isActive = index === activeStep;
        const isPast = index < activeStep;

        return (
          <div
            key={step.id}
            className={`flex items-center gap-3 transition-all duration-300 ${
              isActive ? "text-foreground" : isPast ? "text-muted-foreground" : "text-muted-foreground/50"
            }`}
          >
            <span className={isActive ? "text-blue-500" : isPast ? "text-green-500" : ""}>
              {step.icon}
            </span>
            <span className={`text-sm ${isActive ? "font-medium" : ""}`}>
              {isActive && progress ? getStageLabel(progress.stage_id) : step.label}
            </span>
          </div>
        );
      })}

      {/* Progress bar */}
      {progress && (
        <div className="mt-4 w-48">
          <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-500 rounded-full transition-all duration-300"
              style={{ width: `${progress.percent}%` }}
            />
          </div>
          <p className="text-xs text-muted-foreground mt-1 text-center">
            {progress.percent}%
          </p>
        </div>
      )}
    </div>
  );
}
