import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Ticket as TicketIcon,
  Clock,
  AlertTriangle,
  CheckCircle,
  Users,
  Layers,
  TrendingUp,
  FileCheck,
  Calendar,
  Shield,
  ArrowRight,
} from 'lucide-react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import {
  StudentDashboard,
  StaffDashboard,
  ManagerDashboard,
  Ticket,
} from '../types';
import { StatusBadge, PriorityBadge, SLABadge } from '../components/Badges';

export const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [studentData, setStudentData] = useState<StudentDashboard | null>(null);
  const [staffData, setStaffData] = useState<StaffDashboard | null>(null);
  const [managerData, setManagerData] = useState<ManagerDashboard | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      if (user?.role === 'STUDENT') {
        const res = await api.get('/dashboard/student');
        setStudentData(res.data);
      } else if (user?.role === 'STAFF') {
        const res = await api.get('/dashboard/staff');
        setStaffData(res.data);
      } else {
        // Manager or Admin
        const res = await api.get('/dashboard/manager');
        setManagerData(res.data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user) {
      fetchDashboardData();
    }
  }, [user]);

  if (loading) {
    return <div className="p-8 text-center text-slate-400">Loading dashboard metrics...</div>;
  }

  // -------------------------------------------------------------
  // STUDENT DASHBOARD
  // -------------------------------------------------------------
  if (user?.role === 'STUDENT') {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Student Support Desk</h1>
          <p className="text-xs text-slate-500 mt-1">
            Track status, submit new support inquiries, and review resolved tickets.
          </p>
        </div>

        {/* 4 Primary Metric Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex items-center justify-between">
            <div>
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">My Open Tickets</span>
              <div className="text-2xl font-bold text-slate-900 mt-1">{studentData?.my_open_tickets || 0}</div>
            </div>
            <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center font-bold">
              <TicketIcon className="w-5 h-5" />
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex items-center justify-between">
            <div>
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">In Progress</span>
              <div className="text-2xl font-bold text-amber-600 mt-1">{studentData?.in_progress || 0}</div>
            </div>
            <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center font-bold">
              <Clock className="w-5 h-5" />
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex items-center justify-between">
            <div>
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Action Needed</span>
              <div className="text-2xl font-bold text-orange-600 mt-1">{studentData?.waiting_for_response || 0}</div>
            </div>
            <div className="w-10 h-10 rounded-xl bg-orange-50 text-orange-600 flex items-center justify-center font-bold">
              <AlertTriangle className="w-5 h-5" />
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex items-center justify-between">
            <div>
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Resolved</span>
              <div className="text-2xl font-bold text-emerald-600 mt-1">{studentData?.resolved || 0}</div>
            </div>
            <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold">
              <CheckCircle className="w-5 h-5" />
            </div>
          </div>
        </div>

        {/* Recent Tickets Table */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-bold text-slate-800 uppercase tracking-wider">My Recent Inquiries</h2>
            <button
              onClick={() => navigate('/tickets/new')}
              className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-xs"
            >
              + Create Inquiry
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-slate-200 text-slate-400 font-bold uppercase text-[10px]">
                  <th className="py-2.5 px-3">Ticket #</th>
                  <th className="py-2.5 px-3">Category</th>
                  <th className="py-2.5 px-3">Subject</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3">SLA Status</th>
                  <th className="py-2.5 px-3 text-right">View</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {studentData?.recent_tickets.map((t) => (
                  <tr
                    key={t.id}
                    onClick={() => navigate(`/tickets/${t.id}`)}
                    className="hover:bg-slate-50 cursor-pointer"
                  >
                    <td className="py-3 px-3 font-mono font-bold text-indigo-600">{t.ticket_number}</td>
                    <td className="py-3 px-3 font-medium text-slate-700">{t.category}</td>
                    <td className="py-3 px-3 max-w-sm truncate text-slate-800">{t.subject}</td>
                    <td className="py-3 px-3">
                      <StatusBadge status={t.status} />
                    </td>
                    <td className="py-3 px-3">
                      <SLABadge
                        status={t.sla.status}
                        displayText={t.sla.display_text}
                        isBreached={t.sla.is_breached}
                        isAtRisk={t.sla.is_at_risk}
                        isPaused={t.sla.is_paused}
                      />
                    </td>
                    <td className="py-3 px-3 text-right font-medium text-indigo-600">Details &rarr;</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  }

  // -------------------------------------------------------------
  // STAFF DASHBOARD
  // -------------------------------------------------------------
  if (user?.role === 'STAFF') {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Staff Operations Center</h1>
          <p className="text-xs text-slate-500 mt-1">
            Department: {user.department || 'General Administration'} &bull; Real-time SLA & Workload Tracking
          </p>
        </div>

        {/* 4 Staff Metrics */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex items-center justify-between">
            <div>
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Assigned to Me</span>
              <div className="text-2xl font-bold text-slate-900 mt-1">{staffData?.my_open_tickets || 0}</div>
            </div>
            <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold">
              <TicketIcon className="w-5 h-5" />
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex items-center justify-between">
            <div>
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Due Soon (&lt; 25%)</span>
              <div className="text-2xl font-bold text-amber-600 mt-1">{staffData?.due_soon || 0}</div>
            </div>
            <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center font-bold">
              <Clock className="w-5 h-5" />
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex items-center justify-between">
            <div>
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">SLA Breached</span>
              <div className="text-2xl font-bold text-rose-600 mt-1">{staffData?.sla_breached || 0}</div>
            </div>
            <div className="w-10 h-10 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center font-bold">
              <AlertTriangle className="w-5 h-5" />
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex items-center justify-between">
            <div>
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Waiting Student</span>
              <div className="text-2xl font-bold text-orange-600 mt-1">{staffData?.waiting_for_student || 0}</div>
            </div>
            <div className="w-10 h-10 rounded-xl bg-orange-50 text-orange-600 flex items-center justify-center font-bold">
              <Clock className="w-5 h-5" />
            </div>
          </div>
        </div>

        {/* 2-Column Section: Department Workload & Oldest Queue */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-5 bg-white rounded-xl border border-slate-200 shadow-xs p-6 space-y-4">
            <h2 className="text-xs font-bold text-slate-500 uppercase tracking-wider border-b border-slate-100 pb-2">
              Department Team Workload
            </h2>
            <div className="space-y-3">
              {staffData?.workload.map((w) => (
                <div key={w.staff_id} className="flex items-center justify-between text-xs p-2 bg-slate-50 rounded-lg">
                  <span className="font-semibold text-slate-800">{w.name}</span>
                  <div className="flex gap-2">
                    <span className="px-2 py-0.5 bg-indigo-50 text-indigo-700 rounded font-medium">
                      {w.active_tickets} active
                    </span>
                    {w.breached_tickets > 0 && (
                      <span className="px-2 py-0.5 bg-rose-100 text-rose-700 rounded font-bold">
                        {w.breached_tickets} breached
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="lg:col-span-7 bg-white rounded-xl border border-slate-200 shadow-xs p-6 space-y-4">
            <h2 className="text-xs font-bold text-slate-500 uppercase tracking-wider border-b border-slate-100 pb-2">
              Oldest Unresolved Tickets
            </h2>
            <div className="space-y-2">
              {staffData?.oldest_tickets.map((t) => (
                <div
                  key={t.id}
                  onClick={() => navigate(`/tickets/${t.id}`)}
                  className="p-3 border border-slate-200 rounded-lg flex items-center justify-between text-xs hover:bg-slate-50 cursor-pointer"
                >
                  <div className="space-y-0.5 truncate pr-3">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-indigo-600">{t.ticket_number}</span>
                      <PriorityBadge priority={t.priority} />
                    </div>
                    <div className="font-medium text-slate-800 truncate">{t.subject}</div>
                  </div>
                  <div className="text-right shrink-0">
                    <SLABadge
                      status={t.sla.status}
                      displayText={t.sla.display_text}
                      isBreached={t.sla.is_breached}
                      isAtRisk={t.sla.is_at_risk}
                      isPaused={t.sla.is_paused}
                    />
                    <span className="text-[10px] text-slate-400 block mt-1">Age: {t.ageing.age_display}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // -------------------------------------------------------------
  // MANAGER & ADMIN DASHBOARD
  // -------------------------------------------------------------
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Executive Management Overview</h1>
          <p className="text-xs text-slate-500 mt-1">
            Campus-wide institutional support health, SLA compliance & escalation bottlenecks.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold px-3 py-1 bg-indigo-50 text-indigo-700 rounded-md border border-indigo-200">
            Avg Resolution: {managerData?.avg_resolution_hours || 0} Hours
          </span>
        </div>
      </div>

      {/* 5 KPI Metric Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3.5">
        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">Total Open</span>
          <div className="text-2xl font-bold text-slate-900 mt-1">{managerData?.total_open || 0}</div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">Unassigned</span>
          <div className="text-2xl font-bold text-amber-600 mt-1">{managerData?.unassigned || 0}</div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">SLA At Risk</span>
          <div className="text-2xl font-bold text-orange-600 mt-1">{managerData?.sla_at_risk || 0}</div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">SLA Breached</span>
          <div className="text-2xl font-bold text-rose-600 mt-1">{managerData?.sla_breached || 0}</div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">Escalated</span>
          <div className="text-2xl font-bold text-purple-700 mt-1">{managerData?.escalated || 0}</div>
        </div>
      </div>

      {/* Analytical Breakdown Grids */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Categories Distribution */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-5 space-y-3">
          <h2 className="text-xs font-bold text-slate-500 uppercase tracking-wider border-b border-slate-100 pb-2">
            Tickets by Category
          </h2>
          <div className="space-y-2 text-xs">
            {managerData &&
              Object.entries(managerData.tickets_by_category).map(([cat, count]) => (
                <div key={cat} className="flex justify-between items-center py-1">
                  <span className="font-medium text-slate-700">{cat}</span>
                  <span className="font-bold text-slate-900 bg-slate-100 px-2 py-0.5 rounded">{count}</span>
                </div>
              ))}
          </div>
        </div>

        {/* Priority Distribution */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-5 space-y-3">
          <h2 className="text-xs font-bold text-slate-500 uppercase tracking-wider border-b border-slate-100 pb-2">
            Tickets by Priority
          </h2>
          <div className="space-y-2 text-xs">
            {managerData &&
              Object.entries(managerData.tickets_by_priority).map(([prio, count]) => (
                <div key={prio} className="flex justify-between items-center py-1">
                  <span className="font-medium text-slate-700">{prio}</span>
                  <span className="font-bold text-slate-900 bg-slate-100 px-2 py-0.5 rounded">{count}</span>
                </div>
              ))}
          </div>
        </div>

        {/* Ageing Distribution */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-5 space-y-3">
          <h2 className="text-xs font-bold text-slate-500 uppercase tracking-wider border-b border-slate-100 pb-2">
            Ageing Distribution
          </h2>
          <div className="space-y-2 text-xs">
            {managerData &&
              Object.entries(managerData.ageing_distribution).map(([bucket, count]) => (
                <div key={bucket} className="flex justify-between items-center py-1">
                  <span className="font-medium text-slate-700">{bucket}</span>
                  <span
                    className={`font-bold px-2 py-0.5 rounded ${
                      bucket === '14+ days' ? 'bg-rose-100 text-rose-700' : 'bg-slate-100 text-slate-900'
                    }`}
                  >
                    {count}
                  </span>
                </div>
              ))}
          </div>
        </div>
      </div>

      {/* Staff Workload Table & Oldest Unresolved Tickets */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-5 bg-white rounded-xl border border-slate-200 shadow-xs p-6 space-y-4">
          <h2 className="text-xs font-bold text-slate-500 uppercase tracking-wider border-b border-slate-100 pb-2">
            Staff Workload Allocation
          </h2>
          <div className="space-y-2.5">
            {managerData?.staff_workload.map((s) => (
              <div key={s.staff_id} className="p-2.5 bg-slate-50 rounded-lg flex items-center justify-between text-xs">
                <span className="font-semibold text-slate-800">{s.name}</span>
                <div className="flex gap-2">
                  <span className="px-2 py-0.5 bg-indigo-50 text-indigo-700 font-medium rounded">
                    {s.active_tickets} active
                  </span>
                  {s.breached_tickets > 0 && (
                    <span className="px-2 py-0.5 bg-rose-100 text-rose-700 font-bold rounded">
                      {s.breached_tickets} breached
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="lg:col-span-7 bg-white rounded-xl border border-slate-200 shadow-xs p-6 space-y-4">
          <h2 className="text-xs font-bold text-slate-500 uppercase tracking-wider border-b border-slate-100 pb-2">
            Oldest Unresolved Institution Tickets
          </h2>
          <div className="space-y-2">
            {managerData?.oldest_unresolved_tickets.map((t) => (
              <div
                key={t.id}
                onClick={() => navigate(`/tickets/${t.id}`)}
                className="p-3 border border-slate-200 rounded-lg flex items-center justify-between text-xs hover:bg-slate-50 cursor-pointer"
              >
                <div className="space-y-0.5 truncate pr-3">
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-indigo-600">{t.ticket_number}</span>
                    <PriorityBadge priority={t.priority} />
                    <span className="text-slate-500">({t.student_name})</span>
                  </div>
                  <div className="font-medium text-slate-800 truncate">{t.subject}</div>
                </div>
                <div className="text-right shrink-0">
                  <SLABadge
                    status={t.sla.status}
                    displayText={t.sla.display_text}
                    isBreached={t.sla.is_breached}
                    isAtRisk={t.sla.is_at_risk}
                    isPaused={t.sla.is_paused}
                  />
                  <span className="text-[10px] text-slate-400 block mt-1">Age: {t.ageing.age_display}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
