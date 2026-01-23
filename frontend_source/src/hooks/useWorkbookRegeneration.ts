/**
 * React hook for managing workbook regeneration state.
 * Tracks regeneration loading state and current download filename.
 */
import { useState, useCallback, useRef } from 'react';
import { regenerateWorkbook } from '@/lib/api';
import { toast } from 'sonner';

interface UseWorkbookRegenerationResult {
  /** Whether regeneration is currently in progress */
  isRegenerating: boolean;
  /** Current download filename (updated after regeneration) */
  downloadFilename: string | null;
  /** Trigger workbook regeneration */
  regenerate: () => Promise<void>;
  /** Manually set the filename (e.g., from URL params on initial load) */
  setFilename: (filename: string | null) => void;
}

/**
 * Hook for managing workbook regeneration.
 *
 * @param projectId - The project ID to regenerate
 * @param initialFilename - Initial filename from URL params
 */
export function useWorkbookRegeneration(
  projectId: string | null,
  initialFilename: string | null
): UseWorkbookRegenerationResult {
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [downloadFilename, setDownloadFilename] = useState<string | null>(initialFilename);

  // Track current regeneration to avoid race conditions
  const regenerationCounter = useRef(0);

  const regenerate = useCallback(async () => {
    if (!projectId) {
      console.warn('Cannot regenerate: no projectId');
      return;
    }

    // Increment counter to track this regeneration
    const thisRegeneration = ++regenerationCounter.current;

    setIsRegenerating(true);

    try {
      const result = await regenerateWorkbook(projectId);

      // Only update filename if this is still the latest regeneration
      if (thisRegeneration === regenerationCounter.current) {
        setDownloadFilename(result.filename);
      }
    } catch (error) {
      // Only show error if this is still the latest regeneration
      if (thisRegeneration === regenerationCounter.current) {
        console.error('Failed to regenerate workbook:', error);
        toast.error('Failed to update workbook');
      }
    } finally {
      // Only clear loading if this is still the latest regeneration
      if (thisRegeneration === regenerationCounter.current) {
        setIsRegenerating(false);
      }
    }
  }, [projectId]);

  const setFilename = useCallback((filename: string | null) => {
    setDownloadFilename(filename);
  }, []);

  return {
    isRegenerating,
    downloadFilename,
    regenerate,
    setFilename,
  };
}
