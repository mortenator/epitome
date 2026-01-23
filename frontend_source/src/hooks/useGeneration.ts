/**
 * Hook for managing workbook generation state and SSE progress.
 */
import { useState, useCallback, useRef, useEffect } from 'react';
import { generateWorkbook, subscribeToProgress, ProgressEvent } from '@/lib/api';

export interface GenerationState {
  status: 'idle' | 'generating' | 'complete' | 'error';
  progress: ProgressEvent | null;
  jobId: string | null;
  downloadFilename: string | null;
  projectId: string | null;
  error: string | null;
}

const initialState: GenerationState = {
  status: 'idle',
  progress: null,
  jobId: null,
  downloadFilename: null,
  projectId: null,
  error: null,
};

/**
 * Hook for managing the workbook generation flow.
 *
 * Usage:
 * ```tsx
 * const { status, progress, startGeneration, reset } = useGeneration();
 *
 * // Start generation
 * await startGeneration(prompt, file);
 *
 * // Watch progress
 * if (status === 'generating') {
 *   console.log(`${progress?.percent}%: ${progress?.message}`);
 * }
 *
 * // Handle completion
 * if (status === 'complete') {
 *   navigate(`/callsheet?project=${projectId}&download=${downloadFilename}`);
 * }
 * ```
 */
export function useGeneration() {
  const [state, setState] = useState<GenerationState>(initialState);
  const unsubscribeRef = useRef<(() => void) | null>(null);

  // Clean up SSE subscription on unmount
  useEffect(() => {
    return () => {
      if (unsubscribeRef.current) {
        unsubscribeRef.current();
      }
    };
  }, []);

  const startGeneration = useCallback(async (prompt: string, file?: File) => {
    // Reset state
    setState({
      ...initialState,
      status: 'generating',
    });

    try {
      // Start generation and get job_id
      const { job_id } = await generateWorkbook(prompt, file);
      setState((prev) => ({ ...prev, jobId: job_id }));

      // Subscribe to progress updates
      const unsubscribe = subscribeToProgress(
        job_id,
        // onProgress
        (progress) => {
          setState((prev) => ({ ...prev, progress }));
        },
        // onComplete
        (filename, projectId) => {
          setState((prev) => ({
            ...prev,
            status: 'complete',
            downloadFilename: filename,
            projectId: projectId || null,
          }));
        },
        // onError
        (error) => {
          setState((prev) => ({
            ...prev,
            status: 'error',
            error,
          }));
        }
      );

      unsubscribeRef.current = unsubscribe;
      return job_id;
    } catch (err) {
      setState((prev) => ({
        ...prev,
        status: 'error',
        error: err instanceof Error ? err.message : 'Unknown error',
      }));
      return null;
    }
  }, []);

  const reset = useCallback(() => {
    if (unsubscribeRef.current) {
      unsubscribeRef.current();
      unsubscribeRef.current = null;
    }
    setState(initialState);
  }, []);

  return {
    ...state,
    startGeneration,
    reset,
  };
}

/**
 * Map of stage IDs to user-friendly labels.
 */
export const STAGE_LABELS: Record<string, string> = {
  'analyzing_file': 'Reviewing your files',
  'understanding_prompt': 'Understanding your request',
  'preparing_extraction': 'Preparing AI prompt',
  'sending_to_ai': 'Sending to AI',
  'ai_processing': 'AI is analyzing your data',
  'parsing_response': 'Processing AI response',
  'extraction_complete': 'Extraction complete',
  'extracting_data': 'Extracting project details', // legacy
  'enriching_location': 'Finding location info',
  'enriching_weather': 'Getting weather forecast',
  'enriching_logo': 'Looking up company info',
  'enrichment_complete': 'Data enrichment complete',
  'generating': 'Building your call sheet',
  'saving_file': 'Saving workbook',
  'saving_database': 'Saving to database',
  'ready': 'Your call sheet is ready!',
  'complete': 'Complete',
  'download_ready': 'Ready!',
};

/**
 * Get a user-friendly label for a stage ID.
 */
export function getStageLabel(stageId: string): string {
  return STAGE_LABELS[stageId] || stageId;
}
