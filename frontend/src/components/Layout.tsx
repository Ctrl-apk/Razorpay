import { Outlet, NavLink } from "react-router-dom";
import { Activity, LayoutDashboard, FlaskConical, GitCompare } from "lucide-react";

const navBase   = "flex items-center gap-2 px-3 py-2 rounded-lg text-slate-400 hover:text-white hover:bg-[#1e2a45] transition-colors text-sm font-medium";
const navActive = "flex items-center gap-2 px-3 py-2 rounded-lg text-white bg-[#1e2a45] text-sm font-medium";

export default function Layout() {
  return (
    <div className="flex h-screen bg-[#0a0e1a] overflow-hidden">

      {/* Sidebar */}
      <aside className="w-52 flex-shrink-0 bg-[#0f1629] border-r border-[#1e2a45] flex flex-col">

        {/* Logo */}
        <div className="p-4 border-b border-[#1e2a45]">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center">
              <Activity size={16} className="text-white" />
            </div>
            <div>
              <div className="text-white font-bold text-sm leading-tight">AI Incident</div>
              <div className="text-blue-400 text-xs">Investigator</div>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 p-3 space-y-0.5">
          <NavLink to="/dashboard" className={({ isActive }) => isActive ? navActive : navBase}>
            <LayoutDashboard size={15} />
            Dashboard
          </NavLink>

          <NavLink to="/scenarios" className={({ isActive }) => isActive ? navActive : navBase}>
            <FlaskConical size={15} />
            Load Incident
          </NavLink>

          <NavLink to="/compare" className={({ isActive }) => isActive ? navActive : navBase}>
            <GitCompare size={15} />
            Why AI?
          </NavLink>
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-[#1e2a45]">
          <div className="text-xs text-slate-500 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-green-500 inline-block" />
            Demo mode active
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
