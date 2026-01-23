import svgPaths from "@/lib/svg-paths";

interface EpitomeLogoProps {
  collapsed?: boolean;
}

export function EpitomeLogo({ collapsed = false }: EpitomeLogoProps) {
  if (collapsed) {
    return (
      <div className="h-[35px] w-[35px] flex items-center justify-center">
        <span className="text-2xl font-bold text-[#6BA4E8]" style={{ fontFamily: 'system-ui' }}>E</span>
      </div>
    );
  }

  return (
    <div className="h-[35px] w-[162px]">
      <svg 
        className="block size-full" 
        fill="none" 
        preserveAspectRatio="none" 
        viewBox="0 0 162.15 34.5"
      >
        <g clipPath="url(#clip0_epitome_logo)">
          <path d={svgPaths.p22942400} fill="#6BA4E8" />
          <path d={svgPaths.p3583f600} fill="#6BA4E8" />
          <path d={svgPaths.p38723980} fill="#6BA4E8" />
          <path d={svgPaths.p2b548a00} fill="#6BA4E8" />
          <path d={svgPaths.p23aef080} fill="#6BA4E8" />
          <path d={svgPaths.p1e6243f0} fill="#6BA4E8" />
          <path d={svgPaths.p1cf3c600} fill="#6BA4E8" />
        </g>
        <defs>
          <clipPath id="clip0_epitome_logo">
            <rect fill="white" height="34.5" width="162.15" />
          </clipPath>
        </defs>
      </svg>
    </div>
  );
}
