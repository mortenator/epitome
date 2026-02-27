/**
 * API client for Epitome backend.
 * Handles communication with FastAPI endpoints.
 */

const API_BASE = '/api';

// =============================================================================
// Types
// =============================================================================

export interface GenerateResponse {
  job_id: string;
  status: string;
}

export interface ProgressEvent {
  stage_id: string;
  percent: number;
  message: string;
  timestamp: string;
}

export interface ResultResponse {
  status: 'complete' | 'error';
  data?: Record<string, unknown>;
  download_filename?: string;
  project_id?: string;
  error?: string;
}

export interface CrewMember {
  id?: string;
  role: string;
  name?: string;
  phone?: string;
  email?: string;
  callTime?: string;
  location?: string;
}

export interface Department {
  name: string;
  count: number;
  expanded: boolean;
  crew: CrewMember[];
}

export interface WeatherData {
  high?: string;
  low?: string;
  summary?: string;
  sunrise?: string;
  sunset?: string;
}

export interface CallSheetData {
  id: string;
  dayNumber: number;
  shootDate: string;
  generalCrewCall: string;
  breakfastCall?: string;
  productionCall?: string;
  talentCall?: string;
  weather: WeatherData;
  hospital?: {
    name?: string;
    address?: string;
  };
}

export interface LocationData {
  id: string;
  name: string;
  address?: string;
  city?: string;
  state?: string;
  mapLink?: string;
  parkingNotes?: string;
}

export interface ProjectData {
  project: {
    id: string;
    jobName: string;
    jobNumber: string;
    client: string;
    agency?: string;
  };
  callSheets: CallSheetData[];
  locations: LocationData[];
  departments: Department[];
}

export interface AvailableCrewMember {
  id: string;
  name: string;
  role: string;
  phone?: string;
  email?: string;
  department?: string;
}

export interface ChatResponse {
  type: 'answer' | 'edit';
  response: string;
  action?: string;
  success?: boolean;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

// =============================================================================
// API Functions
// =============================================================================

/**
 * Start workbook generation.
 * Returns a job_id for progress tracking.
 */
export async function generateWorkbook(prompt: string, file?: File): Promise<GenerateResponse> {
  const formData = new FormData();
  // Send empty string if prompt is empty (backend will handle it)
  formData.append('prompt', prompt || '');
  if (file) {
    formData.append('file', file);
  }

  const response = await fetch(`${API_BASE}/generate`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(error || 'Failed to start generation');
  }

  return response.json();
}

/**
 * Subscribe to generation progress via Server-Sent Events.
 * Returns an unsubscribe function.
 */
export function subscribeToProgress(
  jobId: string,
  onProgress: (event: ProgressEvent) => void,
  onComplete: (filename: string, projectId?: string, jobId?: string) => void,
  onError: (error: string) => void
): () => void {
  const eventSource = new EventSource(`${API_BASE}/progress/${jobId}`);

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data) as ProgressEvent;

      if (data.stage_id === 'download_ready') {
        // Parse the message JSON to get filename, project_id, and job_id (fallback)
        const info = JSON.parse(data.message);
        onComplete(info.filename, info.project_id, info.job_id);
        eventSource.close();
      } else if (data.stage_id === 'error') {
        onError(data.message);
        eventSource.close();
      } else {
        onProgress(data);
      }
    } catch (e) {
      console.error('Failed to parse SSE event:', e);
    }
  };

  eventSource.onerror = () => {
    onError('Connection lost');
    eventSource.close();
  };

  return () => eventSource.close();
}

/**
 * Get the result of a completed generation job.
 */
export async function getResult(jobId: string): Promise<ResultResponse> {
  const response = await fetch(`${API_BASE}/result/${jobId}`);
  if (!response.ok) {
    throw new Error('Failed to get result');
  }
  return response.json();
}

/**
 * Fetch project data from generation result (fallback when database save fails).
 */
export async function getGenerationData(jobId: string): Promise<ProjectData> {
  const response = await fetch(`${API_BASE}/generation/${jobId}/data`);
  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Generation data not found');
    }
    throw new Error('Failed to fetch generation data');
  }
  return response.json();
}

/**
 * Fetch project data for the call sheet preview.
 */
export async function getProject(projectId: string): Promise<ProjectData> {
  const response = await fetch(`${API_BASE}/project/${projectId}`);
  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Project not found');
    }
    throw new Error('Failed to fetch project');
  }
  return response.json();
}

/**
 * Update a crew member's call time or location.
 */
export async function updateCrewMember(
  crewId: string,
  updates: { callTime?: string; location?: string; callSheetId?: string }
): Promise<void> {
  const params = new URLSearchParams();
  if (updates.callTime) params.append('callTime', updates.callTime);
  if (updates.location) params.append('location', updates.location);
  if (updates.callSheetId) params.append('callSheetId', updates.callSheetId);

  const response = await fetch(`${API_BASE}/crew/${crewId}?${params}`, {
    method: 'PATCH',
  });

  if (!response.ok) {
    throw new Error('Failed to update crew member');
  }
}

/**
 * Search available crew members from the organization database.
 */
export async function searchCrew(
  query: string = '',
  department?: string
): Promise<AvailableCrewMember[]> {
  const params = new URLSearchParams();
  if (query) params.append('q', query);
  if (department) params.append('department', department);

  const response = await fetch(`${API_BASE}/crew/search?${params}`);
  if (!response.ok) {
    throw new Error('Failed to search crew');
  }

  const data = await response.json();
  return data.crew;
}

/**
 * Get the download URL for a workbook file.
 */
export function getDownloadUrl(filename: string): string {
  return `${API_BASE}/download/${encodeURIComponent(filename)}`;
}

/**
 * Download a workbook file.
 * Opens the file in a new tab/triggers download.
 */
export function downloadWorkbook(filename: string): void {
  window.open(getDownloadUrl(filename), '_blank');
}

export interface RegenerateResponse {
  filename: string;
  download_url: string;
}

/**
 * Regenerate the Excel workbook from current database state.
 * Called after data changes to sync the Excel with latest project data.
 */
export async function regenerateWorkbook(projectId: string): Promise<RegenerateResponse> {
  const response = await fetch(`${API_BASE}/project/${projectId}/regenerate`, {
    method: 'POST',
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(error || 'Failed to regenerate workbook');
  }

  return response.json();
}

/**
 * Send a chat message to the AI assistant.
 * Can be used for Q&A or edit commands.
 * Supports multi-turn conversation by passing message history.
 */
export async function sendChatMessage(
  projectId: string,
  message: string,
  history: ChatMessage[] = []
): Promise<ChatResponse> {
  const formData = new FormData();
  formData.append('project_id', projectId);
  formData.append('message', message);

  // Send conversation history as JSON
  if (history.length > 0) {
    formData.append('history', JSON.stringify(history));
  }

  const response = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(error || 'Failed to send chat message');
  }

  return response.json();
}

export interface ProjectSummary {
  id: string;
  jobName: string;
  client: string;
  status: string;
  createdAt: string | null;
}

export interface CrewSummary {
  id: string;
  name: string;
  role: string;
  department: string;
  email: string;
  phone: string;
}

export async function listProjects(): Promise<ProjectSummary[]> {
  const response = await fetch(`${API_BASE}/projects`);
  if (!response.ok) throw new Error('Failed to fetch projects');
  return response.json();
}

export async function listCrew(): Promise<CrewSummary[]> {
  const response = await fetch(`${API_BASE}/crew`);
  if (!response.ok) throw new Error('Failed to fetch crew');
  return response.json();
}
