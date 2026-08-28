import React, { useState, useRef } from 'react';
import { X, UploadCloud, FileCheck, AlertCircle, RefreshCw, Hash } from 'lucide-react';
import { api } from '../api/client';

interface IngestModalProps {
  isOpen: boolean;
  onClose: () => void;
  onIngestSuccess: (submissionId: string) => void;
}

export const IngestModal: React.FC<IngestModalProps> = ({ isOpen, onClose, onIngestSuccess }) => {
  const [file, setFile] = useState<File | null>(null);
  const [fileSha256, setFileSha256] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progressText, setProgressText] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const computeSha256 = async (f: File) => {
    try {
      const buffer = await f.arrayBuffer();
      const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
      const hashArray = Array.from(new Uint8Array(hashBuffer));
      const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
      setFileSha256(hashHex);
    } catch {
      setFileSha256(null);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      setFile(selected);
      setError(null);
      computeSha256(selected);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const dropped = e.dataTransfer.files[0];
      setFile(dropped);
      setError(null);
      computeSha256(dropped);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError('Please select an RFC 5322 .eml or raw email artifact to analyze.');
      return;
    }

    setLoading(true);
    setError(null);
    setProgressText('Parsing RFC 5322 headers & calculating SHA-256 custody seal...');

    try {
      setTimeout(() => setProgressText('Validating SPF, DKIM & DMARC DNS policies...'), 400);
      setTimeout(() => setProgressText('Tracing Received relay hops & resolving live GeoIP...'), 800);
      setTimeout(() => setProgressText('Executing NLP social engineering & lookalike checks...'), 1200);
      setTimeout(() => setProgressText('Querying Groq AI evidence-grounded reasoning layer...'), 1600);

      const resp = await api.ingestRawEmail(file);
      onIngestSuccess(resp.submission_id);
    } catch (err: any) {
      setError(err?.message || 'Analysis pipeline encountered an error processing this message.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
      <div className="relative w-full max-w-lg bg-[#161b22] rounded-lg p-5 border border-[#30363d] shadow-2xl space-y-4">
        {/* Modal Header */}
        <div className="flex items-center justify-between pb-3 border-b border-[#21262d]">
          <div>
            <h3 className="text-sm font-bold text-slate-100 tracking-tight">Ingest Email Evidence Artifact</h3>
            <p className="text-[11px] text-slate-400 font-mono">Upload raw RFC 5322 .eml for automated multi-stage forensic analysis</p>
          </div>
          <button
            onClick={onClose}
            disabled={loading}
            className="p-1 rounded text-slate-400 hover:text-white hover:bg-[#21262d] transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {error && (
          <div className="p-3 rounded bg-red-950/50 border border-red-800/60 flex items-start gap-2.5 text-xs text-red-200 font-mono">
            <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border border-dashed rounded-lg p-6 text-center cursor-pointer transition-all ${
              file
                ? 'border-amber-500/60 bg-amber-950/10'
                : 'border-[#30363d] hover:border-amber-500/40 bg-[#0d1117]'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".eml,.msg,.txt"
              onChange={handleFileChange}
              className="hidden"
            />
            {file ? (
              <div className="flex flex-col items-center gap-1.5 font-mono text-left">
                <FileCheck className="w-8 h-8 text-amber-400 mb-1" />
                <div className="text-xs font-bold text-slate-100 truncate max-w-sm">{file.name}</div>
                <div className="text-[10px] text-slate-400">
                  Size: {(file.size / 1024).toFixed(1)} KB
                </div>
                {fileSha256 && (
                  <div className="text-[9px] text-slate-400 flex items-center gap-1 mt-1 bg-[#161b22] px-2 py-0.5 rounded border border-[#21262d]">
                    <Hash className="w-2.5 h-2.5 text-amber-400" />
                    <span>SHA-256: {fileSha256.slice(0, 24)}...</span>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex flex-col items-center gap-2">
                <UploadCloud className="w-8 h-8 text-slate-400 hover:text-amber-400 transition-colors" />
                <div className="text-xs font-medium text-slate-200">
                  Click or drag and drop <span className="text-amber-400 font-mono">.eml</span> email file here
                </div>
                <div className="text-[10px] font-mono text-slate-400">
                  RFC 5322 MIME formats with headers, multipart bodies, and static attachments
                </div>
              </div>
            )}
          </div>

          {loading && (
            <div className="p-3 rounded bg-[#0d1117] border border-[#21262d] flex items-center gap-2.5 text-xs font-mono text-amber-300">
              <RefreshCw className="w-3.5 h-3.5 animate-spin text-amber-400 flex-shrink-0" />
              <span>{progressText}</span>
            </div>
          )}

          <div className="flex items-center justify-end gap-2.5 pt-2 border-t border-[#21262d]">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="px-3.5 py-1.5 rounded text-xs font-mono text-slate-400 hover:text-white hover:bg-[#21262d] transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !file}
              className="px-4 py-1.5 rounded bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-mono font-bold shadow-sm disabled:opacity-50 transition-all"
            >
              {loading ? 'Processing Pipeline...' : 'Run Forensic Ingestion'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

