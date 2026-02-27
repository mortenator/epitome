import { MapPin, Phone, AlertTriangle, Sparkles } from "lucide-react";
import { deriveCallTimes } from "@/lib/callTimes";
import { WeatherCard } from "./WeatherCard";
import { CallSheetData, LocationData, Department } from "@/lib/api";
import { useState, useEffect } from 'react';
import { EditableField } from '../shared/EditableField';

interface ProjectInfo {
  id: string;
  jobName: string;
  jobNumber: string;
  client: string;
  clientLogoUrl?: string;
  agency?: string;
}

interface ProductionInfoCardsProps {
  project?: ProjectInfo;
  callSheet?: CallSheetData;
  locations?: LocationData[];
  departments?: Department[];
}

/** Generate a Google Maps search URL from an address */
function getGoogleMapsUrl(address?: string): string | undefined {
  if (!address || address.toUpperCase() === "TBD") return undefined;
  return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(address)}`;
}

/** Map API weather conditions to supported WeatherCard conditions */
type WeatherCondition = "Sunny" | "Cloudy" | "Rain" | "Clear";

function mapWeatherCondition(condition?: string): WeatherCondition {
  if (!condition) return "Sunny";
  const lower = condition.toLowerCase();

  // Rain conditions
  if (lower.includes("rain") || lower.includes("shower") || lower.includes("drizzle") ||
      lower.includes("storm") || lower.includes("thunder") || lower.includes("snow") ||
      lower.includes("sleet") || lower.includes("hail")) {
    return "Rain";
  }

  // Cloudy conditions
  if (lower.includes("cloud") || lower.includes("overcast") || lower.includes("fog") ||
      lower.includes("mist") || lower.includes("haze") || lower.includes("gray") ||
      lower.includes("grey")) {
    return "Cloudy";
  }

  // Clear/Sunny conditions
  if (lower.includes("clear") || lower.includes("sunny") || lower.includes("fair")) {
    return "Sunny";
  }

  // Default to Cloudy for unknown conditions (safer than assuming sunny)
  return "Cloudy";
}


/** Small "Calculated" badge shown when a call time was auto-derived */
function CalcBadge() {
  return (
    <span className="inline-flex items-center gap-1 ml-1.5 rounded-full bg-primary/10 px-1.5 py-0.5 text-[10px] font-medium text-primary">
      <Sparkles className="h-2.5 w-2.5" />
      Calculated
    </span>
  );
}

/** Renders value, or an amber "Missing" pill if the value is absent/TBD */
function FieldValue({ value, className = "" }: { value?: string; className?: string }) {
  const isMissing = !value || value.toUpperCase() === "TBD";
  if (isMissing) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/15 px-2 py-0.5 text-xs font-medium text-amber-400">
        <AlertTriangle className="h-3 w-3 flex-shrink-0" />
        Missing
      </span>
    );
  }
  return <span className={className}>{value}</span>;
}

export function ProductionInfoCards({ project: initialProject, callSheet, locations, departments }: ProductionInfoCardsProps) {
  const [project, setProject] = useState(initialProject);

  useEffect(() => {
    setProject(initialProject);
  }, [initialProject]);

  const handleProjectUpdate = (field: keyof ProjectInfo, value: string) => {
    if (!project) return;
    const updatedProject = { ...project, [field]: value };
    setProject(updatedProject);
    // TODO: Add API call to persist this change to the backend
    console.log(`Saving ${field}: ${value}`);
  };

  // Find crew and truck parking locations
  const crewParking = locations?.find((l) => l.name.toLowerCase().includes("crew"));
  const truckParking = locations?.find((l) => l.name.toLowerCase().includes("truck"));
  const primaryLocation = locations?.[0];

  // Find Producer and Production Manager from Production department
  const productionDept = departments?.find((d) => d.name.toLowerCase() === "production");
  const producer = productionDept?.crew.find((c) =>
    c.role?.toLowerCase().includes("producer") && !c.role?.toLowerCase().includes("manager")
  );
  // Match "production manager", "pm", or roles containing "manager" (handles typos like "prouction manager")
  const productionManager = productionDept?.crew.find((c) => {
    const role = c.role?.toLowerCase() || "";
    return role.includes("production manager") ||
           role.includes("prouction manager") ||  // Common typo
           role === "pm" ||
           (role.includes("manager") && !role.includes("stage"));  // "manager" in production dept, excluding stage manager
  });

  // Parse weather temperature strings
  const parseTemp = (tempStr?: string): number | undefined => {
    if (!tempStr || tempStr.toUpperCase() === "TBD") return undefined;
    const match = tempStr.match(/-?\d+/);
    return match ? parseInt(match[0], 10) : undefined;
  };

  const highTemp = parseTemp(callSheet?.weather?.high);
  const lowTemp = parseTemp(callSheet?.weather?.low);

  // Check if sunrise/sunset are valid (not TBD or empty)
  const sunriseValue = callSheet?.weather?.sunrise || "";
  const sunsetValue = callSheet?.weather?.sunset || "";
  const sunriseIsTBD = !sunriseValue || sunriseValue.toUpperCase() === "TBD";
  const sunsetIsTBD = !sunsetValue || sunsetValue.toUpperCase() === "TBD";

  const sunrise = sunriseIsTBD ? "- AM" : sunriseValue;
  const sunset = sunsetIsTBD ? "- PM" : sunsetValue;

  // If sunrise or sunset is TBD, weather is unknown, so don't show temperature
  const hasValidWeather = !sunriseIsTBD && !sunsetIsTBD &&
    highTemp !== undefined &&
    lowTemp !== undefined;

  // Generate hospital maps URL from address
  const hospitalAddress = callSheet?.hospital?.address;
  const hospitalMapsUrl = getGoogleMapsUrl(
    hospitalAddress ? `${callSheet?.hospital?.name}, ${hospitalAddress}` : undefined
  );

  return (
    <div className="mb-4 md:mb-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3 md:gap-4">
      {/* Production */}
      <div className="rounded-lg border-glass-border bg-glass p-4 overflow-hidden">
        <p className="mb-3 text-xs font-medium uppercase tracking-wider text-muted">
          Production
        </p>
        <div className="space-y-3 text-sm">
          <div>
            <div className="font-medium text-foreground truncate">
              <EditableField
                initialValue={project?.jobName || ""}
                onSave={(newValue) => handleProjectUpdate('jobName', newValue)}
                placeholder="Enter Job Name"
              />
            </div>
            <div className="text-muted-foreground truncate">
              Job #
              <EditableField
                initialValue={project?.jobNumber || ""}
                onSave={(newValue) => handleProjectUpdate('jobNumber', newValue)}
                placeholder="Enter Job Number"
                className="inline-block ml-1"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Client / Agency */}
      <div className="rounded-lg border-glass-border bg-glass p-4 overflow-hidden">
        <p className="mb-3 text-xs font-medium uppercase tracking-wider text-muted">
          Client / Agency
        </p>
        <div className="space-y-3 text-sm">
          <div className="flex items-start gap-3">
            {project?.clientLogoUrl && (
              <img
                src={project.clientLogoUrl}
                alt={`${project.client} logo`}
                className="h-10 w-10 rounded object-contain bg-white flex-shrink-0"
                onError={(e) => {
                  e.currentTarget.style.display = 'none';
                }}
              />
            )}
            <div className="min-w-0 flex-1">
              <div className="font-medium text-foreground truncate">
                <EditableField
                  initialValue={project?.client || ""}
                  onSave={(newValue) => handleProjectUpdate('client', newValue)}
                  placeholder="Enter Client"
                />
              </div>
              <div className="text-muted-foreground truncate">
                <EditableField
                  initialValue={project?.agency || ""}
                  onSave={(newValue) => handleProjectUpdate('agency', newValue)}
                  placeholder="Enter Agency"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Production Cells */}
      <div className="rounded-lg border-glass-border bg-glass p-4 overflow-hidden">
        <p className="mb-3 text-xs font-medium uppercase tracking-wider text-muted">
          Production Cells
        </p>
        <div className="space-y-3 text-sm">
          <div>
            <p className="text-muted text-xs">Producer</p>
            <div className="font-medium text-foreground truncate"><FieldValue value={producer?.name} className="font-medium text-foreground" /></div>
            {producer?.phone && (
              <a
                href={`tel:${producer.phone}`}
                className="flex items-center gap-1 text-primary hover:text-epitome-teal-light text-xs mt-0.5"
              >
                <Phone className="h-3 w-3" />
                {producer.phone}
              </a>
            )}
          </div>
          <div>
            <p className="text-muted text-xs">Production Manager</p>
            <div className="font-medium text-foreground truncate"><FieldValue value={productionManager?.name} className="font-medium text-foreground" /></div>
            {productionManager?.phone && (
              <a
                href={`tel:${productionManager.phone}`}
                className="flex items-center gap-1 text-primary hover:text-epitome-teal-light text-xs mt-0.5"
              >
                <Phone className="h-3 w-3" />
                {productionManager.phone}
              </a>
            )}
          </div>
        </div>
      </div>

      {/* Call Times — auto-calculated from whichever anchor the AI provided */}
      {(() => {
        const derived = deriveCallTimes(
          callSheet?.generalCrewCall,
          callSheet?.productionCall,
          callSheet?.breakfastCall
        );
        return (
          <div className="rounded-lg border-glass-border bg-glass p-4 overflow-hidden">
            <p className="mb-3 text-xs font-medium uppercase tracking-wider text-muted">
              Call Times
            </p>
            {derived ? (
              <div className="space-y-2 text-sm">
                {/* Production */}
                <div className="flex items-center justify-between gap-2">
                  <span className="text-muted-foreground shrink-0">Production</span>
                  <span className="flex items-center">
                    <span className="font-medium text-foreground">{derived.productionCall.value}</span>
                    {derived.productionCall.derived && <CalcBadge />}
                  </span>
                </div>
                {/* Breakfast RTS */}
                <div className="flex items-center justify-between gap-2">
                  <span className="text-muted-foreground shrink-0">Breakfast RTS</span>
                  <span className="flex items-center">
                    <span className="font-medium text-foreground">{derived.breakfastCall.value}</span>
                    {derived.breakfastCall.derived && <CalcBadge />}
                  </span>
                </div>
                {/* General Crew */}
                <div className="flex items-center justify-between gap-2">
                  <span className="text-muted-foreground shrink-0">Crew Call</span>
                  <span className="flex items-center">
                    <span className="font-medium text-foreground">{derived.generalCrewCall.value}</span>
                    {derived.generalCrewCall.derived && <CalcBadge />}
                  </span>
                </div>
                {/* Talent */}
                <div className="flex items-center justify-between gap-2">
                  <span className="text-muted-foreground shrink-0">Talent</span>
                  <FieldValue value={callSheet?.talentCall} className="font-medium text-foreground" />
                </div>
              </div>
            ) : (
              <div className="space-y-2 text-sm">
                <div className="flex justify-between"><span className="text-muted-foreground">Production</span><FieldValue value={undefined} /></div>
                <div className="flex justify-between"><span className="text-muted-foreground">Breakfast RTS</span><FieldValue value={undefined} /></div>
                <div className="flex justify-between"><span className="text-muted-foreground">Crew Call</span><FieldValue value={undefined} /></div>
                <div className="flex justify-between"><span className="text-muted-foreground">Talent</span><FieldValue value={undefined} /></div>
              </div>
            )}
          </div>
        );
      })()}

      {/* Weather */}
      <div>
        <WeatherCard
          weatherCondition={mapWeatherCondition(callSheet?.weather?.summary)}
          isDaytime={true}
          temperature={
            hasValidWeather
              ? { high: highTemp!, low: lowTemp! }
              : undefined
          }
          sunrise={sunrise}
          sunset={sunset}
        />
      </div>

      {/* Location */}
      <div className="rounded-lg border-glass-border bg-glass p-4 flex flex-col overflow-hidden">
        <p className="mb-3 text-xs font-medium uppercase tracking-wider text-muted">
          Location
        </p>
        <div className="space-y-2 text-sm flex-1">
          <div className="text-foreground font-medium break-words"><FieldValue value={primaryLocation?.name} className="text-foreground font-medium" /></div>
          <p className="text-muted-foreground break-words">{primaryLocation?.address || "TBD"}</p>
        </div>
        {primaryLocation?.mapLink && (
          <a
            href={primaryLocation.mapLink}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-primary hover:text-epitome-teal-light text-sm mt-3 shrink-0"
          >
            <MapPin className="h-3 w-3" />
            View Map
          </a>
        )}
      </div>

      {/* Crew Parking */}
      <div className="rounded-lg border-glass-border bg-glass p-4 flex flex-col overflow-hidden">
        <p className="mb-3 text-xs font-medium uppercase tracking-wider text-muted">
          Crew Parking
        </p>
        <div className="space-y-2 text-sm flex-1">
          <p className="text-foreground break-words">{crewParking?.address || primaryLocation?.address || "TBD"}</p>
          <p className="text-muted-foreground break-words">
            {crewParking?.city || primaryLocation?.city || ""}{" "}
            {crewParking?.state || primaryLocation?.state || ""}
          </p>
          {(crewParking?.parkingNotes || primaryLocation?.parkingNotes) && (
            <p className="text-xs text-muted-foreground italic break-words">
              {crewParking?.parkingNotes || primaryLocation?.parkingNotes}
            </p>
          )}
        </div>
        {(crewParking?.mapLink || primaryLocation?.mapLink) && (
          <a
            href={crewParking?.mapLink || primaryLocation?.mapLink}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-primary hover:text-epitome-teal-light text-sm mt-3 shrink-0"
          >
            <MapPin className="h-3 w-3" />
            View Map
          </a>
        )}
      </div>

      {/* Hospital */}
      <div className="rounded-lg border-glass-border bg-glass p-4 flex flex-col overflow-hidden">
        <p className="mb-3 text-xs font-medium uppercase tracking-wider text-muted">
          Nearest Hospital
        </p>
        <div className="space-y-2 text-sm flex-1">
          <div className="text-foreground font-medium break-words"><FieldValue value={callSheet?.hospital?.name} className="text-foreground font-medium" /></div>
          <p className="text-muted-foreground break-words">{callSheet?.hospital?.address || ""}</p>
        </div>
        {hospitalMapsUrl && (
          <a
            href={hospitalMapsUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-primary hover:text-epitome-teal-light text-sm mt-3 shrink-0"
          >
            <MapPin className="h-3 w-3" />
            View Map
          </a>
        )}
      </div>
    </div>
  );
}
