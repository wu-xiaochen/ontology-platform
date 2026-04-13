import React, { useState, useEffect } from 'react';
import { Layout, Brain, Activity, Shield, Code, Send, RefreshCcw, Database } from 'lucide-react';
import GraphView from './components/GraphView';
import ThinkingTrace from './components/ThinkingTrace';
import axios from 'axios';

// --- Mock Data for Initial UI ---
const initialNodes = [
  { id: '1', name: 'Clawra Core', type: 'Entity' },
  { id: '2', name: 'Ontology', type: 'Rule' },
  { id: '3', name: 'Reasoner', type: 'Process' },
];

const initialLinks = [
  { source: '1', target: '2', label: 'governs' },
  { source: '1', target: '3', label: 'drives' },
];

const App: React.FC = () => {
  const [inputText, setInputText] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [graphData, setGraphData] = useState({ nodes: initialNodes, links: initialLinks });
  const [traceSteps, setTraceSteps] = useState<any[]>([]);

  // 模拟发送学习/推理请求
  const handleAction = async (type: 'learn' | 'reason') => {
    if (!inputText) return;
    setIsProcessing(true);
    
    // 模拟添加推理每一步
    const steps = [
      { id: '4', type: 'perception', message: `接收输入: ${inputText.substring(0, 30)}...`, timestamp: new Date().toLocaleTimeString() },
      { id: '5', type: 'cognition', message: `解析领域语义并提取特征向量`, timestamp: new Date().toLocaleTimeString() },
      { id: '6', type: 'validation', message: `本体引擎校验: 未发现逻辑冲突`, timestamp: new Date().toLocaleTimeString() },
    ];
    setTraceSteps(prev => [...prev, ...steps]);

    try {
      // 实际调用 API
      const endpoint = type === 'learn' ? '/api/v4/learn' : '/api/v4/reason';
      // 注意：此处假设后端已经启动并监听 8000 端口
      // const response = await axios.post(`http://localhost:8000${endpoint}`, { content: inputText, query: inputText });
      
      // 模拟延迟
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      setTraceSteps(prev => [...prev, { 
        id: Date.now().toString(), 
        type: 'action', 
        message: type === 'learn' ? '知识已收录至持久化图谱' : '推理过程完成，结论置信度: 0.98', 
        timestamp: new Date().toLocaleTimeString() 
      }]);
    } catch (err) {
      console.error(err);
    } finally {
      setIsProcessing(false);
      setInputText('');
    }
  };

  return (
    <div className="dashboard-grid bg-[#0a0a0c] text-white">
      {/* Header */}
      <header className="col-span-3 glass flex items-center justify-between px-8">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/20">
            <Brain className="text-white w-6 h-6" />
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight">CLAWRA <span className="text-blue-500">v4.0</span></h1>
            <p className="text-[10px] text-white/40 uppercase tracking-widest font-semibold">Cognitive Agent Framework</p>
          </div>
        </div>

        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <span className="status-indicator status-online"></span>
            <span className="text-xs font-medium text-white/70">Engine Online</span>
          </div>
          <div className="h-4 w-px bg-white/10"></div>
          <RefreshCcw className="w-4 h-4 text-white/50 cursor-pointer hover:text-white transition-colors" />
        </div>
      </header>

      {/* Sidebar - Control Panel */}
      <aside className="glass col-start-1 row-start-2 flex flex-col p-6 gap-6">
        <div>
          <h2 className="text-sm font-semibold mb-4 flex items-center gap-2 text-blue-400">
            <Activity className="w-4 h-4" /> Interaction Lab
          </h2>
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="输入文本进行学习或提问推理..."
            className="w-full h-40 bg-black/40 border border-white/10 rounded-xl p-4 text-xs focus:outline-none focus:border-blue-500/50 transition-all resize-none"
          />
        </div>

        <div className="flex gap-3">
          <button 
            onClick={() => handleAction('learn')}
            disabled={isProcessing}
            className="flex-1 bg-white/5 hover:bg-white/10 border border-white/10 h-12 rounded-xl text-xs font-semibold flex items-center justify-center gap-2 transition-all active:scale-95"
          >
            <Database className="w-4 h-4" /> Learn
          </button>
          <button 
            onClick={() => handleAction('reason')}
            disabled={isProcessing}
            className="flex-1 bg-blue-600 hover:bg-blue-500 h-12 rounded-xl text-xs font-semibold flex items-center justify-center gap-2 transition-all shadow-lg shadow-blue-500/20 active:scale-95"
          >
            <Zap className="w-4 h-4 text-white" /> Reason
          </button>
        </div>

        <div className="mt-auto space-y-4">
          <div className="p-4 rounded-xl bg-green-500/5 border border-green-500/20">
             <div className="flex items-center gap-2 mb-2">
                <Shield className="w-4 h-4 text-green-500" />
                <span className="text-[10px] font-bold text-green-500 uppercase">Logic Guard</span>
             </div>
             <p className="text-[11px] text-white/60 leading-relaxed">本体引擎实时监控中，当前发现 0 个逻辑矛盾。</p>
          </div>
        </div>
      </aside>

      {/* Main View - 3D Graph */}
      <main className="col-start-2 row-start-2">
        <GraphView data={graphData} />
      </main>

      {/* Right Panel - Thinking Trace */}
      <aside className="glass col-start-3 row-start-2 overflow-hidden">
        <ThinkingTrace steps={traceSteps} />
      </aside>
    </div>
  );
};

export default App;
