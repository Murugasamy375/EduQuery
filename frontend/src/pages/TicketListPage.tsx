import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Filter, Plus, Clock, ArrowUpDown, RefreshCw } from 'lucide-react';
import api from '../services/api';
import { Ticket, TicketStatus, Priority } from '../types';
import { StatusBadge, PriorityBadge, SLABadge } from '../components/Badges';
import { useAuth } from '../context/AuthContext';

export const TicketListPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters & Search
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [priorityFilter, setPriorityFilter] = useState<string>('ALL');
  const [categoryFilter, setCategoryFilter] = useState<string>('ALL');
  const [departmentFilter, setDepartmentFilter] = useState<string>('ALL');

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  const fetchTickets = async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (search) params.search = search;
      if (statusFilter !== 'ALL') params.status = statusFilter;
      if (priorityFilter !== 'ALL') params.priority = priorityFilter;
      if (categoryFilter !== 'ALL') params.category = categoryFilter;
      if (departmentFilter !== 'ALL') params.department = departmentFilter;

      const res = await api.get('/tickets', { params });
      setTickets(res.data);
      setCurrentPage(1);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTickets();
  }, [statusFilter, priorityFilter, categoryFilter, departmentFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchTickets();
  };

  // Filtered tickets pagination
  const totalPages = Math.ceil(tickets.length / itemsPerPage);
  const paginatedTickets = tickets.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Support Ticket Queue</h1>
          <p className="text-xs text-slate-500 mt-1">
            Displaying institutional requests across administrative and academic workflows.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchTickets}
            className="p-2 border border-slate-300 rounded-lg text-slate-600 hover:bg-slate-100 transition"
            title="Refresh Table"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          {user?.role === 'STUDENT' && (
            <button
              onClick={() => navigate('/tickets/new')}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-xs flex items-center gap-1.5 transition"
            >
              <Plus className="w-4 h-4" />
              New Ticket
            </button>
          )}
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs space-y-3">
        <form onSubmit={handleSearchSubmit} className="flex gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3.5 top-3 text-slate-400" />
            <input
              type="text"
              placeholder="Search by ticket #, student name, student ID, or subject..."
              className="w-full bg-slate-50 border border-slate-300 rounded-lg pl-9.5 pr-4 py-2 text-xs text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 bg-slate-800 hover:bg-slate-900 text-white text-xs font-semibold rounded-lg shadow-xs"
          >
            Search
          </button>
        </form>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 pt-2 border-t border-slate-100 text-xs">
          <div>
            <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">
              Status
            </label>
            <select
              className="w-full bg-slate-50 border border-slate-300 rounded-lg p-1.5 text-xs text-slate-800"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="ALL">All Statuses</option>
              <option value="NEW">NEW</option>
              <option value="ASSIGNED">ASSIGNED</option>
              <option value="IN_PROGRESS">IN PROGRESS</option>
              <option value="WAITING_FOR_STUDENT">WAITING STUDENT</option>
              <option value="RESOLVED">RESOLVED</option>
              <option value="CLOSED">CLOSED</option>
              <option value="REOPENED">REOPENED</option>
            </select>
          </div>

          <div>
            <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">
              Priority
            </label>
            <select
              className="w-full bg-slate-50 border border-slate-300 rounded-lg p-1.5 text-xs text-slate-800"
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
            >
              <option value="ALL">All Priorities</option>
              <option value="LOW">LOW</option>
              <option value="MEDIUM">MEDIUM</option>
              <option value="HIGH">HIGH</option>
              <option value="URGENT">URGENT</option>
            </select>
          </div>

          <div>
            <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">
              Category
            </label>
            <select
              className="w-full bg-slate-50 border border-slate-300 rounded-lg p-1.5 text-xs text-slate-800"
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
            >
              <option value="ALL">All Categories</option>
              <option value="Fees">Fees</option>
              <option value="Attendance">Attendance</option>
              <option value="ID Card">ID Card</option>
              <option value="Documents">Documents</option>
              <option value="Certificates">Certificates</option>
              <option value="General Administration">General Admin</option>
            </select>
          </div>

          <div>
            <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">
              Department
            </label>
            <select
              className="w-full bg-slate-50 border border-slate-300 rounded-lg p-1.5 text-xs text-slate-800"
              value={departmentFilter}
              onChange={(e) => setDepartmentFilter(e.target.value)}
            >
              <option value="ALL">All Departments</option>
              <option value="Finance">Finance</option>
              <option value="Academic Affairs">Academic Affairs</option>
              <option value="Registrar & Student Records">Registrar</option>
              <option value="Campus Administration">Administration</option>
            </select>
          </div>
        </div>
      </div>

      {/* Ticket Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50/75 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                <th className="py-3 px-4">Ticket #</th>
                <th className="py-3 px-4">Student</th>
                <th className="py-3 px-4">Category</th>
                <th className="py-3 px-4">Subject</th>
                <th className="py-3 px-4">Priority</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Assigned Staff</th>
                <th className="py-3 px-4">Age</th>
                <th className="py-3 px-4">SLA Time</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-xs">
              {loading ? (
                <tr>
                  <td colSpan={10} className="py-8 text-center text-slate-400">
                    Loading tickets...
                  </td>
                </tr>
              ) : paginatedTickets.length === 0 ? (
                <tr>
                  <td colSpan={10} className="py-8 text-center text-slate-500">
                    No tickets found matching current filters.
                  </td>
                </tr>
              ) : (
                paginatedTickets.map((t) => (
                  <tr
                    key={t.id}
                    onClick={() => navigate(`/tickets/${t.id}`)}
                    className="hover:bg-slate-50/80 transition cursor-pointer"
                  >
                    <td className="py-3.5 px-4 font-mono font-semibold text-indigo-600">
                      {t.ticket_number}
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="font-semibold text-slate-800">{t.student_name}</div>
                      <div className="text-[10px] text-slate-400 font-mono">ID #{t.student_id}</div>
                    </td>
                    <td className="py-3.5 px-4 text-slate-600 font-medium">
                      {t.category}
                    </td>
                    <td className="py-3.5 px-4 max-w-xs truncate font-medium text-slate-800">
                      {t.subject}
                    </td>
                    <td className="py-3.5 px-4">
                      <PriorityBadge priority={t.priority} />
                    </td>
                    <td className="py-3.5 px-4">
                      <StatusBadge status={t.status} />
                    </td>
                    <td className="py-3.5 px-4 text-slate-600">
                      {t.assigned_staff_name ? (
                        <span className="font-medium text-slate-800">{t.assigned_staff_name}</span>
                      ) : (
                        <span className="text-amber-600 italic font-medium">Unassigned</span>
                      )}
                    </td>
                    <td className="py-3.5 px-4 text-slate-500 font-mono">
                      {t.ageing.age_display}
                      <span className="block text-[10px] text-slate-400">{t.ageing.bucket}</span>
                    </td>
                    <td className="py-3.5 px-4">
                      <SLABadge
                        status={t.sla.status}
                        displayText={t.sla.display_text}
                        isBreached={t.sla.is_breached}
                        isAtRisk={t.sla.is_at_risk}
                        isPaused={t.sla.is_paused}
                      />
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <span className="text-indigo-600 hover:text-indigo-800 font-medium">
                        View &rarr;
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination controls */}
        {totalPages > 1 && (
          <div className="p-4 border-t border-slate-200 flex items-center justify-between text-xs text-slate-600">
            <div>
              Showing {(currentPage - 1) * itemsPerPage + 1} to{' '}
              {Math.min(currentPage * itemsPerPage, tickets.length)} of {tickets.length} tickets
            </div>
            <div className="flex gap-1.5">
              <button
                disabled={currentPage === 1}
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                className="px-3 py-1.5 border border-slate-300 rounded-md hover:bg-slate-100 disabled:opacity-40"
              >
                Previous
              </button>
              <div className="px-3 py-1.5 font-semibold text-slate-800">
                Page {currentPage} of {totalPages}
              </div>
              <button
                disabled={currentPage === totalPages}
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                className="px-3 py-1.5 border border-slate-300 rounded-md hover:bg-slate-100 disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
