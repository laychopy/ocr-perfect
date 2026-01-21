export type JobStatus = 'pending' | 'processing' | 'completed' | 'failed';

export type OutputFormat = 'docx' | 'txt' | 'md';

export interface Job {
  id: string;
  user_id: string;
  filename: string;
  file_size: number;
  status: JobStatus;
  output_format: OutputFormat;
  input_path: string;
  output_path?: string;
  error_message?: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

export interface UploadResponse {
  job_id: string;
  upload_url: string;
  message: string;
}

export interface JobListResponse {
  jobs: Job[];
  total: number;
}

export interface DownloadResponse {
  download_url: string;
  filename: string;
  expires_in: number;
}
