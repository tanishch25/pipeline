import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { Search, MapPin, Copy, Save, Globe, AlertCircle, Phone, Link, CheckCircle2 } from 'lucide-react';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from 'recharts';

export default function LeadCRM() {
  const location = useLocation();
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState(null);
  const [selectedLeads, setSelectedLeads] = useState(new Set());
  
  // Filters
  const [search, setSearch] = useState("");
  const [niche, setNiche] = useState("");
  const [statusFilter, setStatusFilter] = useState('');
  const [minScore, setMinScore] = useState(0);
  


  const fetchLeads = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (search) params.append("search", search);
      if (niche) params.append("niche", niche);
      if (statusFilter) params.append("status", statusFilter);
      if (minScore > 0) params.append("min_score", minScore);
      
      const res = await fetch(`http://localhost:8000/api/leads?${params}`);
      const data = await res.json();
      setLeads(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (location.pathname === '/crm') {
      fetchLeads();
    }
  }, [location.pathname, search, niche, statusFilter, minScore]);

  const toggleSelectAll = () => {
    if (selectedLeads.size === leads.length && leads.length > 0) {
      setSelectedLeads(new Set());
    } else {
      setSelectedLeads(new Set(leads.map(l => l.id)));
    }
  };

  const updateStatus = async (id, newStatus) => {
    await fetch(`http://localhost:8000/api/leads/${id}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus })
    });
    fetchLeads(); // Refresh
  };

  const savePitch = async (id, newBody) => {
    await fetch(`http://localhost:8000/api/leads/${id}/pitch`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ body_text: newBody })
    });
    alert("Pitch updated!");
    fetchLeads();
  };

  const toggleSelect = (id) => {
    const newSet = new Set(selectedLeads);
    if (newSet.has(id)) newSet.delete(id);
    else newSet.add(id);
    setSelectedLeads(newSet);
  };

  const handleBulkSend = async () => {
    if (selectedLeads.size === 0) return;
    if (!confirm(`Are you sure you want to send ${selectedLeads.size} emails?`)) return;
    
    setLoading(true);
    try {
      const res = await fetch(`http://localhost:8000/api/leads/bulk-send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lead_ids: Array.from(selectedLeads) })
      });
      const data = await res.json();
      alert(`Bulk send complete: ${data.success} succeeded, ${data.failed} failed.`);
      setSelectedLeads(new Set());
      fetchLeads();
    } catch (e) {
      alert("Error sending emails: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Lead CRM</h1>
        <div className="flex space-x-4">
          <button 
            onClick={async () => {
              setLoading(true);
              try {
                await fetch('http://localhost:8000/api/pipeline/sync', { method: 'POST' });
                alert("Inbox sync triggered in the background.");
              } catch (e) {
                alert("Sync failed: " + e.message);
              } finally {
                setLoading(false);
              }
            }}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-bold shadow-lg transition-colors flex items-center space-x-2"
          >
            <span>Run Inbox Sync</span>
          </button>
          
          <button 
            onClick={toggleSelectAll}
            className="bg-slate-700 hover:bg-slate-600 text-white px-4 py-2 rounded-lg font-bold shadow-lg transition-colors flex items-center space-x-2"
          >
            <CheckCircle2 className="w-5 h-5" />
            <span>{selectedLeads.size === leads.length && leads.length > 0 ? "Deselect All" : "Select All"}</span>
          </button>
          {selectedLeads.size > 0 && (
            <button 
              onClick={handleBulkSend}
              className="bg-green-600 hover:bg-green-700 text-white px-6 py-2 rounded-lg font-bold shadow-lg transition-colors flex items-center space-x-2"
            >
              <AlertCircle className="w-5 h-5" />
              <span>Send {selectedLeads.size} Selected Pitches</span>
            </button>
          )}
        </div>
      </div>
      
      {/* Filters Toolbar */}
      <div className="bg-slate-800 p-4 rounded-lg border border-slate-700 grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
          <input 
            type="text" 
            placeholder="Search name, city, url..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-slate-900 border border-slate-600 rounded-md focus:outline-none focus:border-purple-500"
          />
        </div>
        <select value={niche} onChange={e => setNiche(e.target.value)} className="bg-slate-900 border border-slate-600 rounded-md px-4 py-2 text-white">
          <option value="">All Niches</option>
          <option value="gym">Gym</option>
          <option value="restaurant">Restaurant</option>
          <option value="utility">Utility</option>
          <option value="other">Other</option>
        </select>
        <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="bg-slate-900 border border-slate-600 rounded-md px-4 py-2 text-white">
          <option value="">All Stages</option>
          <option value="DISCOVERED">Discovered</option>
          <option value="AUDITED">Audited</option>
          <option value="SCORED">Scored</option>
          <option value="PITCH READY">Pitch Ready</option>
          <option value="SENT">Sent</option>
          <option value="REPLIED">Replied</option>
          <option value="CALL_BOOKED">Call Booked</option>
          <option value="WON">Won</option>
          <option value="LOST">Lost</option>
        </select>
        <div className="flex items-center space-x-2">
          <span className="text-sm text-slate-300">Min Score: {minScore}</span>
          <input type="range" min="0" max="100" value={minScore} onChange={e => setMinScore(e.target.value)} className="w-full" />
        </div>
      </div>

      {/* Lead List */}
      {loading ? (
        <div className="text-center py-12 text-slate-400">Loading leads...</div>
      ) : leads.length === 0 ? (
        <div className="text-center py-12 text-slate-400">No leads found.</div>
      ) : (
        <div className="space-y-4">
          {leads.map(lead => (
            <div key={lead.id} className="bg-slate-800 rounded-lg border border-slate-700 overflow-hidden">
              {/* Header */}
              <div 
                className="p-4 flex items-center justify-between cursor-pointer hover:bg-slate-750"
                onClick={() => setExpandedId(expandedId === lead.id ? null : lead.id)}
              >
                <div className="flex items-center space-x-4">
                  <input 
                    type="checkbox" 
                    checked={selectedLeads.has(lead.id)}
                    onChange={(e) => {
                      e.stopPropagation();
                      toggleSelect(lead.id);
                    }}
                    className="w-5 h-5 rounded border-slate-600 text-purple-600 focus:ring-purple-500 bg-slate-900 ml-4 cursor-pointer"
                  />
                  <div className={`w-12 h-12 rounded-full flex items-center justify-center font-bold text-lg ${
                    lead.audit?.final_revamp_score >= 70 ? 'bg-red-500/20 text-red-400' :
                    lead.audit?.final_revamp_score >= 40 ? 'bg-yellow-500/20 text-yellow-400' :
                    'bg-slate-700 text-slate-400'
                  }`}>
                    {lead.audit ? lead.audit.final_revamp_score : '?'}
                  </div>
                  <div className="flex-1 min-w-0">
                  <h3 className="text-xl font-bold text-white truncate">{lead.name}</h3>
                  <div className="flex flex-col sm:flex-row sm:items-center text-sm text-slate-400 space-y-1 sm:space-y-0 sm:space-x-4 mt-1">
                    <span className="flex items-center space-x-1">
                      <MapPin className="w-4 h-4" />
                      <span>{lead.city || 'Unknown Location'}</span>
                    </span>
                    <span className="flex items-center space-x-1">
                      <Link className="w-4 h-4" />
                      <a href={lead.website_url} target="_blank" rel="noopener noreferrer" className="hover:text-purple-400 truncate max-w-[200px]" onClick={e => e.stopPropagation()}>
                        {lead.website_url.replace(/^https?:\/\/(www\.)?/, '')}
                      </a>
                    </span>
                    {lead.email && (
                      <span className="flex items-center space-x-1 text-green-400">
                        <span>📧 {lead.email}</span>
                      </span>
                    )}
                    {lead.phone && (
                      <span className="flex items-center space-x-1 text-blue-400">
                        <Phone className="w-3 h-3" />
                        <span>{lead.phone}</span>
                      </span>
                    )}
                    {(lead.facebook_url || lead.twitter_url || lead.instagram_url || lead.linkedin_url) && (
                      <span className="flex items-center space-x-2 text-pink-400 ml-2">
                        {lead.facebook_url && <a href={lead.facebook_url} target="_blank" rel="noreferrer" onClick={e => e.stopPropagation()} className="hover:text-pink-300">FB</a>}
                        {lead.twitter_url && <a href={lead.twitter_url} target="_blank" rel="noreferrer" onClick={e => e.stopPropagation()} className="hover:text-pink-300">X</a>}
                        {lead.instagram_url && <a href={lead.instagram_url} target="_blank" rel="noreferrer" onClick={e => e.stopPropagation()} className="hover:text-pink-300">IG</a>}
                        {lead.linkedin_url && <a href={lead.linkedin_url} target="_blank" rel="noreferrer" onClick={e => e.stopPropagation()} className="hover:text-pink-300">IN</a>}
                      </span>
                    )}
                  </div>
                </div>
                </div>
                <div className="flex items-center space-x-4">
                  {lead.follow_up_count > 0 && (
                    <span className="px-3 py-1 rounded-full text-xs font-medium bg-blue-900/40 text-blue-300 border border-blue-800">
                      FU: {lead.follow_up_count}
                    </span>
                  )}
                  <span className="px-3 py-1 rounded-full text-xs font-medium bg-slate-700 border border-slate-600">
                    {lead.status}
                  </span>
                  <button 
                    onClick={async (e) => {
                      e.stopPropagation();
                      if (confirm("Are you sure you want to permanently delete this lead?")) {
                        await fetch(`http://localhost:8000/api/leads/${lead.id}`, { method: 'DELETE' });
                        fetchLeads();
                      }
                    }}
                    className="p-1 hover:bg-red-900/50 text-red-400 rounded-md transition-colors"
                    title="Delete Lead"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path></svg>
                  </button>
                </div>
              </div>

              {/* Expanded Drawer */}
              {expandedId === lead.id && (
                <div className="p-6 border-t border-slate-700 bg-slate-800/50 grid grid-cols-1 lg:grid-cols-2 gap-6">
                  
                  {/* Left Col: Details & Audit */}
                  <div className="space-y-6">
                    <div className="flex space-x-3">
                      <a href={lead.website_url} target="_blank" rel="noreferrer" className="flex-1 flex items-center justify-center space-x-2 bg-slate-700 hover:bg-slate-600 py-2 rounded-md transition-colors text-sm">
                        <Globe className="w-4 h-4" /> <span>Visit Website</span>
                      </a>
                      <select 
                        value={lead.status}
                        onChange={(e) => updateStatus(lead.id, e.target.value)}
                        className="flex-1 bg-purple-600 hover:bg-purple-700 border-none rounded-md px-3 py-2 text-sm text-center font-medium focus:ring-0"
                      >
                        <option value="DISCOVERED">Discovered</option>
                        <option value="AUDITED">Audited</option>
                        <option value="SCORED">Scored</option>
                        <option value="PITCH READY">Pitch Ready</option>
                        <option value="SENT">Sent</option>
                        <option value="REPLIED">Replied</option>
                        <option value="CALL_BOOKED">Call Booked</option>
                        <option value="WON">Won</option>
                        <option value="LOST">Lost</option>
                      </select>
                    </div>

                    {lead.audit && (
                      <div className="bg-slate-900 rounded-lg p-4 border border-slate-700 h-64">
                        <ResponsiveContainer width="100%" height="100%">
                          <RadarChart cx="50%" cy="50%" outerRadius="80%" data={[
                            { subject: 'Speed', A: lead.audit.load_time_seconds > 0 ? (10 - lead.audit.load_time_seconds) : 5, fullMark: 10 },
                            { subject: 'Mobile UX', A: lead.audit.is_mobile_responsive ? 10 : 2, fullMark: 10 },
                            { subject: 'Security', A: lead.audit.has_ssl ? 10 : 0, fullMark: 10 },
                            { subject: 'Design', A: 7, fullMark: 10 }, // Mock
                            { subject: 'SEO', A: 6, fullMark: 10 } // Mock
                          ]}>
                            <PolarGrid stroke="#334155" />
                            <PolarAngleAxis dataKey="subject" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                            <PolarRadiusAxis angle={30} domain={[0, 10]} tick={false} axisLine={false} />
                            <Radar name="Score" dataKey="A" stroke="#a855f7" fill="#a855f7" fillOpacity={0.4} />
                          </RadarChart>
                        </ResponsiveContainer>
                      </div>
                    )}
                    
                    {lead.audit?.ai_reasoning && (
                      <div className="bg-slate-900 rounded-lg p-4 border border-slate-700 max-h-48 overflow-y-auto">
                        <h5 className="font-semibold text-slate-300 mb-2">Audit Defect Reasoning:</h5>
                        <p className="text-sm text-slate-400 whitespace-pre-wrap">{lead.audit.ai_reasoning}</p>
                      </div>
                    )}
                  </div>

                  {/* Right Col: Pitch Editor */}
                  <div className="flex flex-col h-full space-y-3">
                    <h4 className="font-medium text-slate-300 flex items-center justify-between">
                      <span>Generated Cold Pitch</span>
                      {lead.pitch && (
                        <button onClick={() => {
                          navigator.clipboard.writeText(lead.pitch.body_text);
                          alert('Copied!');
                        }} className="text-xs flex items-center space-x-1 text-slate-400 hover:text-white">
                          <Copy className="w-3 h-3" /> <span>Copy</span>
                        </button>
                      )}
                    </h4>
                    {lead.pitch ? (
                      <div className="flex-1 flex flex-col space-y-2">
                        <input 
                          type="text" 
                          readOnly 
                          value={lead.pitch.subject_line}
                          className="bg-slate-900 border border-slate-700 rounded-md px-3 py-2 text-sm text-slate-300" 
                        />
                        <textarea
                          defaultValue={lead.pitch.body_text}
                          id={`pitch-${lead.id}`}
                          className="flex-1 bg-slate-900 border border-slate-700 rounded-md p-3 text-sm resize-none focus:outline-none focus:border-purple-500"
                        />
                        
                        <div className="flex items-center space-x-2 pt-2 border-t border-slate-700">
                          <input 
                            type="email" 
                            id={`email-${lead.id}`}
                            defaultValue={lead.email || ""}
                            placeholder="target@email.com" 
                            className="flex-1 bg-slate-900 border border-slate-700 rounded-md px-3 py-2 text-sm focus:outline-none focus:border-purple-500"
                          />
                          <button 
                            onClick={async () => {
                              const body = document.getElementById(`pitch-${lead.id}`).value;
                              await savePitch(lead.id, body);
                            }}
                            className="bg-slate-600 hover:bg-slate-700 text-sm py-2 px-4 rounded-md flex justify-center items-center space-x-2 transition-colors font-medium text-white shadow-lg"
                          >
                            <Save className="w-4 h-4" /> <span>Save Changes</span>
                          </button>
                          <button 
                            onClick={async () => {
                              const body = document.getElementById(`pitch-${lead.id}`).value;
                              const toEmail = document.getElementById(`email-${lead.id}`).value;
                              
                              if (!toEmail) {
                                alert("Please enter a target email address.");
                                return;
                              }
                              
                              // 1. Save edits first
                              await savePitch(lead.id, body);
                              
                              // 2. Send email
                              try {
                                const res = await fetch(`http://localhost:8000/api/leads/${lead.id}/send`, {
                                  method: 'POST',
                                  headers: { 'Content-Type': 'application/json' },
                                  body: JSON.stringify({ to_email: toEmail })
                                });
                                
                                if (res.ok) {
                                  alert("Pitch Sent Successfully!");
                                  fetchLeads(); // Refresh to show PITCHED status
                                } else {
                                  const err = await res.json();
                                  alert(`Failed to send: ${err.detail}`);
                                }
                              } catch (e) {
                                alert(`Error: ${e.message}`);
                              }
                            }}
                            className="bg-green-600 hover:bg-green-700 text-sm py-2 px-4 rounded-md flex justify-center items-center space-x-2 transition-colors font-medium text-white shadow-lg"
                          >
                            <CheckCircle2 className="w-4 h-4" /> <span>Approve & Send</span>
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="flex-1 border border-dashed border-slate-700 rounded-md flex items-center justify-center text-slate-500 text-sm flex-col space-y-2">
                        <AlertCircle className="w-6 h-6" />
                        <span>No pitch generated for this lead.</span>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
