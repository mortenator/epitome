/**
 * EpitomeLogo — Updated to match the pitch deck wordmark.
 * Clean lowercase sans-serif "epitome" with a teal accent dot, centered on dark backgrounds.
 */
interface EpitomeLogoProps {
  collapsed?: boolean;
  monochrome?: boolean;
}

export function EpitomeLogo({ collapsed = false }: EpitomeLogoProps) {
  if (collapsed) {
    return (
      <div className="h-[35px] w-[35px] flex items-center justify-center">
        {/* Collapsed: just the "e" lettermark in teal */}
        <span
          className="text-xl font-semibold tracking-tighter text-primary"
          style={{ fontFamily: "'Inter', sans-serif", letterSpacing: "-0.05em" }}
        >
          e
        </span>
      </div>
    );
  }

  return (
    <div className="h-[35px] flex items-center">
      {/* Wordmark: lowercase "epitome" matching the pitch deck style */}
      <div className="flex items-center gap-0.5">
        <span
          className="text-[22px] font-light tracking-tight text-foreground"
          style={{ fontFamily: "'Inter', sans-serif", letterSpacing: "-0.04em" }}
        >
          epitome
        </span>
        {/* Small teal accent dot — nods to the pitch deck's geometric mark */}
        <span
          className="ml-0.5 mb-1 h-[5px] w-[5px] rounded-full bg-primary inline-block flex-shrink-0"
        />
      </div>
    </div>
  );
}
