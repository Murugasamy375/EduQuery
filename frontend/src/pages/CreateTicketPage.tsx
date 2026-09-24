import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, UploadCloud, Send, AlertCircle, FileText, CheckCircle2 } from 'lucide-react';
import api from '../services/api';
import { Priority } from '../types';

export const CreateTicketPage: React.FC = () => {
  const navigate = useNavigate();
  const [subject, setSubject] = useState('');
  const [category, setCategory] = useState('Fees');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState<Priority>('MEDIUM');
  const [department, setDepartment] = useState('Finance');
  const [isAiLoading, setIsAiLoading] = useState(false);
  const [aiSuggestion, setAiSuggestion] = useState<any>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const categories = [
    'Fees',
    'Attendance',
    'ID Card',
    'Documents',
    'Certificates',
    'General Administration',
  ];

  const departments = [
    'Finance',
    'Academic Affairs',
    'Registrar & Student Records',
    'Campus Administration',
    'Student Support Services',
  ];

  // AI Auto-Classification Handler
  const handleAiClassify = async () => {
    if (!subject.trim() && !description.trim()) {
      setError('Please provide at least a subject or description for AI classification.');
      return;
    }
    setError('');
    setIsAiLoading(true);
    try {
      const res = await api.post('/ai/classify-ticket', {
        subject: subject || 'Student Request',
        description: description || subject,
      });
      setAiSuggestion(res.data);
      if (res.data.category) setCategory(res.data.category);
      if (res.data.priority) setPriority(res.data.priority);
      if (res.data.department) setDepartment(res.data.department);
    } catch (err: any) {
      setError('AI classification service unavailable. You may manually select options.');
    } finally {
      setIsAiLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      const res = await api.post('/tickets', {
        subject,
        category,
        description,
        priority,
        department,
        attachments: [
          {
            id: 'att-user-1',
            filename: 'supporting_document.pdf',
            file_type: 'application/pdf',
            size_bytes: 145000,
          },
        ],
      });
      navigate(`/tickets/${res.data.id}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to submit ticket');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Create Support Ticket</h1>
          <p className="text-xs text-slate-500 mt-1">
            Submit your administrative or academic inquiry to college services.
          </p>
        </div>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          {error}
        </div>
      )}

      {/* Form Container */}
      <form onSubmit={handleSubmit} className="bg-white rounded-xl shadow-xs border border-slate-200 p-6 md:p-8 space-y-6">
        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
            Subject *
          </label>
          <input
            type="text"
            required
            placeholder="e.g. Tuition fee receipt not generated after transaction"
            className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3.5 py-2.5 text-sm text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
            Detailed Description *
          </label>
          <textarea
            required
            rows={5}
            placeholder="Describe the issue, include transaction references, roll numbers, or specific dates..."
            className="w-full bg-slate-50 border border-slate-300 rounded-lg p-3 text-sm text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </div>

        {/* AI Assist Box */}
        <div className="p-4 rounded-xl bg-gradient-to-r from-indigo-50/70 via-purple-50/70 to-pink-50/70 border border-indigo-100 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-1.5 text-xs font-bold text-indigo-900">
              <Sparkles className="w-4 h-4 text-indigo-600" />
              Smart Ticket Assistant (Optional AI)
            </div>
            <p className="text-xs text-indigo-700/80">
              Auto-detect category, department routing, and priority based on your description.
            </p>
          </div>
          <button
            type="button"
            onClick={handleAiClassify}
            disabled={isAiLoading || (!subject && !description)}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-xs flex items-center gap-1.5 shrink-0 transition disabled:opacity-50"
          >
            {isAiLoading ? 'Analyzing...' : 'Auto-Classify with AI'}
          </button>
        </div>

        {aiSuggestion && (
          <div className="p-3.5 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-900 flex items-start gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold">AI Suggested:</span> {aiSuggestion.category} &bull; {aiSuggestion.priority} &bull; {aiSuggestion.department}
              <div className="text-emerald-700 mt-0.5">{aiSuggestion.summary}</div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
              Category
            </label>
            <select
              className="w-full bg-slate-50 border border-slate-300 rounded-lg p-2.5 text-sm text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            >
              {categories.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
              Assigned Department
            </label>
            <select
              className="w-full bg-slate-50 border border-slate-300 rounded-lg p-2.5 text-sm text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              value={department}
              onChange={(e) => setDepartment(e.target.value)}
            >
              {departments.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
              Priority
            </label>
            <select
              className="w-full bg-slate-50 border border-slate-300 rounded-lg p-2.5 text-sm text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              value={priority}
              onChange={(e) => setPriority(e.target.value as Priority)}
            >
              <option value="LOW">LOW (72h SLA)</option>
              <option value="MEDIUM">MEDIUM (48h SLA)</option>
              <option value="HIGH">HIGH (24h SLA)</option>
              <option value="URGENT">URGENT (8h SLA)</option>
            </select>
          </div>
        </div>

        {/* Attachment Upload Simulation */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
            Supporting Document (PDF, PNG, JPG)
          </label>
          <div className="border-2 border-dashed border-slate-300 rounded-xl p-4 text-center hover:border-indigo-400 bg-slate-50/50 cursor-pointer">
            <UploadCloud className="w-6 h-6 mx-auto text-slate-400 mb-1" />
            <span className="text-xs text-slate-600 font-medium">Click to upload supporting receipt or affidavit</span>
            <p className="text-[11px] text-slate-400 mt-0.5">Maximum file size: 10MB</p>
          </div>
        </div>

        <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
          <button
            type="button"
            onClick={() => navigate('/tickets')}
            className="px-4 py-2 border border-slate-300 text-slate-700 rounded-lg text-sm font-medium hover:bg-slate-50 transition"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={submitting}
            className="px-6 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-semibold shadow-xs flex items-center gap-2 transition disabled:opacity-50"
          >
            <Send className="w-4 h-4" />
            {submitting ? 'Submitting...' : 'Submit Request'}
          </button>
        </div>
      </form>
    </div>
  );
};
