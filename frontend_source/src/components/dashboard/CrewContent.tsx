import { useEffect, useState } from "react";
import { Users, Search, Mail, Phone } from "lucide-react";
import { listCrew, CrewSummary } from "@/lib/api";

const DEPT_COLORS: Record<string, string> = {
  Camera: "bg-blue-500/20 text-blue-400",
  Lighting: "bg-yellow-500/20 text-yellow-400",
  Grip: "bg-orange-500/20 text-orange-400",
  Sound: "bg-purple-500/20 text-purple-400",
  "Art Department": "bg-pink-500/20 text-pink-400",
  Production: "bg-primary/20 text-primary",
};

function getDeptColor(dept: string) {
  return DEPT_COLORS[dept] || "bg-muted text-muted-foreground";
}

function getInitials(name: string) {
  return name.split(" ").map(n => n[0]).join("").toUpperCase().slice(0, 2) || "?";
}

export function CrewContent() {
  const [crew, setCrew] = useState<CrewSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  useEffect(() => {
    listCrew()
      .then(setCrew)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const filtered = crew.filter(
    (c) =>
      !search ||
      c.name.toLowerCase().includes(search.toLowerCase()) ||
      c.role.toLowerCase().includes(search.toLowerCase()) ||
      c.department.toLowerCase().includes(search.toLowerCase())
  );

  if (loading) {
    return (
      <div className="p-6 space-y-3">
        {[...Array(8)].map((_, i) => (
          <div key={i} className="h-16 rounded-lg bg-card animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border px-6 py-4">
        <div>
          <h1 className="text-xl font-semibold text-foreground">Crew</h1>
          <p className="text-sm text-muted-foreground">{crew.length} member{crew.length !== 1 ? "s" : ""}</p>
        </div>
        <div className="flex items-center gap-2 rounded-lg border border-border bg-card px-3 py-2">
          <Search className="h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search crew..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="bg-transparent text-sm text-foreground placeholder:text-muted-foreground focus:outline-none w-40"
          />
        </div>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto p-6">
        {error && (
          <div className="mb-4 rounded-lg border border-red-800/50 bg-red-950/40 px-4 py-3 text-sm text-red-400">
            {error}
          </div>
        )}

        {filtered.length === 0 && !error ? (
          <div className="flex h-full flex-col items-center justify-center gap-3 text-center">
            <Users className="h-12 w-12 text-muted-foreground/40" />
            <p className="text-foreground font-medium">{search ? "No results" : "No crew members yet"}</p>
            <p className="text-sm text-muted-foreground">
              {search ? "Try a different search." : "Crew members appear here once you create a project."}
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {filtered.map((member) => (
              <div
                key={member.id}
                className="group flex items-center gap-4 rounded-lg border border-border bg-card px-4 py-3 transition-colors hover:bg-accent cursor-pointer"
              >
                {/* Avatar */}
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
                  {getInitials(member.name)}
                </div>

                {/* Name + role */}
                <div className="flex-1 min-w-0">
                  <p className="truncate text-sm font-medium text-foreground">{member.name || "Unnamed"}</p>
                  <p className="truncate text-xs text-muted-foreground">{member.role || "—"}</p>
                </div>

                {/* Department badge */}
                {member.department && (
                  <span className={"hidden sm:block rounded-full px-2 py-0.5 text-xs font-medium shrink-0 " + getDeptColor(member.department)}>
                    {member.department}
                  </span>
                )}

                {/* Contact */}
                <div className="hidden md:flex items-center gap-3 text-muted-foreground">
                  {member.email && (
                    <a href={"mailto:" + member.email} onClick={(e) => e.stopPropagation()} className="hover:text-foreground transition-colors">
                      <Mail className="h-4 w-4" />
                    </a>
                  )}
                  {member.phone && (
                    <a href={"tel:" + member.phone} onClick={(e) => e.stopPropagation()} className="hover:text-foreground transition-colors">
                      <Phone className="h-4 w-4" />
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
