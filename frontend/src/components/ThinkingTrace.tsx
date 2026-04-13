import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Brain, ShieldCheck, Zap, AlertCircle } from 'lucide-react';

interface TraceStep {
  id: string;
  type: 'perception' | 'cognition' | 'validation' | 'action';
  message: string;
  timestamp: string;
}

interface ThinkingTraceProps {
  steps: TraceStep[];
}

const ThinkingTrace: React.FC<ThinkingTraceProps> = ({ steps }) => {
  const getIcon = (type: TraceStep['type']) => {
    switch (type) {
      case 'perception': return <Zap className="w-4 h-4 text-blue-400" />;
      case 'cognition': return <Brain className="w-4 h-4 text-purple-400" />;
      case 'validation': return <ShieldCheck className="w-4 h-4 text-green-400" />;
      case 'action': return <AlertCircle className="w-4 h-4 text-orange-400" />;
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b border-white/10 flex items-center justify-between">
        <h3 className="text-sm font-semibold tracking-wide uppercase flex items-center gap-2">
          <Brain className="w-4 h-4" /> Cognitive Trace
        </h3>
        <span className="text-[10px] bg-blue-500/20 text-blue-400 px-2 py-0.5 rounded-full border border-blue-500/30">
          Live
        </span>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <AnimatePresence initial={false}>
          {steps.map((step, index) => (
            <motion.div
              key={step.id}
              initial={{ opacity: 0, x: -20, scale: 0.95 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              transition={{ duration: 0.4, ease: "easeOut" }}
              className="flex gap-3 relative"
            >
              {index !== steps.length - 1 && (
                <div className="absolute left-[7px] top-6 bottom-[-16px] w-[2px] bg-white/5" />
              )}
              
              <div className="z-10 bg-gray-900 border border-white/10 rounded-full p-1 h-fit">
                {getIcon(step.type)}
              </div>
              
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] font-mono text-white/50">{step.timestamp}</span>
                </div>
                <div className="glass p-3 text-xs leading-relaxed text-white/90 glass-hover">
                  {step.message}
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default ThinkingTrace;
