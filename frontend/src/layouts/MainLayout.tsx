import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  LayoutDashboard,
  Ticket as TicketIcon,
  PlusCircle,
  Users,
  LogOut,
  GraduationCap,
  Shield,
  Layers,
  ChevronDown,
} from 'lucide-react';
import { NotificationDropdown } from '../components/NotificationDropdown';

export const MainLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, logout, switchDemoUser } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const demoAccounts = [
    { label: 'Admin (All Depts)', email: 'admin@institution.edu' },
    { label: 'Manager (Finance)', email: 'manager.finance@institution.edu' },
    { label: 'Manager (Records)', email: 'manager.records@institution.edu' },
    { label: 'Staff (Finance 1)', email: 'staff.finance1@institution.edu' },
    { label: 'Staff (Records 1)', email: 'staff.records1@institution.edu' },
    { label: 'Student (Aarav Sharma)', email: 'aarav.sharma@student.institution.edu' },
    { label: 'Student (Diya Patel)', email: 'diya.patel@student.institution.edu' },
  ];

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden font-sans text-slate-800">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col shrink-0 text-slate-300">
        {/* Brand */}
        <div className="h-16 flex items-center px-6 gap-3 border-b border-slate-800/80">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-500 to-violet-500 flex items-center justify-center text-white shadow-md shadow-indigo-500/20">
            <GraduationCap className="w-5 h-5" />
          </div>
          <div>
            <div className="font-bold text-white text-base tracking-tight leading-none">EduSupport</div>
            <div className="text-[10px] text-slate-400 font-medium tracking-wider uppercase mt-1">
              Ticket System
            </div>
          </div>
        </div>

        {/* Navigation Links */}
        <div className="flex-1 py-6 px-3 space-y-1.5 overflow-y-auto">
          <div className="px-3 text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
            Main Menu
          </div>

          <NavLink
            to="/dashboard"
            className={({ isActive }) =>
              `flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition ${
                isActive
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`
            }
          >
            <LayoutDashboard className="w-4 h-4" />
            Dashboard
          </NavLink>

          <NavLink
            to="/tickets"
            className={({ isActive }) =>
              `flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition ${
                isActive
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`
            }
          >
            <TicketIcon className="w-4 h-4" />
            Ticket Queue
          </NavLink>

          {user?.role === 'STUDENT' && (
            <NavLink
              to="/tickets/new"
              className={({ isActive }) =>
                `flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition ${
                  isActive
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`
              }
            >
              <PlusCircle className="w-4 h-4" />
              New Ticket
            </NavLink>
          )}

          {/* Quick Demo Switcher Section in sidebar */}
          <div className="pt-6">
            <div className="px-3 text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <Shield className="w-3.5 h-3.5 text-indigo-400" />
              Switch Demo Role
            </div>
            <div className="space-y-1 px-1">
              <select
                className="w-full text-xs bg-slate-800 border border-slate-700 text-slate-200 rounded-lg p-2 focus:ring-1 focus:ring-indigo-500 focus:outline-none"
                value={user?.email || ''}
                onChange={(e) => switchDemoUser(e.target.value)}
              >
                {demoAccounts.map((acc) => (
                  <option key={acc.email} value={acc.email}>
                    {acc.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* User Footer Profile */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/40">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-sm text-indigo-400">
              {user?.name?.charAt(0) || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold text-white truncate">{user?.name}</p>
              <span className="inline-block text-[10px] px-1.5 py-0.5 rounded font-bold uppercase tracking-wider bg-slate-800 text-indigo-300">
                {user?.role}
              </span>
            </div>
            <button
              onClick={handleLogout}
              className="p-1.5 text-slate-400 hover:text-rose-400 rounded-md hover:bg-slate-800 transition"
              title="Sign Out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Navbar */}
        <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-8 shrink-0">
          <div className="flex items-center gap-3">
            <span className="text-xs font-semibold px-2.5 py-1 bg-slate-100 text-slate-600 rounded-md border border-slate-200">
              {user?.department ? user.department : 'Campus-Wide Helpdesk'}
            </span>
            {user?.student_id_card && (
              <span className="text-xs font-mono bg-blue-50 text-blue-700 px-2.5 py-1 rounded-md border border-blue-200">
                ID: {user.student_id_card}
              </span>
            )}
          </div>

          <div className="flex items-center gap-4">
            <NotificationDropdown />
            <div className="h-4 w-px bg-slate-200"></div>
            <div className="text-right">
              <div className="text-xs font-bold text-slate-800">{user?.name}</div>
              <div className="text-[11px] text-slate-400">{user?.email}</div>
            </div>
          </div>
        </header>

        {/* Dynamic Page Outlet */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8 bg-slate-50/60">
          {children}
        </main>
      </div>
    </div>
  );
};
