import { useEffect, useState } from "react";
import { Folder, Plus, ChevronRight } from "lucide-react";
import { listProjects, ProjectSummary } from "@/lib/api";

const STATUS_COLORS: Record<string, string> = {
  ACTIVE: "bg-primary/20 text-primary",
  BID: "bg-yellow-500/20 text-yellow-400",
  AWARDED: "bg-blue-500/20 text-blue-400",
  WRAPPED: "bg-muted text-muted-foreground",
  CLOSED: "bg-muted text-muted-foreground",
};

function formatDate(iso: string | null) {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

export function ProjectsContent() {
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listProjects()
      .then(setProjects)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="p-6 space-y-3">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="h-16 rounded-lg bg-card animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-border px-6 py-4">
        <div>
          <h1 className="text-xl font-semibold text-foreground">Projects</h1>
          <p className="text-sm text-muted-foreground">{projects.length} project{projects.length !== 1 ? "s" : ""}</p>
        </div>
        <button className="flex items-center gap-2 rounded-full bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90 transition-opacity">
          <Plus className="h-4 w-4" />
          New project
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        {error && (
          <div className="mb-4 rounded-lg border border-red-800/50 bg-red-950/40 px-4 py-3 text-sm text-red-400">
            {error}
          </div>
        )}

        {projects.length === 0 && !error ? (
          <div className="flex h-full flex-col items-center justify-center gap-3 text-center">
            <Folder className="h-12 w-12 text-muted-foreground/40" />
            <p className="text-foreground font-medium">No projects yet</p>
            <p className="text-sm text-muted-foreground">Upload a crew list to create your first project.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {projects.map((project) => (
              <div
                key={project.id}
                className="group flex items-center justify-between rounded-lg border border-border bg-card px-4 py-3 transition-colors hover:bg-accent cursor-pointer"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded bg-primary/10">
                    <Folder className="h-4 w-4 text-primary" />
                  </div>
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium text-foreground">{project.jobName}</p>
                    <p className="truncate text-xs text-muted-foreground">{project.client || "No client"}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3 shrink-0 ml-4">
                  <span className={"rounded-full px-2 py-0.5 text-xs font-medium " + (STATUS_COLORS[project.status] || STATUS_COLORS.ACTIVE)}>
                    {project.status}
                  </span>
                  <span className="hidden sm:block text-xs text-muted-foreground">{formatDate(project.createdAt)}</span>
                  <ChevronRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
