import React, { useState, useEffect, useRef } from 'react';
import { Search, X, Server, Globe, Link2, Hash, FileText, ArrowRight, ShieldAlert } from 'lucide-react';
import { api } from '../api/client';
import { ThreatBadge } from './ThreatBadge';

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectSubmission: (id: string) => void;
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({
  isOpen,
  onClose,
  onSelectSubmission
}) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 50);
      setQuery('');
      loadInitial();
    }
  }, [isOpen]);

  const loadInitial = async () => {
    setLoading(true);
    try {
      const resp = await api.listEmails({ page: 1, limit: 6 });
      const items = Array.isArray(resp) ? resp : (resp?.results || []);
      setResults(items);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!query.trim()) return;
    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const resp = await api.listEmails({ page: 1, limit: 12 });
        const items = Array.isArray(resp) ? resp : (resp?.results || []);
        const filtered = items.filter((item: any) => {
          const q = query.toLowerCase();
          return (
            (item.sender && item.sender.toLowerCase().includes(q)) ||
            (item.subject && item.subject.toLowerCase().includes(q)) ||
            (item.submission_id && item.submission_id.toLowerCase().includes(q)) ||
            (item.classification && item.classification.toLowerCase().includes(q))
          );
        });
        setResults(filtered);
        setSelectedIndex(0);
      } catch {
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 150);

    return () => clearTimeout(timer);
  }, [query]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;
      if (e.key === 'Escape') {
        onClose();
      } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex(i => (i + 1) % (results.length || 1));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex(i => (i - 1 + results.length) % (results.length || 1));
      } else if (e.key === 'Enter') {
        if (results[selectedIndex]) {
          onSelectSubmission(results[selectedIndex].submission_id);
          onClose();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, results, selectedIndex]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-xs flex items-start justify-center pt-10 sm:pt-20 p-3 sm:p-4 font-mono select-none">
      <div className="w-full max-w-2xl bg-[#12161B] border border-[#3A4551] rounded-lg shadow-2xl overflow-hidden animate-in fade-in-0 zoom-in-95 duration-150 flex flex-col max-h-[80vh] sm:max-h-[560px]">
        {/* Search Header */}
        <div className="p-3.5 border-b border-[#232A32] flex items-center gap-3 bg-[#0A0D10]">
          <Search className="w-4 h-4 text-[#E8A33D] flex-shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search IP, domain, email, hash, or case..."
            className="w-full bg-transparent text-xs text-[#E7EBEF] placeholder-[#566270] focus:outline-hidden font-mono min-h-[32px]"
          />
          {query && (
            <button
              onClick={() => setQuery('')}
              className="p-1.5 text-[#8B96A3] hover:text-white min-h-[32px] min-w-[32px] flex items-center justify-center"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
          <kbd className="hidden sm:inline-block px-1.5 py-0.5 rounded bg-[#191F26] border border-[#232A32] text-[9px] text-[#8B96A3]">
            ESC
          </kbd>
        </div>

        {/* Results List */}
        <div className="p-2 divide-y divide-[#232A32] overflow-y-auto flex-1 text-xs">
          {loading ? (
            <div className="p-8 text-center text-[#8B96A3] text-xs">Searching forensic artifacts...</div>
          ) : results.length > 0 ? (
            results.map((item, idx) => {
              const isSelected = selectedIndex === idx;
              return (
                <div
                  key={item.submission_id}
                  onClick={() => {
                    onSelectSubmission(item.submission_id);
                    onClose();
                  }}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  className={`p-3 rounded cursor-pointer transition-colors flex items-center justify-between gap-3 ${
                    isSelected ? 'bg-[#191F26] border border-[#E8A33D]/50' : 'hover:bg-[#191F26]/50 border border-transparent'
                  }`}
                >
                  <div className="space-y-1 min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-1.5 sm:gap-2">
                      <span className="text-[#E8A33D] font-bold text-[11px]">
                        CASE-{item.submission_id.slice(0, 8).toUpperCase()}
                      </span>
                      <ThreatBadge type="risk" value={item.risk_level} size="xs" />
                      <ThreatBadge type="classification" value={item.classification} size="xs" />
                    </div>
                    <div className="text-[#E7EBEF] font-sans text-xs truncate font-semibold">
                      {item.subject || 'No Subject'}
                    </div>
                    <div className="text-[10px] text-[#8B96A3] truncate">
                      From: {item.sender || 'Unknown'}
                    </div>
                  </div>

                  <div className="flex items-center gap-2 flex-shrink-0">
                    <span className="font-bold text-xs text-[#E7EBEF]">
                      {Math.round((item.fraud_score || 0) * 100)}/100
                    </span>
                    <ArrowRight className="w-3.5 h-3.5 text-[#8B96A3]" />
                  </div>
                </div>
              );
            })
          ) : (
            <div className="p-8 text-center text-[#8B96A3] text-xs">
              No matching forensic artifacts found for query.
            </div>
          )}
        </div>

        {/* Footer shortcuts */}
        <div className="p-2.5 border-t border-[#232A32] bg-[#0A0D10] text-[10px] text-[#566270] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="hidden sm:inline">↑↓ Navigate</span>
            <span>↵ Select</span>
            <span>ESC Dismiss</span>
          </div>
          <span className="text-[#E8A33D]">TraceX Command Center</span>
        </div>
      </div>
    </div>
  );
};
