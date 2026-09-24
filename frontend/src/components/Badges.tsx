import React from 'react';
import { Priority, SLAStatus, TicketStatus } from '../types';

export const StatusBadge: React.FC<{ status: TicketStatus }> = ({ status }) => {
  const map: Record<TicketStatus, { bg: string; text: string; label: string }> = {
    NEW: { bg: 'bg-blue-100 border-blue-200', text: 'text-blue-800', label: 'NEW' },
    ASSIGNED: { bg: 'bg-purple-100 border-purple-200', text: 'text-purple-800', label: 'ASSIGNED' },
    IN_PROGRESS: { bg: 'bg-amber-100 border-amber-200', text: 'text-amber-800', label: 'IN PROGRESS' },
    WAITING_FOR_STUDENT: { bg: 'bg-orange-100 border-orange-200', text: 'text-orange-800', label: 'WAITING STUDENT' },
    RESOLVED: { bg: 'bg-emerald-100 border-emerald-200', text: 'text-emerald-800', label: 'RESOLVED' },
    CLOSED: { bg: 'bg-slate-100 border-slate-200', text: 'text-slate-700', label: 'CLOSED' },
    REOPENED: { bg: 'bg-rose-100 border-rose-200', text: 'text-rose-800', label: 'REOPENED' },
  };

  const current = map[status] || { bg: 'bg-gray-100 border-gray-200', text: 'text-gray-800', label: status };

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${current.bg} ${current.text}`}>
      {current.label}
    </span>
  );
};

export const PriorityBadge: React.FC<{ priority: Priority }> = ({ priority }) => {
  const map: Record<Priority, { bg: string; text: string; dot: string }> = {
    LOW: { bg: 'bg-slate-50 border-slate-200', text: 'text-slate-700', dot: 'bg-slate-400' },
    MEDIUM: { bg: 'bg-sky-50 border-sky-200', text: 'text-sky-700', dot: 'bg-sky-500' },
    HIGH: { bg: 'bg-amber-50 border-amber-200', text: 'text-amber-700', dot: 'bg-amber-500' },
    URGENT: { bg: 'bg-rose-50 border-rose-200', text: 'text-rose-700', dot: 'bg-rose-600 animate-pulse' },
  };

  const cur = map[priority] || map.MEDIUM;

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md text-xs font-semibold border ${cur.bg} ${cur.text}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${cur.dot}`}></span>
      {priority}
    </span>
  );
};

export const SLABadge: React.FC<{
  status: SLAStatus;
  displayText: string;
  isBreached: boolean;
  isAtRisk: boolean;
  isPaused: boolean;
}> = ({ status, displayText, isBreached, isAtRisk, isPaused }) => {
  if (isBreached) {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-rose-600 text-white shadow-xs">
        ⚠️ {displayText}
      </span>
    );
  }

  if (isAtRisk) {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-amber-500 text-white">
        ⏳ {displayText}
      </span>
    );
  }

  if (isPaused) {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-200 text-slate-700">
        ⏸️ {displayText}
      </span>
    );
  }

  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
      ⏱️ {displayText}
    </span>
  );
};
