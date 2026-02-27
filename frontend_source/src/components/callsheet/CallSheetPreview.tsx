import { ChevronDown, Loader2 } from "lucide-react";
import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { ProductionInfoCards } from "./ProductionInfoCards";
import { CrewDepartment } from "./CrewDepartment";
import { TopBar } from "../shared/TopBar";
import { AvailableCrewMember } from "./AddCrewDropdown";
import { toast } from "sonner";
import { useProject, useUpdateCrewMember } from "@/hooks/useProject";
import { downloadWorkbook, Department, CrewMember } from "@/lib/api";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

interface CallSheetPreviewProps {
  /** Whether workbook is being regenerated (from parent) */
  isRegenerating?: boolean;
  /** Current download filename (from parent) */
  downloadFilename?: string | null;
  /** Callback to trigger regeneration (from parent) */
  onRegenerate?: () => void;
}

export function CallSheetPreview({
  isRegenerating = false,
  downloadFilename: parentDownloadFilename,
  onRegenerate,
}: CallSheetPreviewProps) {
  const [searchParams] = useSearchParams();
  const projectId = searchParams.get("project");
  const jobId = searchParams.get("job");  // Fallback when project_id is null
  const urlDownloadFilename = searchParams.get("download");

  // Use parent's filename if provided, otherwise fall back to URL param
  const downloadFilename = parentDownloadFilename ?? urlDownloadFilename;

  // Fetch project data (use project_id if available, otherwise use job_id fallback)
  const { data: projectData, isLoading, error, refetch } = useProject(projectId || jobId, !!jobId);
  const updateCrewMutation = useUpdateCrewMember();

  // Local state for departments (initialized from API data)
  const [departments, setDepartments] = useState<Department[]>([]);
  const [expandedDepts, setExpandedDepts] = useState<string[]>([]);
  const [selectedDay, setSelectedDay] = useState(0);

  // Initialize departments from API data
  useEffect(() => {
    if (projectData?.departments) {
      setDepartments(projectData.departments);
      // Expand first department by default
      if (projectData.departments.length > 0 && expandedDepts.length === 0) {
        setExpandedDepts([projectData.departments[0].name]);
      }
    }
  }, [projectData]);

  const toggleDept = (name: string) => {
    setExpandedDepts((prev) =>
      prev.includes(name) ? prev.filter((d) => d !== name) : [...prev, name]
    );
  };

  const handleAddPerson = (deptName: string, role: string, member: AvailableCrewMember) => {
    setDepartments((prevDepts) =>
      prevDepts.map((dept) => {
        if (dept.name !== deptName) return dept;

        let assigned = false;
        const updatedCrew = dept.crew.map((crewMember) => {
          if (!assigned && crewMember.role === role && !crewMember.name) {
            assigned = true;
            return {
              ...crewMember,
              name: member.name,
              phone: member.phone,
              email: member.email,
              callTime: "7:00 AM",
              location: "Set",
            };
          }
          return crewMember;
        });

        return { ...dept, crew: updatedCrew };
      })
    );

    toast.success(`${member.name} added as ${role}`);
  };

  const handleUpdateCrewMember = (
    deptName: string,
    crewIndex: number,
    field: "callTime" | "location",
    value: string
  ) => {
    // Optimistically update local state
    setDepartments((prevDepts) =>
      prevDepts.map((dept) => {
        if (dept.name !== deptName) return dept;

        const updatedCrew = dept.crew.map((crewMember, idx) => {
          if (idx === crewIndex) {
            return { ...crewMember, [field]: value };
          }
          return crewMember;
        });

        return { ...dept, crew: updatedCrew };
      })
    );

    // Find the crew member to get their ID
    const dept = departments.find((d) => d.name === deptName);
    const crewMember = dept?.crew[crewIndex];

    if (crewMember?.id) {
      // Persist to database
      updateCrewMutation.mutate(
        {
          crewId: crewMember.id,
          updates: { [field]: value },
        },
        {
          onSuccess: () => {
            // Regenerate Excel workbook to sync changes
            onRegenerate?.();
          },
          onError: () => {
            toast.error("Failed to save changes");
          },
        }
      );
    }
  };

  const handleDownload = () => {
    if (downloadFilename) {
      downloadWorkbook(downloadFilename);
    } else {
      toast.error("No download available");
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="flex flex-1 flex-col min-w-0 overflow-hidden">
        <TopBar />
        <div className="flex flex-1 items-center justify-center bg-background">
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
            <p className="text-sm text-muted-foreground">Loading call sheet...</p>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex flex-1 flex-col min-w-0 overflow-hidden">
        <TopBar />
        <div className="flex flex-1 items-center justify-center bg-background">
          <div className="flex flex-col items-center gap-3 max-w-md text-center">
            <p className="text-lg font-medium text-red-600">Failed to load call sheet</p>
            <p className="text-sm text-muted-foreground">
              {error instanceof Error ? error.message : "An unknown error occurred"}
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Get current call sheet data
  const currentCallSheet = projectData?.callSheets?.[selectedDay];
  const dayTitle = currentCallSheet
    ? `Day ${currentCallSheet.dayNumber}: ${projectData?.project?.jobName || "Production"}`
    : "Call Sheet";
  const dateStr = currentCallSheet?.shootDate
    ? new Date(currentCallSheet.shootDate).toLocaleDateString("en-US", {
        month: "long",
        day: "numeric",
        year: "numeric",
      })
    : "";

  return (
    <div className="flex flex-1 flex-col min-w-0 overflow-hidden">
      <TopBar
        onDownloadClick={handleDownload}
        isRegenerating={isRegenerating}
        downloadEnabled={!!downloadFilename}
      />

      {/* Call Sheet Content */}
      <div className="flex-1 overflow-x-auto overflow-y-auto bg-background p-4 md:p-6">
        <div className="mx-auto max-w-5xl min-w-0">
          {/* Header */}
          <div className="mb-4 md:mb-6 flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
            <div>
              <h1 className="text-xl md:text-2xl font-semibold text-foreground">{dayTitle}</h1>
              <p className="text-sm text-muted-foreground">{dateStr}</p>
            </div>
            {projectData?.callSheets && projectData.callSheets.length > 1 && (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <button className="flex items-center justify-center gap-1 rounded-lg border border-glass-border bg-glass px-3 py-1.5 text-sm text-foreground hover:bg-accent w-full sm:w-auto">
                    Switch Day
                    <ChevronDown className="h-4 w-4" />
                  </button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  {projectData.callSheets.map((cs, index) => (
                    <DropdownMenuItem
                      key={cs.id}
                      onClick={() => setSelectedDay(index)}
                      className={selectedDay === index ? "bg-accent" : ""}
                    >
                      <span className="font-medium">Day {cs.dayNumber}</span>
                      <span className="ml-2 text-muted-foreground">
                        {new Date(cs.shootDate).toLocaleDateString("en-US", {
                          month: "short",
                          day: "numeric",
                        })}
                      </span>
                    </DropdownMenuItem>
                  ))}
                </DropdownMenuContent>
              </DropdownMenu>
            )}
          </div>

          {/* Production Info Cards */}
          <ProductionInfoCards
            project={projectData?.project}
            callSheet={currentCallSheet}
            locations={projectData?.locations}
            departments={departments}
          />

          {/* Departments */}
          <div className="space-y-2">
            {departments.map((dept) => (
              <CrewDepartment
                key={dept.name}
                name={dept.name}
                count={dept.count}
                crew={dept.crew}
                expanded={expandedDepts.includes(dept.name)}
                onToggle={() => toggleDept(dept.name)}
                onAddPerson={(role, member) => handleAddPerson(dept.name, role, member)}
                onUpdateCrewMember={(crewIndex, field, value) =>
                  handleUpdateCrewMember(dept.name, crewIndex, field, value)
                }
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
