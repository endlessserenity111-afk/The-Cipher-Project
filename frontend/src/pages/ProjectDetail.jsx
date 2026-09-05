import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, CheckCircle2, AlertTriangle, Image as ImageIcon, ImageOff, BrainCircuit, ShieldAlert, Sparkles } from 'lucide-react';
import { cn } from '../App';

const API_BASE = 'http://127.0.0.1:8000';

export default function ProjectDetail() {
  const { id } = useParams();
  const [project, setProject] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [aiExplanation, setAiExplanation] = useState('');
  const [aiLoading, setAiLoading] = useState(true);

  useEffect(() => {
    async function loadProject() {
      setLoading(true);
      try {
        const res = await fetch(`${API_BASE}/api/projects/${id}`);
        if (!res.ok) throw new Error('Project not found');
        const data = await res.json();
        setProject(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    
    async function loadExplanation() {
      setAiLoading(true);
      try {
        const res = await fetch(`${API_BASE}/api/projects/${id}/explain`);
        if (!res.ok) throw new Error('Explanation failed');
        const data = await res.json();
        setAiExplanation(data.explanation || 'Explanation temporarily unavailable.');
      } catch (err) {
        setAiExplanation('Explanation temporarily unavailable — see risk factors above.');
      } finally {
        setAiLoading(false);
      }
    }
    
    loadProject();
    loadExplanation();
  }, [id]);

  if (loading) {
    return <div className="flex justify-center items-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div></div>;
  }

  if (error || !project) {
    return (
      <div className="institutional-card p-12 text-center">
        <AlertTriangle className="w-12 h-12 text-red-500 mx-auto mb-4" />
        <h2 className="text-xl font-bold text-slate-900 mb-2">Error Loading Project</h2>
        <p className="text-slate-500 mb-6">{error || 'Project not found.'}</p>
        <Link to="/projects" className="text-blue-600 font-semibold hover:underline">← Back to Projects Explorer</Link>
      </div>
    );
  }

  // Parse risk reasons
  const riskReasons = project.risk_reasons ? project.risk_reasons.split(' | ') : [];

  return (
    <div className="space-y-6">
      <Link to="/projects" className="inline-flex items-center gap-2 text-sm font-medium text-slate-500 hover:text-slate-800 transition-colors">
        <ArrowLeft className="w-4 h-4" />
        Back to Projects
      </Link>

      <div className="flex flex-col md:flex-row justify-between items-start gap-4 mb-2">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 leading-tight">
            {project.category || 'Project Detail'}
          </h2>
          <p className="text-slate-500 mt-1 flex items-center gap-2">
            <span>{project.mp_name}</span> • <span>{project.constituency}, {project.state}</span>
          </p>
        </div>
        <div className="flex gap-2 items-center">
          <span className={cn("badge text-sm px-3 py-1", `badge-${project.risk_level?.toLowerCase()}`)}>
            Risk Level: {project.risk_level}
          </span>
          <span className="badge bg-slate-100 text-slate-700 border-slate-200 text-sm px-3 py-1">
            {project.match_tier}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Recommendation vs Completion */}
        <div className="lg:col-span-2 space-y-6">
          <h3 className="text-lg font-semibold text-slate-900 border-b-2 border-slate-200 pb-2">Recommendation vs Completion</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            
            <div className="institutional-panel p-5 border-l-4 border-l-slate-400">
              <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-4">Recommended Work</h4>
              <div className="space-y-4">
                <div>
                  <span className="text-xs text-slate-500 block">Work ID</span>
                  <span className="font-mono text-sm text-slate-800">{project.recommendation_work_id || 'N/A'}</span>
                </div>
                <div>
                  <span className="text-xs text-slate-500 block">Amount</span>
                  <span className="font-medium text-lg text-slate-800">
                    ₹{project.recommended_amount ? project.recommended_amount.toLocaleString() : 'N/A'}
                  </span>
                </div>
              </div>
            </div>

            <div className="institutional-panel p-5 border-l-4 border-l-slate-700">
              <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-4">Completed Work</h4>
              <div className="space-y-4">
                <div>
                  <span className="text-xs text-slate-500 block">Work ID</span>
                  <span className="font-mono text-sm text-slate-800">{project.completion_work_id || 'N/A'}</span>
                </div>
                <div>
                  <span className="text-xs text-slate-500 block">Amount</span>
                  <span className="font-medium text-lg text-slate-800">
                    ₹{project.final_amount ? project.final_amount.toLocaleString() : 'N/A'}
                  </span>
                </div>
                <div>
                  <span className="text-xs text-slate-500 block">Days to Completion</span>
                  <span className="text-slate-800">{project.days_to_completion || 'N/A'} days</span>
                </div>
              </div>
            </div>
            
          </div>

          <h3 className="text-lg font-semibold text-slate-900 border-b-2 border-slate-200 pb-2 mt-8">Match Confidence</h3>
          <div className="institutional-card p-6">
            <div className="flex items-center gap-4 mb-6">
              <div className="w-16 h-16 rounded bg-slate-50 border border-slate-200 flex items-center justify-center">
                <span className="text-xl font-bold text-slate-900">{project.match_score?.toFixed(0)}%</span>
              </div>
              <div>
                <p className="font-medium text-slate-800 text-lg">System Match Score</p>
                <p className="text-slate-500 text-sm">Determined by algorithmic similarity</p>
              </div>
            </div>
          </div>
        </div>

        {/* Risk Analysis Side Panel */}
        <div className="space-y-6">
          <div className="institutional-card overflow-hidden">
            <div className="bg-slate-50 p-5 border-b border-slate-200">
              <h3 className="text-base font-semibold text-slate-900 flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-slate-500" />
                Risk Analysis
              </h3>
            </div>
            
            <div className="p-6 space-y-6">
              <div className="text-center">
                <div className="text-5xl font-black text-slate-900 mb-2">{project.risk_score} <span className="text-2xl text-slate-400 font-medium">/100</span></div>
                <div className={cn("badge", `badge-${project.risk_level?.toLowerCase()}`)}>
                  {project.risk_level} RISK
                </div>
              </div>

              {riskReasons.length > 0 && (
                <div className="space-y-2 mt-6">
                  <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider">Risk Factors</h4>
                  <ul className="space-y-2">
                    {riskReasons.map((reason, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-sm text-slate-700 bg-slate-50 p-2 rounded border border-slate-200">
                        <AlertTriangle className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
                        <span>{reason}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {project.ml_anomaly_flag && (
                <div className="bg-slate-100 border border-slate-300 rounded p-3 flex items-start gap-3">
                  <BrainCircuit className="w-4 h-4 text-slate-700 shrink-0 mt-0.5" />
                  <p className="text-sm font-medium text-slate-800">Flagged by anomaly detection model</p>
                </div>
              )}
            </div>
          </div>

          {/* AI Summary Section */}
          <div className="institutional-card overflow-hidden">
            <div className="bg-slate-50 p-5 border-b border-slate-200 flex items-center justify-between">
              <h3 className="text-base font-semibold text-slate-900 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-slate-500" />
                AI Summary
              </h3>
            </div>
            <div className="p-6">
              {aiLoading ? (
                <div className="flex items-center gap-3 text-slate-500">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
                  <span className="text-sm font-medium animate-pulse">Generating risk context...</span>
                </div>
              ) : (
                <p className="text-sm text-slate-700 leading-relaxed">
                  {aiExplanation}
                </p>
              )}
            </div>
          </div>

          <div className="institutional-card p-5">
            <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Evidence Status</h3>
            {project.has_images ? (
              <div className="flex items-center gap-3 text-emerald-700 bg-emerald-50 p-3 rounded-lg border border-emerald-100">
                <ImageIcon className="w-5 h-5" />
                <span className="font-medium text-sm">Photographic proof available</span>
              </div>
            ) : (
              <div className="flex items-center gap-3 text-amber-700 bg-amber-50 p-3 rounded-lg border border-amber-100">
                <ImageOff className="w-5 h-5" />
                <span className="font-medium text-sm">No photographic proof of completion</span>
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
