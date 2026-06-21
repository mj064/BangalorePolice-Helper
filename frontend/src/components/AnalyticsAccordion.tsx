import React, { useState } from 'react';
import { ChevronDown } from 'lucide-react';

interface AnalyticsAccordionProps {
  title: string;
  icon: React.ReactNode;
  defaultOpen?: boolean;
  children: React.ReactNode;
}

export const AnalyticsAccordion: React.FC<AnalyticsAccordionProps> = ({
  title,
  icon,
  defaultOpen = false,
  children,
}) => {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className="overflow-hidden rounded-xl border border-white/8 bg-black/20">
      <button
        type="button"
        onClick={() => setOpen((current) => !current)}
        className="flex w-full items-center justify-between px-3 py-3 text-left transition hover:bg-white/[0.02]"
      >
        <span className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-400">
          {icon}
          {title}
        </span>
        <ChevronDown className={`h-4 w-4 text-slate-500 transition ${open ? 'rotate-180' : ''}`} />
      </button>
      {open && <div className="border-t border-white/8 px-3 py-3">{children}</div>}
    </div>
  );
};
