/**
 * React Query hooks for project data fetching and mutations.
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getProject, getGenerationData, updateCrewMember, searchCrew, ProjectData, AvailableCrewMember } from '@/lib/api';

/**
 * Fetch project data by ID.
 * Returns departments, call sheets, locations, and project info.
 * If isJobId is true, uses the generation data endpoint (fallback when database save fails).
 */
export function useProject(projectId: string | null, isJobId: boolean = false) {
  return useQuery<ProjectData>({
    queryKey: ['project', projectId, isJobId],
    queryFn: () => {
      if (isJobId && projectId) {
        // Use fallback endpoint for generation data
        return getGenerationData(projectId);
      } else {
        // Use normal project endpoint
        return getProject(projectId!);
      }
    },
    enabled: !!projectId,
    staleTime: 30000, // 30 seconds before refetch
    retry: 2,
  });
}

/**
 * Mutation for updating crew member call time/location.
 * Automatically invalidates project query on success.
 */
export function useUpdateCrewMember() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      crewId,
      updates,
    }: {
      crewId: string;
      updates: { callTime?: string; location?: string; callSheetId?: string };
    }) => updateCrewMember(crewId, updates),

    onSuccess: () => {
      // Invalidate project query to refetch updated data
      queryClient.invalidateQueries({ queryKey: ['project'] });
    },

    onError: (error) => {
      console.error('Failed to update crew member:', error);
    },
  });
}

/**
 * Search available crew members.
 */
export function useCrewSearch(query: string, department?: string) {
  return useQuery<AvailableCrewMember[]>({
    queryKey: ['crew-search', query, department],
    queryFn: () => searchCrew(query, department),
    enabled: query.length > 0,
    staleTime: 60000, // 1 minute
  });
}
