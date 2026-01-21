import { Job, JobListResponse, UploadResponse, DownloadResponse, OutputFormat, JobStatus } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080';

class ApiService {
  private getAuthHeader: () => Promise<Record<string, string>>;

  constructor(getAuthHeader: () => Promise<Record<string, string>>) {
    this.getAuthHeader = getAuthHeader;
  }

  private async fetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const headers = await this.getAuthHeader();

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        ...headers,
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(error.detail || 'Request failed');
    }

    if (response.status === 204) {
      return undefined as T;
    }

    return response.json();
  }

  async uploadFile(file: File, outputFormat: OutputFormat = 'docx'): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('output_format', outputFormat);

    const headers = await this.getAuthHeader();

    const response = await fetch(`${API_BASE_URL}/api/upload`, {
      method: 'POST',
      headers,
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(error.detail || 'Upload failed');
    }

    return response.json();
  }

  async listJobs(statusFilter?: JobStatus, limit: number = 50): Promise<JobListResponse> {
    const params = new URLSearchParams();
    if (statusFilter) params.append('status_filter', statusFilter);
    params.append('limit', limit.toString());

    const queryString = params.toString();
    return this.fetch<JobListResponse>(`/api/jobs${queryString ? `?${queryString}` : ''}`);
  }

  async getJob(jobId: string): Promise<Job> {
    return this.fetch<Job>(`/api/jobs/${jobId}`);
  }

  async getDownloadUrl(jobId: string): Promise<DownloadResponse> {
    return this.fetch<DownloadResponse>(`/api/jobs/${jobId}/download`);
  }

  async deleteJob(jobId: string): Promise<void> {
    return this.fetch<void>(`/api/jobs/${jobId}`, {
      method: 'DELETE',
    });
  }
}

export function createApiService(getIdToken: () => Promise<string | null>): ApiService {
  const getAuthHeader = async (): Promise<Record<string, string>> => {
    const token = await getIdToken();
    if (!token) {
      throw new Error('Not authenticated');
    }
    return {
      Authorization: `Bearer ${token}`,
    };
  };

  return new ApiService(getAuthHeader);
}
