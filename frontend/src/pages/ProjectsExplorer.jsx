import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { ChevronLeft, ChevronRight, ArrowUpDown, Search, FilterX } from 'lucide-react';
import { cn } from '../App';

const API_BASE = 'http://127.0.0.1:8000';

export default function ProjectsExplorer() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  
  const [data, setData] = useState({ items: [], total: 0, page: 1, total_pages: 1 });
  const [states, setStates] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);

  // Extract params
  const page = parseInt(searchParams.get('page') || '1', 10);
  const riskLevel = searchParams.get('risk_level') || '';
  const state = searchParams.get('state') || '';
  const category = searchParams.get('category') || '';
  const sortBy = searchParams.get('sort_by') || 'risk_score';
  const order = searchParams.get('order') || 'desc';

  // Load filter options once
  useEffect(() => {
    async function loadFilters() {
      try {
        const [stateRes, catRes] = await Promise.all([
          fetch(`${API_BASE}/api/rollups/state`),
          fetch(`${API_BASE}/api/rollups/category`)
        ]);
        const stateData = await stateRes.json();
        const catData = await catRes.json();
        setStates(stateData.map(s => s.state));
        setCategories(catData.map(c => c.category));
      } catch (err) {
        console.error("Error loading filters", err);
      }
    }
    loadFilters();
  }, []);

  // Load projects when params change
  useEffect(() => {
    async function loadProjects() {
      setLoading(true);
      try {
        const params = new URLSearchParams();
        params.append('page', page);
        params.append('page_size', 50);
        if (riskLevel) params.append('risk_level', riskLevel);
        if (state) params.append('state', state);
        if (category) params.append('category', category);
        if (sortBy) params.append('sort_by', sortBy);
        if (order) params.append('order', order);

        const res = await fetch(`${API_BASE}/api/projects?${params.toString()}`);
        const json = await res.json();
        setData(json);
      } catch (err) {
        console.error("Error loading projects", err);
      } finally {
        setLoading(false);
      }
    }
    loadProjects();
  }, [page, riskLevel, state, category, sortBy, order]);

  function updateParam(key, value) {
    const newParams = new URLSearchParams(searchParams);
    if (value) {
      newParams.set(key, value);
    } else {
      newParams.delete(key);
    }
    if (key !== 'page') newParams.set('page', '1'); // reset page on filter change
    setSearchParams(newParams);
  }

  function handleSort(column) {
    if (sortBy === column) {
      updateParam('order', order === 'asc' ? 'desc' : 'asc');
    } else {
      const newParams = new URLSearchParams(searchParams);
      newParams.set('sort_by', column);
      newParams.set('order', 'desc');
      setSearchParams(newParams);
    }
  }

  function clearFilters() {
    setSearchParams(new URLSearchParams());
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-800">Projects Explorer</h2>
          <p className="text-slate-500 mt-1">Browse and filter all analyzed MPLADS projects.</p>
        </div>
      </div>

      {/* Filters */}
      <div className="institutional-card p-4 flex flex-wrap gap-4 items-end">
        <div className="flex flex-col gap-1.5 w-full md:w-auto min-w-[200px]">
          <label className="text-xs font-semibold text-slate-500 uppercase">Risk Level</label>
          <select 
            value={riskLevel} 
            onChange={(e) => updateParam('risk_level', e.target.value)}
            className="bg-white border border-slate-200 text-slate-800 rounded px-3 py-2 text-sm focus:outline-none focus:border-slate-400 transition-colors"
          >
            <option value="">All Levels</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>
        </div>

        <div className="flex flex-col gap-1.5 w-full md:w-auto min-w-[200px]">
          <label className="text-xs font-semibold text-slate-500 uppercase">State</label>
          <select 
            value={state} 
            onChange={(e) => updateParam('state', e.target.value)}
            className="bg-white border border-slate-200 text-slate-800 rounded px-3 py-2 text-sm focus:outline-none focus:border-slate-400 transition-colors"
          >
            <option value="">All States</option>
            {states.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>

        <div className="flex flex-col gap-1.5 w-full md:w-auto min-w-[200px]">
          <label className="text-xs font-semibold text-slate-500 uppercase">Category</label>
          <select 
            value={category} 
            onChange={(e) => updateParam('category', e.target.value)}
            className="bg-white border border-slate-200 text-slate-800 rounded px-3 py-2 text-sm focus:outline-none focus:border-slate-400 transition-colors"
          >
            <option value="">All Categories</option>
            {categories.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>

        <button 
          onClick={clearFilters}
          className="ml-auto flex items-center gap-2 px-4 py-2 text-sm font-semibold text-slate-600 bg-white border border-slate-200 hover:bg-slate-50 rounded transition-colors"
        >
          <FilterX className="w-4 h-4" />
          Clear Filters
        </button>
      </div>

      {/* Table */}
      <div className="institutional-card overflow-hidden flex flex-col relative min-h-[400px]">
        {loading && (
          <div className="absolute inset-0 bg-white/50 backdrop-blur-sm z-10 flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        )}
        
        <div className="overflow-x-auto flex-1">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr>
                <th className="table-header w-16">ID</th>
                <th className="table-header cursor-pointer hover:bg-slate-50" onClick={() => handleSort('state')}>
                  <div className="flex items-center gap-1">State <ArrowUpDown className="w-3 h-3 text-slate-400" /></div>
                </th>
                <th className="table-header">Work Description / Category</th>
                <th className="table-header cursor-pointer hover:bg-slate-50 text-right" onClick={() => handleSort('match_score')}>
                  <div className="flex items-center justify-end gap-1">Match % <ArrowUpDown className="w-3 h-3 text-slate-400" /></div>
                </th>
                <th className="table-header cursor-pointer hover:bg-slate-50 text-right" onClick={() => handleSort('risk_score')}>
                  <div className="flex items-center justify-end gap-1">Risk Score <ArrowUpDown className="w-3 h-3 text-slate-400" /></div>
                </th>
                <th className="table-header text-center">Risk Level</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((project) => (
                <tr 
                  key={project.recommendation_row_id} 
                  onClick={() => navigate(`/projects/${project.recommendation_row_id}`)}
                  className="table-row cursor-pointer group"
                >
                  <td className="table-cell font-mono text-slate-500 text-xs">{project.recommendation_row_id}</td>
                  <td className="table-cell font-medium text-slate-900">{project.state}</td>
                  <td className="table-cell max-w-xs">
                    <div className="truncate font-medium text-slate-800" title={project.category}>{project.category}</div>
                    <div className="text-xs text-slate-500 mt-0.5 truncate">{project.mp_name} - {project.constituency}</div>
                  </td>
                  <td className="table-cell text-right font-medium text-slate-700">{project.match_score?.toFixed(1)}%</td>
                  <td className="table-cell text-right font-medium">{project.risk_score}</td>
                  <td className="table-cell text-center">
                    <span className={cn("badge", `badge-${project.risk_level?.toLowerCase()}`)}>
                      {project.risk_level}
                    </span>
                  </td>
                </tr>
              ))}
              {!loading && data.items.length === 0 && (
                <tr>
                  <td colSpan="6" className="py-12 text-center text-slate-500 flex flex-col items-center">
                    <Search className="w-8 h-8 text-slate-300 mb-2" />
                    No projects match your filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="px-6 py-4 border-t border-slate-200 flex items-center justify-between bg-white">
          <div className="text-sm text-slate-500">
            Showing <span className="font-medium text-slate-800">{data.items.length}</span> of <span className="font-medium text-slate-800">{data.total}</span> results
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => updateParam('page', page - 1)}
              disabled={page <= 1}
              className="p-1.5 rounded bg-white border border-slate-200 text-slate-600 disabled:opacity-50 hover:bg-slate-50 transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="text-sm font-medium px-2 text-slate-700">
              Page {page} of {data.total_pages || 1}
            </span>
            <button
              onClick={() => updateParam('page', page + 1)}
              disabled={page >= data.total_pages}
              className="p-1.5 rounded bg-white border border-slate-200 text-slate-600 disabled:opacity-50 hover:bg-slate-50 transition-colors"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
