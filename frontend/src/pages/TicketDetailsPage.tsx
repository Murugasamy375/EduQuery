import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Clock,
  User,
  Shield,
  Send,
  Lock,
  ArrowLeft,
  CheckCircle,
  RotateCcw,
  AlertTriangle,
  FileText,
  MessageSquare,
  Building,
  Info,
} from 'lucide-react';
import api from '../services/api';
import { Ticket, Activity, User as UserType } from '../types';
import { StatusBadge, PriorityBadge, SLABadge } from '../components/Badges';
import { useAuth } from '../context/AuthContext';

export const TicketDetailsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const navigate = useNavigate();

  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [staffList, setStaffList] = useState<UserType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Comment & Note state
  const [commentText, setCommentText] = useState('');
  const [internalNoteText, setInternalNoteText] = useState('');
  const [activeTab, setActiveTab] = useState<'comment' | 'internal'>('comment');
  const [actionLoading, setActionLoading] = useState(false);

  // Modals / Actions
  const [showResolveModal, setShowResolveModal] = useState(false);
  const [resolveSummary, setResolveSummary] = useState('');

  const [showReopenModal, setShowReopenModal] = useState(false);
  const [reopenReason, setReopenReason] = useState('');

  const [showEscalateModal, setShowEscalateModal] = useState(false);
  const [escalateReason, setEscalateReason] = useState('SLA_BREACH');
  const [escalateNotes, setEscalateNotes] = useState('');
  const [escalateTargetStaff, setEscalateTargetStaff] = useState<number | undefined>();

  // Status Modal (e.g. Waiting for student)
  const [showStatusModal, setShowStatusModal] = useState(false);
  const [targetStatus, setTargetStatus] = useState<string>('IN_PROGRESS');
  const [pendingReason, setPendingReason] = useState('WAITING_FOR_STUDENT');
  const [requestedAction, setRequestedAction] = useState('');

  const fetchTicketData = async () => {
    try {
      const [tRes, aRes] = await Promise.all([
        api.get(`/tickets/${id}`),
        api.get(`/tickets/${id}/activities`),
      ]);
      setTicket(tRes.data);
      setActivities(aRes.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load ticket details.');
    } finally {
      setLoading(false);
    }
  };

  const fetchStaff = async () => {
    try {
      const res = await api.get('/auth/staff');
      setStaffList(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchTicketData();
    if (user?.role !== 'STUDENT') {
      fetchStaff();
    }
  }, [id, user]);

  const handleAddComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!commentText.trim()) return;
    setActionLoading(true);
    try {
      await api.post(`/tickets/${id}/comments`, { comment: commentText });
      setCommentText('');
      fetchTicketData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to post reply.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleAddInternalNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!internalNoteText.trim()) return;
    setActionLoading(true);
    try {
      await api.post(`/tickets/${id}/internal-note`, { note: internalNoteText });
      setInternalNoteText('');
      fetchTicketData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to post note.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleAssign = async (staffId: number) => {
    try {
      await api.post(`/tickets/${id}/assign`, { staff_id: staffId });
      fetchTicketData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Assignment failed.');
    }
  };

  const handleStatusChangeSubmit = async () => {
    try {
      await api.post(`/tickets/${id}/status`, {
        status: targetStatus,
        pending_reason: targetStatus === 'WAITING_FOR_STUDENT' ? pendingReason : undefined,
        requested_action: targetStatus === 'WAITING_FOR_STUDENT' ? requestedAction : undefined,
      });
      setShowStatusModal(false);
      fetchTicketData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Status transition rejected.');
    }
  };

  const handleResolveSubmit = async () => {
    try {
      await api.post(`/tickets/${id}/resolve`, { resolution_summary: resolveSummary });
      setShowResolveModal(false);
      fetchTicketData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Resolution failed.');
    }
  };

  const handleReopenSubmit = async () => {
    try {
      await api.post(`/tickets/${id}/reopen`, { reason: reopenReason });
      setShowReopenModal(false);
      fetchTicketData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to reopen ticket.');
    }
  };

  const handleEscalateSubmit = async () => {
    try {
      await api.post(`/tickets/${id}/escalate`, {
        reason: escalateReason,
        target_staff_id: escalateTargetStaff || undefined,
        notes: escalateNotes,
      });
      setShowEscalateModal(false);
      fetchTicketData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Escalation failed.');
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-slate-400">Loading ticket...</div>;
  }

  if (error || !ticket) {
    return (
      <div className="max-w-xl mx-auto p-6 bg-white rounded-xl border border-rose-200 text-center space-y-3">
        <AlertTriangle className="w-8 h-8 text-rose-500 mx-auto" />
        <h2 className="text-base font-bold text-slate-800">Access Restricted</h2>
        <p className="text-xs text-slate-500">{error || 'Ticket not found.'}</p>
        <button
          onClick={() => navigate('/tickets')}
          className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-xs font-semibold"
        >
          Return to Queue
        </button>
      </div>
    );
  }

  const isStaffOrAbove = user?.role === 'STAFF' || user?.role === 'MANAGER' || user?.role === 'ADMIN';
  const isManagerOrAdmin = user?.role === 'MANAGER' || user?.role === 'ADMIN';

  return (
    <div className="space-y-6">
      {/* Top back navigation & quick summary */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pb-4 border-b border-slate-200">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/tickets')}
            className="p-2 border border-slate-300 rounded-lg hover:bg-slate-100 text-slate-600 transition"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-base font-bold text-indigo-600">{ticket.ticket_number}</span>
              <StatusBadge status={ticket.status} />
              <PriorityBadge priority={ticket.priority} />
              {ticket.is_escalated && (
                <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-rose-100 text-rose-700 border border-rose-200 flex items-center gap-1">
                  🚨 ESCALATED ({ticket.escalation_count}x)
                </span>
              )}
            </div>
            <h1 className="text-lg font-bold text-slate-900 mt-1">{ticket.subject}</h1>
          </div>
        </div>

        {/* Action Buttons Header */}
        <div className="flex flex-wrap items-center gap-2">
          {ticket.status === 'RESOLVED' && (
            <button
              onClick={() => setShowReopenModal(true)}
              className="px-3.5 py-1.5 bg-rose-50 border border-rose-300 text-rose-700 hover:bg-rose-100 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition"
            >
              <RotateCcw className="w-3.5 h-3.5" /> Reopen Ticket
            </button>
          )}

          {isStaffOrAbove && ticket.status !== 'CLOSED' && ticket.status !== 'RESOLVED' && (
            <>
              <button
                onClick={() => {
                  setTargetStatus(ticket.status === 'WAITING_FOR_STUDENT' ? 'IN_PROGRESS' : 'WAITING_FOR_STUDENT');
                  setShowStatusModal(true);
                }}
                className="px-3 py-1.5 border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-semibold transition"
              >
                Change Status
              </button>

              <button
                onClick={() => setShowResolveModal(true)}
                className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-xs transition"
              >
                <CheckCircle className="w-3.5 h-3.5" /> Resolve Ticket
              </button>

              <button
                onClick={() => setShowEscalateModal(true)}
                className="px-3 py-1.5 bg-amber-500 hover:bg-amber-600 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-xs transition"
              >
                <AlertTriangle className="w-3.5 h-3.5" /> Escalate
              </button>
            </>
          )}
        </div>
      </div>

      {/* 3-Column Professional Layout: Left (Info) | Center (Timeline) | Right (SLA/State) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Ticket Info (4 cols) */}
        <div className="lg:col-span-3 space-y-4">
          <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-5 space-y-4">
            <h2 className="text-xs font-bold text-slate-500 uppercase tracking-wider border-b border-slate-100 pb-2">
              Ticket Details
            </h2>

            <div>
              <span className="text-[11px] text-slate-400 block font-medium">Category</span>
              <span className="text-xs font-semibold text-slate-800">{ticket.category}</span>
            </div>

            <div>
              <span className="text-[11px] text-slate-400 block font-medium">Department</span>
              <span className="text-xs font-semibold text-slate-800 flex items-center gap-1 mt-0.5">
                <Building className="w-3.5 h-3.5 text-slate-400" />
                {ticket.department}
              </span>
            </div>

            <div>
              <span className="text-[11px] text-slate-400 block font-medium">Submitted By</span>
              <span className="text-xs font-semibold text-slate-800">{ticket.student_name}</span>
              <span className="text-[11px] text-slate-500 block">{ticket.student_email}</span>
            </div>

            <div>
              <span className="text-[11px] text-slate-400 block font-medium">Description</span>
              <p className="text-xs text-slate-700 leading-relaxed mt-1 bg-slate-50 p-3 rounded-lg border border-slate-200 whitespace-pre-wrap">
                {ticket.description}
              </p>
            </div>

            {ticket.pending_details && (
              <div className="p-3 bg-amber-50/70 border border-amber-200 rounded-lg text-xs space-y-1">
                <div className="font-bold text-amber-800 flex items-center gap-1">
                  <Info className="w-3.5 h-3.5" /> Pending Action Required
                </div>
                <div className="text-amber-900 font-medium">
                  {ticket.pending_details.reason}
                </div>
                <div className="text-amber-800 text-[11px] italic">
                  "{ticket.pending_details.requested_action}"
                </div>
                <div className="text-[10px] text-amber-600 mt-1">
                  Requested by: {ticket.pending_details.requested_by}
                </div>
              </div>
            )}

            {ticket.resolution_summary && (
              <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs space-y-1">
                <div className="font-bold text-emerald-800 flex items-center gap-1">
                  <CheckCircle className="w-3.5 h-3.5" /> Resolution Summary
                </div>
                <div className="text-emerald-900 text-xs">{ticket.resolution_summary}</div>
              </div>
            )}

            {ticket.attachments && ticket.attachments.length > 0 && (
              <div>
                <span className="text-[11px] text-slate-400 block font-medium mb-1.5">
                  Supporting Documents ({ticket.attachments.length})
                </span>
                <div className="space-y-1.5">
                  {ticket.attachments.map((att) => (
                    <div
                      key={att.id}
                      className="p-2 border border-slate-200 rounded-lg flex items-center justify-between text-xs bg-slate-50"
                    >
                      <div className="flex items-center gap-2 truncate">
                        <FileText className="w-4 h-4 text-indigo-600 shrink-0" />
                        <span className="truncate font-medium text-slate-800">{att.filename}</span>
                      </div>
                      <span className="text-[10px] text-slate-400 font-mono">
                        {Math.round(att.size_bytes / 1024)} KB
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Center Column: Activity Timeline & Commenting (6 cols) */}
        <div className="lg:col-span-6 space-y-4">
          <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-6 space-y-6">
            <h2 className="text-xs font-bold text-slate-500 uppercase tracking-wider border-b border-slate-100 pb-2">
              Activity History & Timeline
            </h2>

            {/* Timeline Stream */}
            <div className="space-y-4 relative before:absolute before:inset-0 before:left-3 before:w-0.5 before:bg-slate-200">
              {activities.map((act) => {
                const isInternal = act.is_internal;
                return (
                  <div key={act.id} className="relative flex items-start gap-3 pl-1 text-xs">
                    <div
                      className={`w-5 h-5 rounded-full flex items-center justify-center shrink-0 z-10 ${
                        isInternal
                          ? 'bg-amber-100 text-amber-700 border border-amber-300'
                          : 'bg-indigo-100 text-indigo-700 border border-indigo-300'
                      }`}
                    >
                      {isInternal ? <Lock className="w-2.5 h-2.5" /> : <MessageSquare className="w-2.5 h-2.5" />}
                    </div>

                    <div
                      className={`flex-1 rounded-xl p-3 border ${
                        isInternal
                          ? 'bg-amber-50/60 border-amber-200 text-amber-950'
                          : 'bg-slate-50/70 border-slate-200 text-slate-800'
                      }`}
                    >
                      <div className="flex justify-between items-center mb-1">
                        <div className="flex items-center gap-1.5 font-semibold">
                          <span>{act.actor_name}</span>
                          <span className="text-[10px] uppercase font-bold text-slate-400">
                            ({act.actor_role})
                          </span>
                          {isInternal && (
                            <span className="text-[9px] bg-amber-200 text-amber-800 px-1.5 py-0.2 rounded font-bold uppercase">
                              Internal Note
                            </span>
                          )}
                        </div>
                        <span className="text-[10px] text-slate-400 font-mono">
                          {new Date(act.created_at).toLocaleString([], {
                            month: 'short',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </span>
                      </div>
                      <p className="leading-relaxed whitespace-pre-wrap">{act.description}</p>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Response Section */}
            {ticket.status !== 'CLOSED' ? (
              <div className="pt-4 border-t border-slate-100">
                {isStaffOrAbove && (
                  <div className="flex gap-2 mb-3">
                    <button
                      type="button"
                      onClick={() => setActiveTab('comment')}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                        activeTab === 'comment'
                          ? 'bg-indigo-600 text-white'
                          : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                      }`}
                    >
                      Public Reply (Student Visible)
                    </button>
                    <button
                      type="button"
                      onClick={() => setActiveTab('internal')}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1 transition ${
                        activeTab === 'internal'
                          ? 'bg-amber-600 text-white'
                          : 'bg-amber-50 text-amber-800 border border-amber-200 hover:bg-amber-100'
                      }`}
                    >
                      <Lock className="w-3 h-3" /> Internal Staff Note
                    </button>
                  </div>
                )}

                {activeTab === 'comment' ? (
                  <form onSubmit={handleAddComment} className="space-y-2">
                    <textarea
                      rows={3}
                      placeholder={
                        user?.role === 'STUDENT'
                          ? 'Type your reply here to update staff...'
                          : 'Type a message to the student...'
                      }
                      className="w-full bg-slate-50 border border-slate-300 rounded-lg p-2.5 text-xs text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      value={commentText}
                      onChange={(e) => setCommentText(e.target.value)}
                    />
                    <div className="flex justify-between items-center">
                      <span className="text-[10px] text-slate-400">
                        {user?.role === 'STUDENT' && ticket.status === 'WAITING_FOR_STUDENT'
                          ? '✨ Replying will automatically move ticket to IN_PROGRESS.'
                          : ''}
                      </span>
                      <button
                        type="submit"
                        disabled={actionLoading || !commentText.trim()}
                        className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-lg flex items-center gap-1.5 shadow-xs transition disabled:opacity-50"
                      >
                        <Send className="w-3.5 h-3.5" /> Send Reply
                      </button>
                    </div>
                  </form>
                ) : (
                  <form onSubmit={handleAddInternalNote} className="space-y-2">
                    <textarea
                      rows={3}
                      placeholder="Add an internal observation or clearance record (Invisible to student)..."
                      className="w-full bg-amber-50/50 border border-amber-300 rounded-lg p-2.5 text-xs text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-amber-500"
                      value={internalNoteText}
                      onChange={(e) => setInternalNoteText(e.target.value)}
                    />
                    <div className="flex justify-end">
                      <button
                        type="submit"
                        disabled={actionLoading || !internalNoteText.trim()}
                        className="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white text-xs font-semibold rounded-lg flex items-center gap-1.5 shadow-xs transition disabled:opacity-50"
                      >
                        <Lock className="w-3.5 h-3.5" /> Save Staff Note
                      </button>
                    </div>
                  </form>
                )}
              </div>
            ) : (
              <div className="p-3 text-center text-xs text-slate-500 bg-slate-50 border border-slate-200 rounded-lg">
                This ticket is permanently closed. Replies are disabled.
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Status, SLA Countdown & Ownership (3 cols) */}
        <div className="lg:col-span-3 space-y-4">
          {/* SLA Tracking Card */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-5 space-y-4">
            <h2 className="text-xs font-bold text-slate-500 uppercase tracking-wider border-b border-slate-100 pb-2">
              SLA & Ageing Monitor
            </h2>

            <div>
              <span className="text-[11px] text-slate-400 block font-medium">SLA Countdown</span>
              <div className="mt-1">
                <SLABadge
                  status={ticket.sla.status}
                  displayText={ticket.sla.display_text}
                  isBreached={ticket.sla.is_breached}
                  isAtRisk={ticket.sla.is_at_risk}
                  isPaused={ticket.sla.is_paused}
                />
              </div>
              <span className="text-[10px] text-slate-400 block mt-1">
                Due by: {new Date(ticket.sla_due_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}
              </span>
            </div>

            <div className="pt-2 border-t border-slate-100">
              <span className="text-[11px] text-slate-400 block font-medium">Ticket Age</span>
              <div className="text-sm font-semibold text-slate-800 mt-0.5">{ticket.ageing.age_display}</div>
              <span className="text-[10px] text-slate-500">Bucket: {ticket.ageing.bucket}</span>
            </div>

            <div className="pt-2 border-t border-slate-100">
              <span className="text-[11px] text-slate-400 block font-medium">Created On</span>
              <span className="text-xs text-slate-700">
                {new Date(ticket.created_at).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })}
              </span>
            </div>
          </div>

          {/* Ownership & Assignment Card */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-5 space-y-4">
            <h2 className="text-xs font-bold text-slate-500 uppercase tracking-wider border-b border-slate-100 pb-2">
              Ownership & Staff
            </h2>

            <div>
              <span className="text-[11px] text-slate-400 block font-medium">Currently Assigned To</span>
              <span className="text-xs font-semibold text-slate-800">
                {ticket.assigned_staff_name || 'Unassigned'}
              </span>
            </div>

            {/* Assignment Dropdown for Managers/Admin/Staff */}
            {isStaffOrAbove && (
              <div className="pt-2 border-t border-slate-100">
                <label className="block text-[11px] text-slate-400 font-medium mb-1">
                  Reassign / Assign Staff
                </label>
                <select
                  className="w-full bg-slate-50 border border-slate-300 rounded-lg p-1.5 text-xs text-slate-800"
                  value={ticket.assigned_staff_id || ''}
                  onChange={(e) => handleAssign(Number(e.target.value))}
                >
                  <option value="">Select Staff Member...</option>
                  {staffList.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name} ({s.department || s.role})
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Resolve Modal */}
      {showResolveModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 space-y-4">
            <h3 className="text-base font-bold text-slate-900">Resolve Ticket</h3>
            <p className="text-xs text-slate-500">
              Provide a clear summary of how this support inquiry was investigated and resolved.
            </p>
            <textarea
              rows={4}
              required
              className="w-full border border-slate-300 rounded-lg p-2.5 text-xs text-slate-900"
              placeholder="e.g. Bank wire transaction verified and credited to student tuition account."
              value={resolveSummary}
              onChange={(e) => setResolveSummary(e.target.value)}
            />
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowResolveModal(false)}
                className="px-3.5 py-1.5 border border-slate-300 text-slate-700 rounded-lg text-xs"
              >
                Cancel
              </button>
              <button
                onClick={handleResolveSubmit}
                disabled={!resolveSummary.trim()}
                className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold disabled:opacity-50"
              >
                Confirm Resolution
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Reopen Modal */}
      {showReopenModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 space-y-4">
            <h3 className="text-base font-bold text-slate-900">Reopen Ticket</h3>
            <p className="text-xs text-slate-500">
              Please specify the reason why this issue remains unresolved or requires further action.
            </p>
            <textarea
              rows={3}
              required
              className="w-full border border-slate-300 rounded-lg p-2.5 text-xs text-slate-900"
              placeholder="e.g. The replacement card is still not opening the hostel turnstile."
              value={reopenReason}
              onChange={(e) => setReopenReason(e.target.value)}
            />
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowReopenModal(false)}
                className="px-3.5 py-1.5 border border-slate-300 text-slate-700 rounded-lg text-xs"
              >
                Cancel
              </button>
              <button
                onClick={handleReopenSubmit}
                disabled={!reopenReason.trim()}
                className="px-4 py-1.5 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-xs font-semibold disabled:opacity-50"
              >
                Confirm Reopen
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Escalate Modal */}
      {showEscalateModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 space-y-4">
            <h3 className="text-base font-bold text-slate-900">Escalate Ticket to Management</h3>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Escalation Trigger</label>
              <select
                className="w-full border border-slate-300 rounded-lg p-2 text-xs"
                value={escalateReason}
                onChange={(e) => setEscalateReason(e.target.value)}
              >
                <option value="SLA_BREACH">SLA Breach / Response Delay</option>
                <option value="URGENT_SLA_APPROACHING">Urgent SLA Approaching Limit</option>
                <option value="SPECIAL_APPROVAL_NEEDED">Special Department Head Approval Needed</option>
                <option value="REPEATEDLY_REOPENED">Repeatedly Reopened Issue</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Escalate To Specific Staff/Manager (Optional)</label>
              <select
                className="w-full border border-slate-300 rounded-lg p-2 text-xs"
                value={escalateTargetStaff || ''}
                onChange={(e) => setEscalateTargetStaff(Number(e.target.value) || undefined)}
              >
                <option value="">Auto-Route to Department Head</option>
                {staffList.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name} ({s.role})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Escalation Note</label>
              <textarea
                rows={2}
                className="w-full border border-slate-300 rounded-lg p-2 text-xs"
                placeholder="Reasoning for supervisor escalation..."
                value={escalateNotes}
                onChange={(e) => setEscalateNotes(e.target.value)}
              />
            </div>

            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowEscalateModal(false)}
                className="px-3.5 py-1.5 border border-slate-300 text-slate-700 rounded-lg text-xs"
              >
                Cancel
              </button>
              <button
                onClick={handleEscalateSubmit}
                className="px-4 py-1.5 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-xs font-semibold"
              >
                Submit Escalation
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Change Status Modal (e.g. Waiting for student) */}
      {showStatusModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 space-y-4">
            <h3 className="text-base font-bold text-slate-900">Update Ticket Status</h3>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Target Status</label>
              <select
                className="w-full border border-slate-300 rounded-lg p-2 text-xs"
                value={targetStatus}
                onChange={(e) => setTargetStatus(e.target.value)}
              >
                <option value="IN_PROGRESS">IN_PROGRESS</option>
                <option value="WAITING_FOR_STUDENT">WAITING_FOR_STUDENT (Pauses SLA)</option>
                <option value="CLOSED">CLOSED</option>
              </select>
            </div>

            {targetStatus === 'WAITING_FOR_STUDENT' && (
              <>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Pending Reason</label>
                  <select
                    className="w-full border border-slate-300 rounded-lg p-2 text-xs"
                    value={pendingReason}
                    onChange={(e) => setPendingReason(e.target.value)}
                  >
                    <option value="WAITING_FOR_STUDENT">Awaiting Student Response</option>
                    <option value="WAITING_FOR_DOCUMENT">Awaiting Additional Document</option>
                    <option value="WAITING_FOR_DEPARTMENT">Awaiting External Department</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Requested Action *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Please provide your bank transaction reference ID"
                    className="w-full border border-slate-300 rounded-lg p-2 text-xs"
                    value={requestedAction}
                    onChange={(e) => setRequestedAction(e.target.value)}
                  />
                </div>
              </>
            )}

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setShowStatusModal(false)}
                className="px-3.5 py-1.5 border border-slate-300 text-slate-700 rounded-lg text-xs"
              >
                Cancel
              </button>
              <button
                onClick={handleStatusChangeSubmit}
                className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold"
              >
                Update Status
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
