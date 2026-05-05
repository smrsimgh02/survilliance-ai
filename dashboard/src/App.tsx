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
  AlertTriangle,
  Map as MapIcon,
  LayoutDashboard,
  History as HistoryIcon,
  X
} from 'lucide-react';
import { api, getWSUrl } from './lib/api';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';

// Fix Leaflet icon issue
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

let DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41]
});

L.Marker.prototype.options.icon = DefaultIcon;

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
  location?: string | null;
}

export default function App() {
  const [nodes, setNodes] = useState<Node[]>([]);
  const [activeNodeId, setActiveNodeId] = useState<string | null>(null);
  const [, setDetections] = useState<Detection[]>([]);
  const [wsStatus, setWsStatus] = useState<'connected' | 'disconnected' | 'connecting'>('connecting');
  const [totalCount, setTotalCount] = useState(0);
  const [latency, setLatency] = useState<number | string>('--');
  const [viewMode, setViewMode] = useState<'live' | 'map'>('live');
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [searchResults, setSearchResults] = useState<Detection[]>([]);
  const [searchQuery, setSearchQuery] = useState({ class_name: '', camera_id: '', start_date: '', end_date: '' });
  const [isSearching, setIsSearching] = useState(false);
  
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
    
    const interval = setInterval(fetchNodes, 10000);
    return () => clearInterval(interval);
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

  const handleSearch = async () => {
    setIsSearching(true);
    try {
      const params: any = {};
      if (searchQuery.class_name) params.class_name = searchQuery.class_name;
      if (searchQuery.camera_id) params.camera_id = searchQuery.camera_id;
      if (searchQuery.start_date) params.start_date = new Date(searchQuery.start_date).toISOString();
      if (searchQuery.end_date) params.end_date = new Date(searchQuery.end_date).toISOString();
      
      const res = await api.get('/detections/search', { params });
      setSearchResults(res.data);
    } catch (error) {
      console.error("Search failed:", error);
    } finally {
      setIsSearching(false);
    }
  };

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
              <span className="text-[10px] text-slate-500 font-medium">Auto-reconnect active • {new Date().toLocaleTimeString()}</span>
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
            <div className="flex bg-white/5 p-1 rounded-xl border border-white/5">
              <button 
                onClick={() => setViewMode('live')}
                className={`p-2 rounded-lg transition-all flex items-center gap-2 text-xs font-bold ${viewMode === 'live' ? 'bg-primary-accent text-white shadow-lg' : 'text-slate-400 hover:text-white'}`}
              >
                <LayoutDashboard size={16} /> LIVE
              </button>
              <button 
                onClick={() => setViewMode('map')}
                className={`p-2 rounded-lg transition-all flex items-center gap-2 text-xs font-bold ${viewMode === 'map' ? 'bg-primary-accent text-white shadow-lg' : 'text-slate-400 hover:text-white'}`}
              >
                <MapIcon size={16} /> MAP
              </button>
            </div>
            <div className="w-px h-8 bg-white/10 mx-2" />
            <button 
              onClick={() => setIsSearchOpen(true)}
              className="p-2 hover:bg-white/5 rounded-lg transition-colors text-slate-400"
            >
              <Search size={20} />
            </button>
            <button className="p-2 hover:bg-white/5 rounded-lg transition-colors text-slate-400">
              <Settings size={20} />
            </button>
          </div>
        </header>

        {/* Viewport */}
        <div className="flex-1 p-8 flex items-center justify-center relative bg-[radial-gradient(circle_at_center,#1e293b_0%,#020617_100%)]">
          {viewMode === 'live' ? (
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
                    src={activeNode?.url === "0" ? `http://localhost:8001/video_feed/${activeNodeId}` : activeNode?.url} 
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
          ) : (
            <div className="w-full h-full rounded-3xl overflow-hidden border-4 border-white/5 shadow-2xl relative">
              <MapContainer 
                center={[28.6139, 77.2090]} 
                zoom={13} 
                style={{ height: '100%', width: '100%', background: '#020617' }}
              >
                <TileLayer
                  url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
                />
                {nodes.map(node => {
                  const [lat, lng] = node.location ? node.location.split(',').map(Number) : [28.6139 + Math.random()*0.01, 77.2090 + Math.random()*0.01];
                  return (
                    <Marker key={node.id} position={[lat, lng]}>
                      <Popup>
                        <div className="p-2 min-w-[150px]">
                          <h3 className="font-bold text-slate-900 text-sm leading-tight mb-1">{node.name}</h3>
                          <div className="flex items-center gap-2 mb-3">
                            <div className={`w-1.5 h-1.5 rounded-full ${node.status === 'active' ? 'bg-emerald-500' : 'bg-slate-300'}`} />
                            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-tighter">{node.status}</span>
                          </div>
                          <button 
                            onClick={() => {
                              setActiveNodeId(node.id);
                              setViewMode('live');
                            }}
                            className="w-full bg-blue-600 hover:bg-blue-700 text-white py-1.5 rounded-lg text-[10px] font-bold transition-colors shadow-md"
                          >
                            OPEN LIVE FEED
                          </button>
                        </div>
                      </Popup>
                    </Marker>
                  );
                })}
              </MapContainer>
              <div className="absolute top-6 left-6 z-[1000] bg-black/60 backdrop-blur-md px-4 py-2 rounded-full border border-white/10">
                <span className="text-[10px] font-black tracking-widest">MAP NAVIGATION</span>
              </div>
            </div>
          )}
        </div>

        {/* Search Modal */}
        {isSearchOpen && (
          <div className="fixed inset-0 z-[2000] flex items-center justify-center p-8 bg-black/80 backdrop-blur-sm">
            <div className="bg-sidebar-bg w-full max-w-4xl max-h-[80vh] rounded-3xl border border-white/10 flex flex-col overflow-hidden shadow-2xl">
              <div className="p-6 border-b border-white/10 flex items-center justify-between bg-white/5">
                <div className="flex items-center gap-3">
                  <HistoryIcon className="text-primary-accent" />
                  <h2 className="font-bold text-lg italic tracking-tighter">Search Detection History</h2>
                </div>
                <button 
                  onClick={() => setIsSearchOpen(false)}
                  className="p-2 hover:bg-white/10 rounded-full transition-colors"
                >
                  <X size={24} />
                </button>
              </div>

              <div className="p-6 grid grid-cols-5 gap-4 border-b border-white/10">
                <div className="flex flex-col gap-2">
                  <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest px-2">Object Class</label>
                  <input 
                    type="text" 
                    placeholder="e.g. person, car"
                    value={searchQuery.class_name}
                    onChange={e => setSearchQuery({...searchQuery, class_name: e.target.value})}
                    className="bg-white/5 border border-white/10 p-3 rounded-xl focus:outline-none focus:border-primary-accent transition-all text-sm"
                  />
                </div>
                <div className="flex flex-col gap-2">
                  <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest px-2">Intelligence Source</label>
                  <select 
                    value={searchQuery.camera_id}
                    onChange={e => setSearchQuery({...searchQuery, camera_id: e.target.value})}
                    className="bg-white/5 border border-white/10 p-3 rounded-xl focus:outline-none focus:border-primary-accent transition-all text-sm appearance-none"
                  >
                    <option value="">All Sources</option>
                    {nodes.map(n => <option key={n.id} value={n.id}>{n.name}</option>)}
                  </select>
                </div>
                <div className="flex flex-col gap-2">
                  <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest px-2">Start Date</label>
                  <input 
                    type="datetime-local" 
                    value={searchQuery.start_date}
                    onChange={e => setSearchQuery({...searchQuery, start_date: e.target.value})}
                    className="bg-white/5 border border-white/10 p-3 rounded-xl focus:outline-none focus:border-primary-accent transition-all text-sm"
                  />
                </div>
                <div className="flex flex-col gap-2">
                  <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest px-2">End Date</label>
                  <input 
                    type="datetime-local" 
                    value={searchQuery.end_date}
                    onChange={e => setSearchQuery({...searchQuery, end_date: e.target.value})}
                    className="bg-white/5 border border-white/10 p-3 rounded-xl focus:outline-none focus:border-primary-accent transition-all text-sm"
                  />
                </div>
                <div className="flex flex-col gap-2 justify-end">
                  <button 
                    onClick={handleSearch}
                    disabled={isSearching}
                    className="bg-primary-accent hover:bg-blue-600 disabled:opacity-50 p-3 rounded-xl font-bold text-sm transition-all flex items-center justify-center gap-2"
                  >
                    {isSearching ? 'Searching...' : <><Search size={18} /> Run Analysis</>}
                  </button>
                </div>
              </div>

              <div className="flex-1 overflow-y-auto p-6">
                {searchResults.length > 0 ? (
                  <div className="grid grid-cols-2 gap-4">
                    {searchResults.map((res, i) => (
                      <div key={i} className="bg-white/5 border border-white/5 p-4 rounded-2xl flex items-center justify-between hover:bg-white/10 transition-all group">
                        <div className="flex items-center gap-4">
                          <div className="w-12 h-12 bg-primary-accent/10 rounded-xl flex items-center justify-center border border-primary-accent/20">
                            {res.class_name === 'person' ? <User className="text-primary-accent" /> : <Car className="text-primary-accent" />}
                          </div>
                          <div>
                            <h4 className="font-bold text-sm uppercase">{res.class_name}</h4>
                            <p className="text-[10px] text-slate-500 font-bold">{new Date(res.timestamp).toLocaleString()}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <span className="text-xs font-mono font-bold text-emerald-500">{(res.confidence * 100).toFixed(0)}%</span>
                          <p className="text-[10px] text-slate-500">Confidence</p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="h-full flex flex-col items-center justify-center text-slate-500 opacity-40 py-12">
                    <Search size={64} className="mb-4" />
                    <p className="font-bold uppercase tracking-widest">No matching signatures found</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

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
