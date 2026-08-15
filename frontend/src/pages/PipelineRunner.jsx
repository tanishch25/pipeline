import React, { useState, useEffect, useRef } from 'react';
import { Play, Loader2, Square } from 'lucide-react';
import { API_BASE_URL } from '../config';

export default function PipelineRunner() {
  const [query, setQuery] = useState("Gyms in Austin TX");
  const [limit, setLimit] = useState(5);
  const [mockMode, setMockMode] = useState(false);
  const [engine, setEngine] = useState("hybrid");
  const [autoSend, setAutoSend] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [logs, setLogs] = useState([]);
  const logsEndRef = useRef(null);

  const scrollToBottom = () => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [logs]);

  const launchPipeline = async () => {
    if (!query) return;
    setIsRunning(true);
    setLogs([]);
    
    try {
      // 1. Trigger the background run
      const res = await fetch(`${API_BASE_URL}/api/pipeline/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, limit: parseInt(limit), mock_mode: mockMode, engine: engine, auto_send: autoSend })
      });
      if (!res.ok) throw new Error("Failed to start pipeline");

      // 2. Connect to SSE stream
      const eventSource = new EventSource(`${API_BASE_URL}/api/pipeline/progress`);
      
      eventSource.onmessage = (event) => {
        if (event.data === "DONE") {
          eventSource.close();
          setIsRunning(false);
          setLogs(prev => [...prev, "[SYSTEM] Pipeline executed successfully."]);
        } else {
          setLogs(prev => [...prev, event.data]);
        }
      };

      eventSource.onerror = () => {
        eventSource.close();
        setIsRunning(false);
        setLogs(prev => [...prev, "[ERROR] Connection to event stream lost."]);
      };
      
    } catch (err) {
      setLogs(prev => [...prev, `[ERROR] ${err.message}`]);
      setIsRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Pipeline Runner</h1>
        <p className="text-slate-400 mt-1">Configure and launch the autonomous lead scraper and auditor.</p>
      </div>

      <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-slate-300 mb-2">Search Queries (Comma-separated)</label>
            <textarea 
              value={query} 
              onChange={e => setQuery(e.target.value)}
              className="w-full bg-slate-900 border border-slate-600 rounded-md px-4 py-2 text-white focus:outline-none focus:border-purple-500 h-24 resize-none"
              placeholder="e.g. Restaurants in Manchester UK, Gyms in Austin TX"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Batch Limit ({limit})</label>
            <input 
              type="range" 
              min="1" max="500" 
              value={limit} 
              onChange={e => setLimit(e.target.value)}
              className="w-full mt-2"
            />
            <p className="text-xs text-slate-400 mt-2">Max 500 across all queries.</p>
          </div>
        </div>
        
        <div className="mt-6">
            <label className="block text-sm font-medium text-slate-300 mb-2">AI Engine</label>
            <select 
              value={engine}
              onChange={e => setEngine(e.target.value)}
              className="w-full md:w-1/3 bg-slate-900 border border-slate-600 rounded-md px-4 py-2 text-white focus:outline-none focus:border-purple-500"
            >
              <option value="hybrid">Hybrid (Groq + Ollama)</option>
              <option value="local">Local Only (Ollama)</option>
              <option value="cloud">Cloud Only (Groq)</option>
            </select>
            <p className="text-xs text-slate-400 mt-2">
              {engine === "hybrid" && "Currently using: Groq API for lightning-fast analysis, and local Ollama for pitch generation."}
              {engine === "local" && "Currently using: 100% offline local Ollama model for both analysis and pitching (slower, but unlimited/private)."}
              {engine === "cloud" && "Currently using: Groq API for everything (lightning fast, but counts against your daily rate limit)."}
            </p>
        </div>

        <div className="flex flex-col space-y-4 mt-6">
          <div className="flex items-center">
            <input 
              type="checkbox" 
              id="mockMode"
              checked={mockMode}
              onChange={e => setMockMode(e.target.checked)}
              className="w-4 h-4 text-purple-600 bg-slate-900 border-slate-600 rounded focus:ring-purple-500 focus:ring-2"
            />
            <label htmlFor="mockMode" className="ml-2 text-sm font-medium text-slate-300">
              Enable Dry Run / Mock Mode (Bypass APIs)
            </label>
          </div>
          
          <div className="flex items-center">
            <input 
              type="checkbox" 
              id="autoSend"
              checked={autoSend}
              onChange={e => setAutoSend(e.target.checked)}
              className="w-4 h-4 text-purple-600 bg-slate-900 border-slate-600 rounded focus:ring-purple-500 focus:ring-2"
            />
            <label htmlFor="autoSend" className="ml-2 text-sm font-medium text-slate-300">
              Auto-Send Emails (Automatically send pitch emails after evaluation layer succeeds)
            </label>
          </div>
        </div>

        <div className="mt-8 pt-6 border-t border-slate-700 flex justify-end space-x-4">
          {isRunning && (
            <button
              onClick={async () => {
                await fetch(`${API_BASE_URL}/api/pipeline/stop`, { method: 'POST' });
                setLogs(prev => [...prev, "[SYSTEM] Stop signal sent. Halting soon..."]);
              }}
              className="flex items-center space-x-2 bg-red-600 hover:bg-red-700 text-white px-6 py-2 rounded-md font-medium transition-colors"
            >
              <span>Stop Pipeline</span>
            </button>
          )}
          <button
            onClick={launchPipeline}
            disabled={isRunning}
            className="flex items-center space-x-2 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed text-white px-6 py-2 rounded-md font-medium transition-colors"
          >
            {isRunning ? <Loader2 className="w-5 h-5 animate-spin" /> : <Play className="w-5 h-5" />}
            <span>{isRunning ? "Running..." : "Launch Pipeline"}</span>
          </button>
        </div>
      </div>

      {/* Terminal View */}
      <div className="bg-black rounded-lg p-4 border border-slate-700 font-mono text-sm h-96 overflow-y-auto shadow-inner">
        <div className="text-slate-500 mb-4">// System Terminal Logs</div>
        {logs.map((log, i) => (
          <div key={i} className={`${
            log.includes("[ERROR]") ? "text-red-400" : 
            log.includes("[SYSTEM]") ? "text-green-400" : "text-slate-300"
          } whitespace-pre-wrap mb-1`}>
            <span className="text-slate-600 mr-2">{new Date().toLocaleTimeString()}</span>
            {log}
          </div>
        ))}
        <div ref={logsEndRef} />
      </div>
    </div>
  );
}
