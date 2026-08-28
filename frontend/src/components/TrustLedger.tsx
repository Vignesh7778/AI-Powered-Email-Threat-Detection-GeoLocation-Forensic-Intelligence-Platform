import React from 'react';

interface TrustLedgerProps {
  verifiedCount?: number;
  predictedCount?: number;
  inferredCount?: number;
  unknownCount?: number;
  className?: string;
}

export const TrustLedger: React.FC<TrustLedgerProps> = ({
  verifiedCount = 14,
  predictedCount = 3,
  inferredCount = 2,
  unknownCount = 1,
  className = ''
}) => {
  return (
    <div className={`h-8 bg-[#0A0D10] border-b border-[#232A32] px-4 flex items-center justify-between font-mono text-[11px] select-none text-[#8B96A3] ${className}`}>
      <div className="flex items-center gap-4">
        <span className="text-[10px] uppercase font-bold tracking-wider text-[#566270] font-sans">
          Trust Ledger:
        </span>
        
        <div className="flex items-center gap-1.5 text-[#E7EBEF]">
          <span className="w-2 h-2 rounded-full bg-[#2DD4BF] shadow-[0_0_6px_#2DD4BF80]" />
          <span className="font-semibold text-[#2DD4BF]">{verifiedCount}</span>
          <span className="text-[#8B96A3]">Verified</span>
        </div>

        <span className="text-[#232A32]">|</span>

        <div className="flex items-center gap-1.5 text-[#E7EBEF]">
          <span className="w-2 h-2 rounded-full bg-[#E8A33D] shadow-[0_0_6px_#E8A33D80]" />
          <span className="font-semibold text-[#E8A33D]">{predictedCount}</span>
          <span className="text-[#8B96A3]">Predicted</span>
        </div>

        <span className="text-[#232A32]">|</span>

        <div className="flex items-center gap-1.5 text-[#E7EBEF]">
          <span className="w-2 h-2 rounded-full bg-[#8B8FE8] shadow-[0_0_6px_#8B8FE880]" />
          <span className="font-semibold text-[#8B8FE8]">{inferredCount}</span>
          <span className="text-[#8B96A3]">Inferred</span>
        </div>

        <span className="text-[#232A32]">|</span>

        <div className="flex items-center gap-1.5 text-[#8B96A3]">
          <span className="w-2 h-2 rounded-full bg-[#566270]" />
          <span className="font-semibold text-[#8B96A3]">{unknownCount}</span>
          <span className="text-[#566270]">Unknown</span>
        </div>
      </div>

      <div className="hidden sm:flex items-center gap-2 text-[10px] text-[#566270]">
        <span>Strict 4-Tier Truth Model</span>
        <span className="w-1.5 h-1.5 rounded-full bg-[#2DD4BF]" />
        <span>Court Admissible</span>
      </div>
    </div>
  );
};
