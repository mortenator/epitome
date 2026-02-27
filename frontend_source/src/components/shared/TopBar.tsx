import { Upload, Download, Loader2 } from "lucide-react";

interface TopBarProps {
  onDistributeClick?: () => void;
  onDownloadClick?: () => void;
  /** Whether the workbook is being regenerated */
  isRegenerating?: boolean;
  /** Whether download is enabled (has a valid filename) */
  downloadEnabled?: boolean;
}

export function TopBar({
  onDistributeClick,
  onDownloadClick,
  isRegenerating = false,
  downloadEnabled = true,
}: TopBarProps) {
  const isDisabled = isRegenerating || !downloadEnabled;

  return (
    <div className="flex items-center justify-between border-b border-border bg-background px-3 md:px-4 min-h-[52px]">
      <div className="flex items-center gap-2 rounded-lg border border-border px-2 md:px-3 py-1.5">
        <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
        </svg>
        <span className="text-sm text-foreground">Preview</span>
      </div>
      <div className="flex items-center gap-2 md:gap-3">
        <button
          onClick={onDistributeClick}
          className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
        >
          <Upload className="h-4 w-4" />
          <span className="hidden sm:inline">Distribute</span>
        </button>
        <button
          onClick={onDownloadClick}
          disabled={isDisabled}
          className={`rounded-full px-3 md:px-4 py-1.5 text-sm font-medium text-white flex items-center gap-1.5 transition-colors ${
            isDisabled
              ? "bg-blue-400 cursor-not-allowed"
              : "bg-blue-500 hover:bg-blue-600"
          }`}
        >
          {isRegenerating ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="hidden sm:inline">Updating...</span>
              <span className="sm:hidden">...</span>
            </>
          ) : (
            <>
              <Download className="h-4 w-4 sm:hidden" />
              <span className="hidden sm:inline">Download</span>
              <span className="sm:hidden">Save</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}
