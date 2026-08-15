import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, Cell } from 'recharts';
import { TrendingUp, Users, Target, Zap } from 'lucide-react';

export default function Analytics() {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetch('http://localhost:8000/api/analytics/summary')
      .then(res => res.json())
      .then(setData)
      .catch(console.error);
  }, []);

  if (!data) {
    return <div className="p-8 text-center text-slate-400">Loading Analytics...</div>;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Analytics & Conversion</h1>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {[
          { label: 'Total Discovered', value: data.funnel.discovered, icon: Users, color: 'text-blue-400', bg: 'bg-blue-400/10' },
          { label: 'High Priority', value: data.funnel.high_priority, icon: Zap, color: 'text-yellow-400', bg: 'bg-yellow-400/10' },
          { label: 'Pitches Sent', value: data.funnel.pitched, icon: Target, color: 'text-purple-400', bg: 'bg-purple-400/10' },
          { label: 'Total Replied', value: data.funnel.replied, icon: Target, color: 'text-pink-400', bg: 'bg-pink-400/10' },
          { label: 'Follow-ups Sent', value: data.funnel.follow_ups_sent, icon: Zap, color: 'text-orange-400', bg: 'bg-orange-400/10' },
          { label: 'Reply Rate', value: `${data.funnel.reply_rate}%`, icon: TrendingUp, color: 'text-green-400', bg: 'bg-green-400/10' },
        ].map((kpi, i) => (
          <div key={i} className="bg-slate-800 p-4 rounded-lg border border-slate-700 flex flex-col items-center justify-center text-center space-y-2 hover:bg-slate-700/50 transition-colors">
            <div className={`p-2 rounded-full ${kpi.bg}`}>
              <kpi.icon className={`w-5 h-5 ${kpi.color}`} />
            </div>
            <div>
              <div className="text-xl font-bold">{kpi.value}</div>
              <div className="text-xs text-slate-400">{kpi.label}</div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Funnel Chart */}
        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
          <h3 className="font-semibold text-lg mb-6">Pipeline Funnel</h3>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.stages} layout="vertical" margin={{ top: 5, right: 30, left: 40, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" horizontal={false} />
                <XAxis type="number" stroke="#94a3b8" />
                <YAxis dataKey="stage" type="category" stroke="#94a3b8" width={100} tick={{fontSize: 12}} />
                <RechartsTooltip cursor={{fill: '#334155'}} contentStyle={{backgroundColor: '#1e293b', borderColor: '#334155'}} />
                <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                  {data.stages.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={
                      entry.stage === 'WON' ? '#22c55e' : 
                      entry.stage === 'LOST' ? '#ef4444' : 
                      '#a855f7'
                    } />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Niche Breakdown */}
        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
          <h3 className="font-semibold text-lg mb-6">Leads by Niche</h3>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.niches}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                <XAxis dataKey="name" stroke="#94a3b8" tick={{fontSize: 12, textTransform: 'capitalize'}} />
                <YAxis stroke="#94a3b8" />
                <RechartsTooltip cursor={{fill: '#334155'}} contentStyle={{backgroundColor: '#1e293b', borderColor: '#334155'}} />
                <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
