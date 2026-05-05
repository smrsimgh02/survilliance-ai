import { useState, useEffect, useRef } from 'react';
import { 
  Shield, 
  Camera, 
  Search, 
  Settings, 
  Plus, 
  Wifi, 
  WifiOff,
  Clock,
  User,
  Car,
  AlertTriangle
} from 'lucide-react';
import { api, getWSUrl } from './lib/api';

interface Detection {
  camera_id: string;
  class_name: string;
  confidence: number;
  xcenter: number;
  ycenter: number;
  width: number;
  height: number;
  timestamp: string;
  ts?: number; // local timestamp for removal
}

interface Node {
  id: string;
  name: string;
  url: string;
  status: string;
}

export default function App() {
  const [nodes, setNodes] = useState<Node[]>([]);
  const [activeNodeId, setActiveNodeId] = useState<string | null>(null);
  const [, setDetections] = useState<Detection[]>([]);
  const [wsStatus, setWsStatus] = useState<'connected' | 'disconnected' | 'connecting'>('connecting');
  const [totalCount, setTotalCount] = useState(0);
  const [latency, setLatency] = useState<number | string>('--');
  
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<HTMLImageElement>(null);
  const detectionsRef = useRef<Detection[]>([]); // For immediate access in requestAnimationFrame

  // Fetch Nodes
  const fetchNodes = async () => {
    try {
      const res = await api.get('/cameras/');
      setNodes(res.data);
      if (res.data.length > 0 && !activeNodeId) {
        setActiveNodeId(res.data[0].id);
      }
    } catch (error) {
      console.error("Failed to fetch nodes:", error);
    }
  };

  useEffect(() => {
    fetchNodes();
    connectWS();
  }, []);

  const connectWS = () => {
    setWsStatus('connecting');
    const ws = new WebSocket(getWSUrl());

    ws.onopen = () => setWsStatus('connected');
    ws.onclose = () => {
      setWsStatus('disconnected');
      setTimeout(connectWS, 3000);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      const items = Array.isArray(data) ? data : [data];
      
      const now = Date.now();
      const newDetections = items
        .filter(d => d.class_name !== 'AI-HEARTBEAT')
        .map(d => ({ ...d, ts: now }));

      if (newDetections.length > 0) {
        setTotalCount(prev => prev + newDetections.length);
        
        // Calculate latency
        const first = newDetections[0];
        if (first.timestamp) {
          const diff = now - new Date(first.timestamp).getTime();
          setLatency(diff > 0 ? diff : 10);
        }

        // Update ref and state
        const updated = [...detectionsRef.current, ...newDetections].filter(d => (now - (d.ts || 0)) < 1000);
        detectionsRef.current = updated;
        setDetections(updated);
      }
    };
  };

  // Canvas Animation
  useEffect(() => {
    let animationId: number;
    
    const render = () => {
      const canvas = canvasRef.current;
      const img = streamRef.current;
      if (!canvas || !img || !img.complete || !img.naturalWidth) {
        animationId = requestAnimationFrame(render);
        return;
      }

      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      // Fit canvas to image
      const nw = img.naturalWidth;
      const nh = img.naturalHeight;
      const cw = img.clientWidth;
      const ch = img.clientHeight;
      
      const imageRatio = nw / nh;
      const containerRatio = cw / ch;
      
      let rw, rh;
      if (containerRatio > imageRatio) {
        rh = ch;
        rw = ch * imageRatio;
      } else {
        rw = cw;
        rh = cw / imageRatio;
      }

      if (canvas.width !== rw || canvas.height !== rh) {
        canvas.width = rw;
        canvas.height = rh;
      }

      ctx.clearRect(0, 0, rw, rh);
      
      const now = Date.now();
      
      detectionsRef.current.forEach(d => {
        if (d.camera_id !== activeNodeId) return;
        if (now - (d.ts || 0) > 800) return;

        const x = (d.xcenter - d.width/2) * rw;
        const y = (d.ycenter - d.height/2) * rh;
        const w = d.width * rw;
        const h = d.height * rh;

        // Draw Box
        ctx.strokeStyle = '#3b82f6';
        ctx.lineWidth = 2;
        ctx.strokeRect(x, y, w, h);

        // Label
        ctx.fillStyle = '#3b82f6';
        ctx.font = 'bold 10px Inter';
        const label = `${d.class_name.toUpperCase()} ${(d.confidence * 100).toFixed(0)}%`;
        const tw = ctx.measureText(label).width;
        ctx.fillRect(x, y - 15, tw + 10, 15);
        ctx.fillStyle = 'white';
        ctx.fillText(label, x + 5, y - 4);
      });

      animationId = requestAnimationFrame(render);
    };

    animationId = requestAnimationFrame(render);
    return () => cancelAnimationFrame(animationId);
  }, [activeNodeId, nodes]);

  const activeNode = nodes.find(n => n.id === activeNodeId);

  return (
    <div className="flex h-screen bg-main-bg text-white font-sans overflow-hidden">
      {/* Sidebar */}
      <aside className="w-72 bg-sidebar-bg border-r border-white/10 flex flex-col">
        <div className="p-6 border-b border-white/10 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Shield className="text-primary-accent w-6 h-6" />
            <h1 className="font-bold text-sm tracking-widest uppercase">Sentinel AI</h1>
          </div>
          <div className="bg-primary-accent/20 text-primary-accent text-[10px] px-2 py-1 rounded-full font-bold">
            {nodes.length} NODES
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          <h2 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest px-2">Active Sources</h2>
          {nodes.map(node => (
            <div 
              key={node.id}
              onClick={() => setActiveNodeId(node.id)}
              className={`p-4 rounded-xl cursor-pointer transition-all border ${
                activeNodeId === node.id 
                ? 'bg-primary-accent/10 border-primary-accent shadow-[0_0_20px_rgba(59,130,246,0.1)]' 
                : 'bg-white/5 border-white/5 hover:bg-white/10'
              }`}
            >
              <div className="flex justify-between items-center">
                <div className="flex flex-col">
                  <span className="text-sm font-semibold">{node.name}</span>
                  <span className="text-[10px] text-slate-400 font-mono">{node.id}</span>
                </div>
                <div className={`w-2 h-2 rounded-full ${node.status === 'active' ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]' : 'bg-slate-500'}`} />
              </div>
            </div>
          ))}
          
          <button className="w-full mt-4 p-4 rounded-xl border border-dashed border-white/10 text-slate-400 text-xs font-medium hover:text-white hover:border-white/30 transition-all flex items-center justify-center gap-2">
            <Plus size={16} /> Register New Source
          </button>
        </div>

        <div className="p-4 border-t border-white/10 bg-black/20">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg ${wsStatus === 'connected' ? 'bg-emerald-500/10 text-emerald-500' : 'bg-red-500/10 text-red-500'}`}>
              {wsStatus === 'connected' ? <Wifi size={18} /> : <WifiOff size={18} />}
            </div>
            <div className="flex flex-col">
              <span className="text-xs font-bold uppercase tracking-tighter">
                {wsStatus === 'connected' ? 'Hub Synchronized' : 'Hub Offline'}
              </span>
              <span className="text-[10px] text-slate-500 font-medium">Auto-reconnect active</span>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col">
        {/* Header */}
        <header className="h-20 bg-sidebar-bg/50 backdrop-blur-md border-b border-white/10 flex items-center justify-between px-8">
          <div className="flex items-center gap-4">
            <div className="bg-white/5 p-2 rounded-lg border border-white/5">
              <Camera size={20} className="text-slate-400" />
            </div>
            <div>
              <h2 className="font-bold text-lg">{activeNode?.name || 'SELECT A SOURCE'}</h2>
              <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">
                {activeNodeId ? `Uptime: 100% • ID: ${activeNodeId}` : 'Awaiting initialization'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex flex-col items-end">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-slate-400">LATENCY</span>
                <span className="text-xs font-mono font-bold text-primary-accent">{latency}ms</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-slate-400">DETECTIONS</span>
                <span className="text-xs font-mono font-bold text-emerald-500">{totalCount}</span>
              </div>
            </div>
            <div className="w-px h-8 bg-white/10 mx-2" />
            <button className="p-2 hover:bg-white/5 rounded-lg transition-colors text-slate-400">
              <Search size={20} />
            </button>
            <button className="p-2 hover:bg-white/5 rounded-lg transition-colors text-slate-400">
              <Settings size={20} />
            </button>
          </div>
        </header>

        {/* Viewport */}
        <div className="flex-1 p-8 flex items-center justify-center relative bg-[radial-gradient(circle_at_center,#1e293b_0%,#020617_100%)]">
          <div className="relative group max-w-[1200px] w-full aspect-video bg-black rounded-3xl overflow-hidden shadow-2xl border-4 border-white/5">
            {/* Scanline overlay */}
            <div className="absolute inset-0 pointer-events-none z-10 opacity-20" 
              style={{ background: 'linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.1) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.02), rgba(0, 255, 0, 0.01), rgba(0, 0, 255, 0.02))', backgroundSize: '100% 4px, 3px 100%' }} 
            />
            
            {/* HUD */}
            <div className="absolute top-6 left-6 z-20 flex items-center gap-3 bg-black/40 backdrop-blur-md px-4 py-2 rounded-full border border-white/10">
              <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
              <span className="text-[10px] font-black tracking-widest">LIVE FEED</span>
            </div>

            {activeNodeId ? (
              <>
                <img 
                  ref={streamRef}
                  src={activeNode?.url === "0" ? `http://localhost:8000/video_feed/${activeNodeId}` : activeNode?.url} 
                  className="w-full h-full object-contain"
                  alt="Stream"
                />
                <canvas 
                  ref={canvasRef}
                  className="absolute pointer-events-none z-20 left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2"
                />
              </>
            ) : (
              <div className="w-full h-full flex flex-col items-center justify-center text-slate-500 gap-4">
                <AlertTriangle size={48} className="opacity-20" />
                <span className="text-sm font-bold uppercase tracking-widest opacity-40">Select Intelligence Source</span>
              </div>
            )}
          </div>
        </div>

        {/* Bottom Bar / Quick Stats */}
        <footer className="h-16 border-t border-white/10 bg-sidebar-bg/30 flex items-center px-8 gap-12 overflow-x-auto">
          <div className="flex items-center gap-2 whitespace-nowrap">
            <User size={14} className="text-slate-500" />
            <span className="text-[10px] font-bold text-slate-400">LAST PERSON:</span>
            <span className="text-[10px] font-bold">12:45:01</span>
          </div>
          <div className="flex items-center gap-2 whitespace-nowrap">
            <Car size={14} className="text-slate-500" />
            <span className="text-[10px] font-bold text-slate-400">LAST VEHICLE:</span>
            <span className="text-[10px] font-bold">12:42:15</span>
          </div>
          <div className="flex items-center gap-2 whitespace-nowrap">
            <Clock size={14} className="text-slate-500" />
            <span className="text-[10px] font-bold text-slate-400">RECORDING DURATION:</span>
            <span className="text-[10px] font-bold">04:12:45</span>
          </div>
        </footer>
      </main>
    </div>
  );
}
