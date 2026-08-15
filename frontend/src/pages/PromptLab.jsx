import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { Beaker, Settings, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { API_BASE_URL } from '../config';

export default function PromptLab() {
  const location = useLocation();
  const [leads, setLeads] = useState([]);
  const [selectedLeadId, setSelectedLeadId] = useState('');
  
  const [systemPrompt, setSystemPrompt] = useState(
    "You are an elite outbound sales copywriter specializing in short, punchy cold emails. No fluff. Maximum 3 sentences."
  );
  const [userTemplate, setUserTemplate] = useState(
    "Hey {company_name}, noticed your site has {flaw_1}. We help {niche} businesses fix this to get more clients. Open to a chat?"
  );
  
  const [draftPrompt, setDraftPrompt] = useState("");
  const [evalPrompt, setEvalPrompt] = useState("");
  const [refinePrompt, setRefinePrompt] = useState("");

  useEffect(() => {
    fetch('${API_BASE_URL}/api/prompts/config')
      .then(r => r.json())
      .then(data => {
        if (data.draft_prompt) setDraftPrompt(data.draft_prompt);
        if (data.evaluate_prompt) setEvalPrompt(data.evaluate_prompt);
        if (data.refine_prompt) setRefinePrompt(data.refine_prompt);
      })
      .catch(console.error);
  }, []);
  
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  
  useEffect(() => {
    if (location.pathname === '/lab') {
      fetch(`${API_BASE_URL}/api/leads`)
        .then(r => r.json())
        .then(data => {
          setLeads(data);
          if(data.length > 0 && !selectedLeadId) setSelectedLeadId(data[0].id);
        })
        .catch(console.error);
    }
  }, [location.pathname]);

  const runTest = async () => {
    if (!selectedLeadId) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/prompts/test-pitch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          lead_id: selectedLeadId,
          system_prompt: systemPrompt,
          user_template: userTemplate,
          temperature: 0.7
        })
      });
      const data = await res.json();
      if (!res.ok) {
        alert(`Error: ${data.detail || 'Failed to generate test pitch'}`);
        return;
      }
      setResult(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Prompt & A/B Testing Lab</h1>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Editor */}
        <div className="space-y-4">
          <div className="bg-slate-800 rounded-lg p-5 border border-slate-700">
            <h3 className="font-semibold mb-4 flex items-center"><Settings className="w-4 h-4 mr-2"/> Configuration</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-slate-400 mb-1">Target Lead (Real Data Injection)</label>
                <select 
                  value={selectedLeadId} 
                  onChange={e => setSelectedLeadId(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-600 rounded-md p-2 text-sm"
                >
                  {leads.map(l => (
                    <option key={l.id} value={l.id}>{l.name} ({l.niche})</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm text-slate-400 mb-1">System Prompt</label>
                <textarea 
                  rows={4}
                  value={systemPrompt}
                  onChange={e => setSystemPrompt(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-600 rounded-md p-3 text-sm font-mono text-purple-300 focus:outline-none focus:border-purple-500"
                />
              </div>

              <div>
                <label className="block text-sm text-slate-400 mb-1">User Template (Available vars: {'{company_name}, {niche}, {flaw_1}'})</label>
                <textarea 
                  rows={4}
                  value={userTemplate}
                  onChange={e => setUserTemplate(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-600 rounded-md p-3 text-sm font-mono text-blue-300 focus:outline-none focus:border-purple-500"
                />
              </div>

              <button 
                onClick={runTest}
                disabled={loading || !selectedLeadId}
                className="w-full bg-purple-600 hover:bg-purple-700 py-3 rounded-md font-medium flex items-center justify-center transition-colors disabled:opacity-50"
              >
                <Beaker className="w-5 h-5 mr-2" />
                {loading ? 'Generating...' : 'Run A/B Test Pitch'}
              </button>
            </div>
          </div>
        </div>

        {/* Results */}
        <div>
          <div className="bg-slate-800 rounded-lg p-5 border border-slate-700 h-full flex flex-col">
            <h3 className="font-semibold mb-4">Output Variant</h3>
            
            {result ? (
              <div className="space-y-6 flex-1">
                <div className="bg-slate-900 p-4 rounded-md border border-slate-700">
                  <p className="whitespace-pre-wrap text-slate-200">{result.pitch}</p>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-slate-900 p-3 rounded-md border border-slate-700 text-center">
                    <div className="text-2xl font-bold text-white">{result.word_count}</div>
                    <div className="text-xs text-slate-400 uppercase">Words</div>
                  </div>
                  <div className={`p-3 rounded-md border text-center ${result.flags.length > 0 ? 'bg-red-900/20 border-red-800' : 'bg-green-900/20 border-green-800'}`}>
                    <div className="text-2xl font-bold flex justify-center items-center h-8">
                      {result.flags.length > 0 ? <AlertTriangle className="text-red-500 w-6 h-6"/> : <CheckCircle2 className="text-green-500 w-6 h-6"/>}
                    </div>
                    <div className="text-xs text-slate-400 uppercase">Tone Check</div>
                  </div>
                </div>

                {result.flags.length > 0 && (
                  <div className="bg-red-900/20 border border-red-800/50 rounded-md p-3 text-sm text-red-200">
                    <strong>Banned Words Detected:</strong> {result.flags.join(", ")}
                  </div>
                )}
                
                <div className="pt-4 border-t border-slate-700">
                  <button
                    onClick={async () => {
                      try {
                        const res = await fetch('${API_BASE_URL}/api/prompts/save-pitch', {
                          method: 'POST',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify({
                            lead_id: parseInt(selectedLeadId),
                            subject_line: "Generated A/B Pitch",
                            body_text: result.pitch
                          })
                        });
                        if (res.ok) {
                          alert("Pitch saved to CRM successfully!");
                        } else {
                          alert("Failed to save pitch to CRM.");
                        }
                      } catch (e) {
                        alert("Error saving pitch: " + e.message);
                      }
                    }}
                    className="w-full bg-green-600 hover:bg-green-700 py-3 rounded-md font-medium flex items-center justify-center transition-colors shadow-lg"
                  >
                    <CheckCircle2 className="w-5 h-5 mr-2" />
                    Save Pitch to CRM
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex-1 border-2 border-dashed border-slate-700 rounded-md flex items-center justify-center text-slate-500">
                Run a test to see the generated pitch here.
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="mt-12 bg-slate-800 rounded-lg p-5 border border-slate-700">
        <h3 className="font-semibold mb-4 text-xl flex items-center"><Settings className="w-5 h-5 mr-2 text-purple-400"/> Core Pipeline Prompts (Ollama / Groq)</h3>
        <p className="text-sm text-slate-400 mb-6">These are the actual prompts used by the automated backend pipeline. Edit them to improve your outbound copy engine.</p>
        
        <div className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Stage 1: Draft Generator Prompt</label>
            <p className="text-xs text-slate-500 mb-2">Vars: {'{lead_name}, {lead_niche}, {lead_city}, {flaws_text}'}</p>
            <textarea 
              rows={6}
              value={draftPrompt}
              onChange={e => setDraftPrompt(e.target.value)}
              className="w-full bg-slate-900 border border-slate-600 rounded-md p-3 text-sm font-mono text-purple-200 focus:outline-none focus:border-purple-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Stage 2: Evaluator Prompt</label>
            <p className="text-xs text-slate-500 mb-2">Vars: {'{num_drafts}, {lead_name}, {drafts_text}'}</p>
            <textarea 
              rows={4}
              value={evalPrompt}
              onChange={e => setEvalPrompt(e.target.value)}
              className="w-full bg-slate-900 border border-slate-600 rounded-md p-3 text-sm font-mono text-blue-200 focus:outline-none focus:border-purple-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Stage 3: Refiner Prompt</label>
            <p className="text-xs text-slate-500 mb-2">Vars: {'{draft_subject}, {draft_body}, {draft_flaws}, {draft_compliment}'}</p>
            <textarea 
              rows={4}
              value={refinePrompt}
              onChange={e => setRefinePrompt(e.target.value)}
              className="w-full bg-slate-900 border border-slate-600 rounded-md p-3 text-sm font-mono text-green-200 focus:outline-none focus:border-purple-500"
            />
          </div>

          <button 
            onClick={async () => {
              try {
                const res = await fetch('${API_BASE_URL}/api/prompts/config', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({
                    draft_prompt: draftPrompt,
                    evaluate_prompt: evalPrompt,
                    refine_prompt: refinePrompt
                  })
                });
                if (res.ok) alert("Pipeline Prompts Saved!");
              } catch (e) {
                alert("Error saving pipeline prompts");
              }
            }}
            className="bg-purple-600 hover:bg-purple-700 py-3 px-6 rounded-md font-medium transition-colors"
          >
            Save Pipeline Prompts
          </button>
        </div>
      </div>
    </div>
  );
}
