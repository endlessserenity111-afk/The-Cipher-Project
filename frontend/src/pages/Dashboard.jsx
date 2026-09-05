import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell 
} from 'recharts';
import { 
  AlertTriangle, ShieldAlert, ShieldCheck, FileSearch, 
  BrainCircuit, Activity
} from 'lucide-react';
import { cn } from '../App';

const API_BASE = 'http://127.0.0.1:8000';

function StatCard({ title, value, subtitle, icon: Icon, colorClass }) {
  return (
    <div className="institutional-card p-6 flex items-start gap-4 transition-colors hover:bg-slate-50 duration-200">
      <div className={cn("p-2 rounded border", colorClass)}>
        <Icon className="w-5 h-5" />
      </div>
      <div>
        <h3 className="text-sm font-semibold text-slate-500 mb-1">{title}</h3>
        <p className="text-3xl font-bold text-slate-900">{value}</p>
        {subtitle && <p className="text-xs font-medium text-slate-400 mt-1 uppercase tracking-wider">{subtitle}</p>}
      </div>
    </div>
  );
}

export default function Dashboard() {
  const navigate = useNavigate();
  const [dashboardData, setDashboardData] = useState(null);
  const [stateData, setStateData] = useState([]);
  const [riskyProjects, setRiskyProjects] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [dashRes, stateRes, highRiskRes] = await Promise.all([
          fetch(`${API_BASE}/api/dashboard`),
          fetch(`${API_BASE}/api/rollups/state`),
          fetch(`${API_BASE}/api/projects?risk_level=HIGH&sort_by=risk_score&order=desc&page_size=10`)
        ]);
        
        const dash = await dashRes.json();
        const states = await stateRes.json();
        let risky = await highRiskRes.json();

        // If not enough HIGH risk, backfill with MEDIUM
        if (risky.items && risky.items.length < 10) {
          const medRiskRes = await fetch(`${API_BASE}/api/projects?risk_level=MEDIUM&sort_by=risk_score&order=desc&page_size=${10 - risky.items.length}`);
          const medRisk = await medRiskRes.json();
          risky.items = [...risky.items, ...(medRisk.items || [])];
        }

        setDashboardData(dash);
        // Sort states by avg risk score and take top 15
        setStateData(states.sort((a, b) => b.avg_risk_score - a.avg_risk_score).slice(0, 15));
        setRiskyProjects(risky.items || []);
      } catch (err) {
        console.error("Error fetching data:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  if (loading) {
    return <div className="flex justify-center items-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div></div>;
  }

  if (!dashboardData) return <div>Failed to load data</div>;

  const riskLevelData = [
    { name: 'High', value: dashboardData.high_risk_projects, color: '#ef4444' },
    { name: 'Medium', value: dashboardData.medium_risk_projects, color: '#eab308' },
    { name: 'Low', value: dashboardData.low_risk_projects, color: '#10b981' }
  ];

  return (
    <div className="space-y-8">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard 
          title="Total Analyzed" 
          value={dashboardData.recommendations?.toLocaleString()} 
          subtitle="Recommendation records"
          icon={FileSearch}
          colorClass="bg-slate-50 text-slate-600 border-slate-200"
        />
        <StatCard 
          title="High Confidence Matches" 
          value={(dashboardData.tier1_matches + dashboardData.tier2_matches)?.toLocaleString()} 
          subtitle="Tier 1 & Tier 2"
          icon={ShieldCheck}
          colorClass="bg-slate-50 text-slate-600 border-slate-200"
        />
        <StatCard 
          title="Needs Review" 
          value={dashboardData.unmatched?.toLocaleString()} 
          subtitle="Unmatched records"
          icon={ShieldAlert}
          colorClass="bg-slate-50 text-slate-600 border-slate-200"
        />
        <StatCard 
          title="ML Anomalies" 
          value={dashboardData.ml_anomaly_projects?.toLocaleString()} 
          subtitle="Flagged by model"
          icon={BrainCircuit}
          colorClass="bg-slate-50 text-slate-600 border-slate-200"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Risk Distribution Chart */}
        <div className="institutional-card p-6 col-span-1">
          <h3 className="text-base font-semibold text-slate-900 mb-6 flex items-center gap-2">
            <Activity className="w-4 h-4 text-slate-500" />
            Risk Level Distribution
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={riskLevelData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fill: '#64748b', fontSize: 12}} />
                <YAxis axisLine={false} tickLine={false} tick={{fill: '#64748b', fontSize: 12}} />
                <Tooltip 
                  cursor={{fill: '#f1f5f9'}}
                  contentStyle={{borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'}}
                />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {riskLevelData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* State Risk Chart */}
        <div className="institutional-card p-6 col-span-1 lg:col-span-2">
          <h3 className="text-base font-semibold text-slate-900 mb-6">Average Risk Score by State (Top 15)</h3>
          <div className="h-[400px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stateData} layout="vertical" margin={{ top: 5, right: 30, left: 40, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="#e2e8f0" />
                <XAxis type="number" axisLine={false} tickLine={false} tick={{fill: '#64748b', fontSize: 12}} />
                <YAxis dataKey="state" type="category" axisLine={false} tickLine={false} tick={{fill: '#475569', fontSize: 11}} width={120} interval={0} />
                <Tooltip 
                  cursor={{fill: '#f1f5f9'}}
                  contentStyle={{borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'}}
                  formatter={(value) => [value.toFixed(1), 'Avg Risk Score']}
                />
                <Bar dataKey="avg_risk_score" fill="#64748b" radius={[0, 4, 4, 0]} barSize={16} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Top Risky Projects Table */}
      <div className="institutional-card overflow-hidden">
        <div className="px-6 py-5 border-b border-slate-200 flex items-center justify-between bg-slate-50">
          <h3 className="text-base font-semibold text-slate-900 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-slate-500" />
            Highest Risk Projects
          </h3>
          <button 
            onClick={() => navigate('/projects?sort_by=risk_score&order=desc')}
            className="text-sm text-slate-600 font-semibold hover:text-slate-900 transition-colors"
          >
            View all →
          </button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr>
                <th className="table-header w-16">ID</th>
                <th className="table-header">MP Name</th>
                <th className="table-header">State</th>
                <th className="table-header text-right">Risk Score</th>
                <th className="table-header">Risk Level</th>
              </tr>
            </thead>
            <tbody>
              {riskyProjects.map((project) => (
                <tr 
                  key={project.recommendation_row_id} 
                  onClick={() => navigate(`/projects/${project.recommendation_row_id}`)}
                  className="table-row cursor-pointer"
                >
                  <td className="table-cell font-mono text-slate-500">{project.recommendation_row_id}</td>
                  <td className="table-cell font-medium text-slate-900">{project.mp_name}</td>
                  <td className="table-cell">{project.state}</td>
                  <td className="table-cell text-right font-medium">{project.risk_score}</td>
                  <td className="table-cell">
                    <span className={cn("badge", `badge-${project.risk_level?.toLowerCase()}`)}>
                      {project.risk_level}
                    </span>
                  </td>
                </tr>
              ))}
              {riskyProjects.length === 0 && (
                <tr>
                  <td colSpan="5" className="py-8 text-center text-slate-500">No high-risk projects found.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
