import { useState, useEffect, useCallback } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { createApiService } from '../services/api';
import FileUpload from '../components/FileUpload';
import JobList from '../components/JobList';
import { Job, OutputFormat } from '../types';

export default function Dashboard() {
  const { user, loading, signOut, getIdToken } = useAuth();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const api = createApiService(getIdToken);

  const fetchJobs = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await api.listJobs();
      setJobs(response.jobs);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch jobs');
    } finally {
      setIsLoading(false);
    }
  }, [api]);

  useEffect(() => {
    if (user) {
      fetchJobs();
      // Poll for updates every 10 seconds
      const interval = setInterval(fetchJobs, 10000);
      return () => clearInterval(interval);
    }
  }, [user, fetchJobs]);

  const handleUpload = async (file: File, outputFormat: OutputFormat) => {
    setIsUploading(true);
    setError(null);
    try {
      await api.uploadFile(file, outputFormat);
      await fetchJobs();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
      throw err;
    } finally {
      setIsUploading(false);
    }
  };

  const handleDownload = async (jobId: string) => {
    try {
      const response = await api.getDownloadUrl(jobId);
      window.open(response.download_url, '_blank');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Download failed');
    }
  };

  const handleDelete = async (jobId: string) => {
    if (!confirm('Are you sure you want to delete this job?')) return;

    try {
      await api.deleteJob(jobId);
      setJobs((prev) => prev.filter((j) => j.id !== jobId));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Delete failed');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/" replace />;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900">OCR Perfect</h1>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                {user.photoURL && (
                  <img
                    src={user.photoURL}
                    alt={user.displayName || 'User'}
                    className="w-8 h-8 rounded-full"
                  />
                )}
                <span className="text-sm text-gray-700">
                  {user.displayName || user.email}
                </span>
              </div>
              <button
                onClick={signOut}
                className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
              >
                Sign out
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-700">{error}</p>
            <button
              onClick={() => setError(null)}
              className="mt-2 text-sm text-red-600 hover:text-red-800"
            >
              Dismiss
            </button>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <FileUpload onUpload={handleUpload} isUploading={isUploading} />
          <JobList
            jobs={jobs}
            onDownload={handleDownload}
            onDelete={handleDelete}
            onRefresh={fetchJobs}
            isLoading={isLoading}
          />
        </div>
      </main>
    </div>
  );
}
