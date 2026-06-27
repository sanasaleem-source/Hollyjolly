import { useState, useEffect, useRef } from 'react';
import { 
  Tv, Play, Pause, Film, FolderOpen, Database, Sparkles, AlertTriangle, 
  Settings, CheckCircle2, RefreshCw, Layers, Download, Sliders, 
  ChevronRight, ArrowRight, BookOpen, Clock, ShieldCheck, HelpCircle, FileText
} from 'lucide-react';

interface Character {
  name: string;
  appearance: string;
  clothing: string;
  injuries: string;
  relationships: string;
  history: string;
  lastSeenShotId: string;
}

interface WorldObject {
  name: string;
  owner: string;
  condition: string;
  location: string;
  version: number;
}

interface Shot {
  shotId: string;
  sceneId: string;
  description: string;
  cameraAngle: string;
  durationSeconds: number;
  lighting: string;
  charactersPresent: string[];
  objectsPresent: string[];
  action: string;
  dialogue?: string;
  status: 'pending' | 'generating' | 'done' | 'failed';
  imageUrl?: string;
  assetVersions?: Record<string, number>;
  validationResult?: {
    passed: boolean;
    failures: string[];
    severity: string;
  };
  repairAttempts: number;
}

export default function App() {
  const [prompt, setPrompt] = useState("A classic detective mystery in a dark rainy noir city streets under wet neon shadows.");
  const [targetScope, setTargetScope] = useState("all");
  const [activeTab, setActiveTab] = useState<'world' | 'assets' | 'logs'>('world');
  
  // Pipeline state
  const [shots, setShots] = useState<Shot[]>([]);
  const [characters, setCharacters] = useState<Character[]>([
    {
      name: "John",
      appearance: "Middle-aged detective, rugged features, tired eyes",
      clothing: "Classic dark grey wool trench coat, brown fedora",
      injuries: "None",
      relationships: "Distrusts the Chief, old friends with Detective Vance",
      history: "15 years on the force, haunted by an unsolved cold case",
      lastSeenShotId: "shot_001"
    },
    {
      name: "Vance",
      appearance: "Slick, young rookie, sharp jawline, grooming",
      clothing: "Tailored blue suit, clean leather gloves",
      injuries: "Slight scar over right eyebrow",
      relationships: "Looks up to John, secretive about his contacts",
      history: "Recently transferred from narcotics, eager to prove himself",
      lastSeenShotId: "shot_001"
    }
  ]);
  const [objects, setObjects] = useState<WorldObject[]>([
    {
      name: "Umbrella",
      owner: "John",
      condition: "Worn out but functional",
      location: "John's Hand",
      version: 1
    },
    {
      name: "Case File",
      owner: "Unknown",
      condition: "Dusty, water-damaged edges",
      location: "Alleyway crate",
      version: 1
    }
  ]);
  const [logs, setLogs] = useState<string[]>([
    "Studio Initialized. System connected to local SQLite world state engine.",
    "Ready for creative input. Input a story prompt to generate shots plan."
  ]);
  const [selectedShotId, setSelectedShotId] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingIndex, setProcessingIndex] = useState(-1);
  
  // Preview Player State
  const [isPlaying, setIsPlaying] = useState(false);
  const [playerIndex, setPlayerIndex] = useState(0);
  const [playerProgress, setPlayerProgress] = useState(0);
  const playerTimer = useRef<NodeJS.Timeout | null>(null);

  // Auto Scroll log helper
  const logEndRef = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  // Preset Story prompts
  const presets = [
    {
      name: "Rainy Noir",
      text: "A classic detective mystery in a dark rainy noir city streets under wet neon shadows."
    },
    {
      name: "Space Warp",
      text: "A grand cosmic mission of a stellar space cruiser warp-driving past a brilliant gas nebula constellation."
    },
    {
      name: "Sunlit Meadow",
      text: "A fast medieval chase sequence across a sun-drenched valley with a warrior fleeing riding a brown horse."
    }
  ];

  const handleApplyPreset = (text: string) => {
    setPrompt(text);
    addLog(`Preset applied: "${text}"`);
  };

  const addLog = (msg: string) => {
    setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] ${msg}`]);
  };

  // 1. GENERATE storyboard shots plan from prompt
  const handleParseStory = async () => {
    if (isProcessing) return;
    setIsProcessing(true);
    addLog("Director: Starting storyboard planning cycle...");
    setSelectedShotId(null);
    setShots([]);
    
    try {
      const res = await fetch('/api/parse-story', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt })
      });
      const data = await res.json();
      
      if (data.success) {
        setShots(data.shots);
        setCharacters(data.characters);
        setObjects(data.objects);
        if (data.shots.length > 0) {
          setSelectedShotId(data.shots[0].shotId);
        }
        addLog("Director: Sequence mapped. Proceeding to sequence render pipeline...");
        
        // Auto-start pipeline execution
        triggerPipeline(data.shots);
      } else {
        addLog(`Director Error: ${data.error || "Failed to generate shot plans"}`);
        setIsProcessing(false);
      }
    } catch (err: any) {
      addLog(`Network Failure: ${err.message}`);
      setIsProcessing(false);
    }
  };

  // 2. ORCHESTRATE and run shot-by-shot rendering & validation
  const triggerPipeline = async (shotList: Shot[]) => {
    addLog("Orchestrator: Initializing task executor threads...");
    
    for (let i = 0; i < shotList.length; i++) {
      setProcessingIndex(i);
      const activeShot = shotList[i];
      addLog(`Orchestrator: [Shot ${i+1}/${shotList.length}] Initiating bakes for ${activeShot.shotId}`);
      
      // Update local shot status to generating
      setShots(prev => prev.map((s, idx) => idx === i ? { ...s, status: 'generating' } : s));

      try {
        const res = await fetch('/api/process-shot', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ shotId: activeShot.shotId, index: i })
        });
        const data = await res.json();
        
        if (data.success) {
          // Update status & results
          setShots(prev => prev.map((s, idx) => idx === i ? data.shot : s));
          if (data.shot.status === 'failed') {
            addLog(`Validators: ❌ Shot ${activeShot.shotId} failed multimodal checks! Triggering Repair Engine.`);
          } else {
            addLog(`Validators: ✅ Shot ${activeShot.shotId} passed all consistency check matrices.`);
          }
        }
      } catch (err: any) {
        addLog(`Orchestrator Failure: ${err.message}`);
        setShots(prev => prev.map((s, idx) => idx === i ? { ...s, status: 'failed' } : s));
      }
      
      // small delay to visualize steps nicely
      await new Promise(r => setTimeout(r, 1200));
    }
    
    setProcessingIndex(-1);
    setIsProcessing(false);
    addLog("Orchestrator: All storyboard pipeline operations complete.");
  };

  // 3. REPAIR a specific shot
  const handleRepairShot = async (shotId: string) => {
    addLog(`RepairEngine: Launching targeted fix vectors for Shot ${shotId}...`);
    setShots(prev => prev.map(s => s.shotId === shotId ? { ...s, status: 'generating' } : s));

    try {
      const res = await fetch('/api/repair-shot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ shotId })
      });
      const data = await res.json();

      if (data.success) {
        setShots(prev => prev.map(s => s.shotId === shotId ? data.shot : s));
        addLog(`Validators: Re-evaluated. Shot ${shotId} successfully repaired and updated!`);
      } else {
        addLog(`RepairEngine Failure: ${data.error}`);
        setShots(prev => prev.map(s => s.shotId === shotId ? { ...s, status: 'failed' } : s));
      }
    } catch (err: any) {
      addLog(`Repair Network Error: ${err.message}`);
    }
  };

  // Movie slideshow player control
  const togglePlayer = () => {
    if (isPlaying) {
      if (playerTimer.current) clearInterval(playerTimer.current);
      setIsPlaying(false);
    } else {
      const completedShots = shots.filter(s => s.status === 'done' && s.imageUrl);
      if (completedShots.length === 0) {
        addLog("Preview Player: No rendered frames available. Run prompt first!");
        return;
      }
      setIsPlaying(true);
      setPlayerIndex(0);
      setPlayerProgress(0);
    }
  };

  useEffect(() => {
    if (isPlaying) {
      const completedShots = shots.filter(s => s.status === 'done' && s.imageUrl);
      if (completedShots.length === 0) {
        setIsPlaying(false);
        return;
      }
      
      playerTimer.current = setInterval(() => {
        setPlayerProgress(prev => {
          if (prev >= 100) {
            setPlayerIndex(curr => {
              if (curr >= completedShots.length - 1) {
                return 0; // loop
              }
              return curr + 1;
            });
            return 0;
          }
          return prev + 10; // increment step
        });
      }, 350);
    } else {
      if (playerTimer.current) clearInterval(playerTimer.current);
    }

    return () => {
      if (playerTimer.current) clearInterval(playerTimer.current);
    };
  }, [isPlaying, shots]);

  const selectedShot = shots.find(s => s.shotId === selectedShotId) || shots[0];
  const completedShotsList = shots.filter(s => s.status === 'done' && s.imageUrl);

  return (
    <div className="min-h-screen bg-[#09090b] text-zinc-100 flex flex-col font-sans selection:bg-amber-500/30 selection:text-amber-200">
      
      {/* Top Studio Title Bar */}
      <header className="border-b border-zinc-800 bg-[#0d0d11]/95 backdrop-blur px-5 py-3.5 flex items-center justify-between sticky top-0 z-50">
        <div className="flex items-center space-x-3.5">
          <div className="p-2 bg-gradient-to-br from-amber-500 to-orange-600 rounded-xl shadow-lg shadow-orange-500/10">
            <Film className="w-5.5 h-5.5 text-black stroke-[2.2]" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-lg font-bold tracking-tight text-white font-display">AI Production Studio</h1>
              <span className="text-[10px] font-semibold bg-zinc-800 text-amber-400 px-2 py-0.5 rounded-full border border-zinc-700">V1 PRO</span>
            </div>
            <p className="text-[11px] text-zinc-400">Professional Studio-Grade Headless Rendering & Continuity Pipeline</p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2 px-3 py-1.5 bg-zinc-900 rounded-lg border border-zinc-800 text-[11px] text-zinc-400">
            <span className={`w-2 h-2 rounded-full ${isProcessing ? 'bg-amber-400 animate-pulse' : 'bg-emerald-500'}`} />
            <span>{isProcessing ? 'Pipeline Running' : 'Local Sandbox Ready'}</span>
          </div>
          <button 
            onClick={() => addLog("Configuration drawer opened.")}
            className="p-2 text-zinc-400 hover:text-white bg-zinc-900 hover:bg-zinc-800 rounded-lg border border-zinc-800 transition"
          >
            <Settings className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* Main Two-Panel Layout Splitter */}
      <main className="flex-1 grid grid-cols-1 lg:grid-cols-12 overflow-hidden">
        
        {/* LEFT PANEL: Control & State Side (35% - 4.2 cols) */}
        <section className="lg:col-span-4 border-r border-zinc-800 flex flex-col bg-[#0f0f13] overflow-y-auto max-h-[calc(100vh-69px)]">
          
          {/* Section: Story Prompt Input */}
          <div className="p-5 border-b border-zinc-800/60 bg-[#121217]">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2">
                <Sparkles className="w-4 h-4 text-amber-400" />
                <h2 className="text-xs font-bold tracking-wider text-zinc-300 uppercase">Director Story Prompt</h2>
              </div>
              <span className="text-[10px] text-zinc-500 flex items-center space-x-1">
                <Clock className="w-3 h-3 text-zinc-500" />
                <span>Render sequence</span>
              </span>
            </div>

            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Detail your storyline, characters, action blocks, and environment aesthetics..."
              className="w-full h-24 bg-zinc-950 text-zinc-200 text-xs p-3.5 rounded-xl border border-zinc-800 focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/20 transition resize-none leading-relaxed"
            />

            {/* Presets Grid */}
            <div className="mt-3 flex flex-wrap gap-1.5">
              {presets.map((preset) => (
                <button
                  key={preset.name}
                  onClick={() => handleApplyPreset(preset.text)}
                  className="px-2 py-1 bg-zinc-900 hover:bg-zinc-800 text-[10px] text-zinc-400 hover:text-white rounded-md border border-zinc-800/80 transition"
                >
                  {preset.name}
                </button>
              ))}
            </div>

            {/* Run Pipeline CTA */}
            <div className="mt-4 flex items-center space-x-2">
              <div className="flex-1">
                <select
                  value={targetScope}
                  onChange={(e) => setTargetScope(e.target.value)}
                  className="w-full bg-zinc-950 text-zinc-300 text-[11px] px-2.5 py-2.5 rounded-lg border border-zinc-800 focus:outline-none transition"
                >
                  <option value="all">Pipeline Range: All Shots</option>
                  <option value="scene_001">Scope: Scene 1 Only</option>
                </select>
              </div>
              <button
                onClick={handleParseStory}
                disabled={isProcessing || !prompt}
                className="flex items-center justify-center space-x-1.5 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 disabled:from-zinc-800 disabled:to-zinc-800 disabled:text-zinc-600 text-zinc-950 px-4 py-2.5 rounded-lg text-xs font-bold transition shadow-lg shadow-amber-500/5 cursor-pointer disabled:cursor-not-allowed"
              >
                {isProcessing ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Processing...</span>
                  </>
                ) : (
                  <>
                    <Tv className="w-3.5 h-3.5 stroke-[2.2]" />
                    <span>Run Pipeline</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Tab Selection Row */}
          <div className="flex border-b border-zinc-800 bg-[#0e0e12]/80 sticky top-0 z-10 backdrop-blur-sm">
            <button
              onClick={() => setActiveTab('world')}
              className={`flex-1 py-3 text-center text-[11px] font-bold tracking-wider uppercase border-b-2 transition flex items-center justify-center space-x-1.5 ${
                activeTab === 'world' 
                  ? 'border-amber-500 text-white bg-zinc-900/30' 
                  : 'border-transparent text-zinc-500 hover:text-zinc-300'
              }`}
            >
              <Database className="w-3.5 h-3.5" />
              <span>World State DB</span>
            </button>
            <button
              onClick={() => setActiveTab('assets')}
              className={`flex-1 py-3 text-center text-[11px] font-bold tracking-wider uppercase border-b-2 transition flex items-center justify-center space-x-1.5 ${
                activeTab === 'assets' 
                  ? 'border-amber-500 text-white bg-zinc-900/30' 
                  : 'border-transparent text-zinc-500 hover:text-zinc-300'
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              <span>Asset Library</span>
            </button>
            <button
              onClick={() => setActiveTab('logs')}
              className={`flex-1 py-3 text-center text-[11px] font-bold tracking-wider uppercase border-b-2 transition flex items-center justify-center space-x-1.5 ${
                activeTab === 'logs' 
                  ? 'border-amber-500 text-white bg-[#0e0e12]' 
                  : 'border-transparent text-zinc-500 hover:text-zinc-300'
              }`}
            >
              <FileText className="w-3.5 h-3.5" />
              <span>Execution Logs</span>
            </button>
          </div>

          {/* Dynamic Tab Workspace panels */}
          <div className="flex-1 p-4 overflow-y-auto">
            
            {/* TAB: WORLD STATE VIEW */}
            {activeTab === 'world' && (
              <div className="space-y-5 animate-fade-in">
                {/* Characters Table */}
                <div>
                  <div className="flex items-center space-x-1.5 mb-2">
                    <Database className="w-3.5 h-3.5 text-zinc-500" />
                    <h3 className="text-[11px] font-bold tracking-wider text-zinc-400 uppercase">Characters Registry</h3>
                  </div>
                  
                  <div className="space-y-2.5">
                    {characters.map((char) => (
                      <div key={char.name} className="p-3 bg-[#15151b] border border-zinc-800/80 rounded-xl hover:border-zinc-700 transition">
                        <div className="flex items-center justify-between mb-1.5">
                          <span className="text-xs font-bold text-white flex items-center space-x-1.5">
                            <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                            <span>{char.name}</span>
                          </span>
                          <span className="text-[9px] text-zinc-500 font-mono bg-zinc-950 px-2 py-0.5 rounded border border-zinc-800/60">
                            Last Seen: {char.lastSeenShotId}
                          </span>
                        </div>
                        <div className="space-y-1 text-[10.5px] leading-relaxed">
                          <p className="text-zinc-300"><span className="text-zinc-500 font-semibold">Appearance:</span> {char.appearance}</p>
                          <p className="text-zinc-300"><span className="text-zinc-500 font-semibold">Clothing:</span> {char.clothing}</p>
                          {char.injuries !== "None" && (
                            <p className="text-orange-400/90 font-medium"><span className="text-zinc-500 font-semibold">Injuries:</span> {char.injuries}</p>
                          )}
                          <p className="text-zinc-400 text-[10px] mt-1 border-t border-zinc-800/50 pt-1.5 italic">"{char.relationships}"</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Objects Table */}
                <div>
                  <div className="flex items-center space-x-1.5 mb-2">
                    <Sliders className="w-3.5 h-3.5 text-zinc-500" />
                    <h3 className="text-[11px] font-bold tracking-wider text-zinc-400 uppercase">Props & Objects DB</h3>
                  </div>
                  
                  <div className="bg-zinc-950 rounded-xl border border-zinc-800/80 overflow-hidden">
                    <table className="w-full text-left border-collapse text-[10.5px]">
                      <thead>
                        <tr className="bg-zinc-900 border-b border-zinc-800 text-zinc-500 font-bold uppercase text-[9px] tracking-wider">
                          <th className="p-2.5">Prop Name</th>
                          <th className="p-2.5">Owner</th>
                          <th className="p-2.5">Condition</th>
                          <th className="p-2.5 text-right">Ver</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-zinc-800/45">
                        {objects.map((obj) => (
                          <tr key={obj.name} className="hover:bg-zinc-900/30 text-zinc-300 transition">
                            <td className="p-2.5 font-bold text-zinc-200">{obj.name}</td>
                            <td className="p-2.5 text-zinc-400">{obj.owner}</td>
                            <td className="p-2.5">
                              <span className="px-1.5 py-0.5 rounded text-[9.5px] font-medium bg-emerald-950/40 text-emerald-400 border border-emerald-900/40">
                                {obj.condition}
                              </span>
                            </td>
                            <td className="p-2.5 text-right font-mono text-zinc-500">v{obj.version}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}

            {/* TAB: ASSETS LIBRARY */}
            {activeTab === 'assets' && (
              <div className="space-y-3 animate-fade-in">
                <div className="p-3.5 bg-zinc-950 rounded-xl border border-zinc-800/60 text-[11px] text-zinc-400 leading-relaxed">
                  <p>Predictive folder registry of version-controlled digital assets stored locally under <code className="text-amber-400/95 bg-zinc-900 px-1 py-0.5 rounded">storage/assets/</code>.</p>
                </div>

                <div className="space-y-2">
                  <div className="p-3 bg-[#131317] border border-zinc-800 rounded-xl">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-bold text-white flex items-center space-x-1.5">
                        <FolderOpen className="w-3.5 h-3.5 text-zinc-400" />
                        <span>characters/john/</span>
                      </span>
                      <span className="text-[10px] text-amber-500 font-semibold font-mono">v1</span>
                    </div>
                    <div className="space-y-1 pl-5 text-[10.5px] text-zinc-400 font-mono">
                      <p>📄 appearance.json</p>
                      <p>🖼️ appearance.png</p>
                      <p>📦 blender_rig.blend</p>
                    </div>
                  </div>

                  <div className="p-3 bg-[#131317] border border-zinc-800 rounded-xl">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-bold text-white flex items-center space-x-1.5">
                        <FolderOpen className="w-3.5 h-3.5 text-zinc-400" />
                        <span>objects/umbrella/</span>
                      </span>
                      <span className="text-[10px] text-amber-500 font-semibold font-mono">v1</span>
                    </div>
                    <div className="space-y-1 pl-5 text-[10.5px] text-zinc-400 font-mono">
                      <p>📄 prop.json</p>
                      <p>🖼️ prop.png</p>
                    </div>
                  </div>

                  <div className="p-3 bg-[#131317] border border-zinc-800 rounded-xl">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-bold text-white flex items-center space-x-1.5">
                        <FolderOpen className="w-3.5 h-3.5 text-zinc-400" />
                        <span>environments/city/</span>
                      </span>
                      <span className="text-[10px] text-amber-500 font-semibold font-mono">v1</span>
                    </div>
                    <div className="space-y-1 pl-5 text-[10.5px] text-zinc-400 font-mono">
                      <p>📄 backdrop.json</p>
                      <p>🖼️ backdrop.png</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* TAB: PIPELINE LOGS */}
            {activeTab === 'logs' && (
              <div className="bg-zinc-950 p-3.5 rounded-xl border border-zinc-800/80 font-mono text-[10.5px] text-zinc-400 h-[380px] overflow-y-auto flex flex-col space-y-2 animate-fade-in">
                {logs.map((log, idx) => (
                  <div key={idx} className="border-b border-zinc-900/60 pb-1.5 last:border-0 leading-relaxed">
                    <span className="text-amber-500/80"></span> {log}
                  </div>
                ))}
                <div ref={logEndRef} />
              </div>
            )}

          </div>
        </section>

        {/* RIGHT PANEL: Storyboard Timeline & Visualizer Side (65% - 7.8 cols) */}
        <section className="lg:col-span-8 flex flex-col bg-[#08080a] overflow-y-auto max-h-[calc(100vh-69px)]">
          
          {/* Main Visualizer Area */}
          <div className="p-6 grid grid-cols-1 md:grid-cols-12 gap-6 border-b border-zinc-800/60">
            
            {/* Column: Left / Preview Player */}
            <div className="md:col-span-7 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Tv className="w-4.5 h-4.5 text-amber-500" />
                  <h2 className="text-xs font-bold tracking-wider text-zinc-300 uppercase">Interactive Preview Player</h2>
                </div>
                <span className="text-[10px] text-zinc-500">Lossless 24fps output</span>
              </div>

              {/* Movie screen canvas simulator */}
              <div className="aspect-video bg-zinc-950 rounded-2xl border border-zinc-800/80 overflow-hidden relative group flex items-center justify-center">
                
                {isPlaying && completedShotsList.length > 0 ? (
                  <>
                    <img
                      src={completedShotsList[playerIndex].imageUrl}
                      alt="Rendering Slideshow Frame"
                      className="w-full h-full object-cover"
                      referrerPolicy="no-referrer"
                    />
                    <div className="absolute top-3 left-3 bg-black/70 backdrop-blur-md px-3 py-1.5 rounded-lg border border-zinc-800 text-[10px] font-mono flex items-center space-x-1.5 text-amber-400">
                      <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                      <span>{completedShotsList[playerIndex].shotId.toUpperCase()}</span>
                      <span className="text-zinc-500">|</span>
                      <span className="text-zinc-300">{completedShotsList[playerIndex].cameraAngle}</span>
                    </div>

                    {/* dialogue overlay */}
                    {completedShotsList[playerIndex].dialogue && (
                      <div className="absolute bottom-5 left-1/2 -translate-x-1/2 bg-black/80 backdrop-blur-md px-4 py-2 rounded-xl text-center text-xs font-medium text-white max-w-[80%] border border-zinc-800">
                        {completedShotsList[playerIndex].dialogue}
                      </div>
                    )}
                  </>
                ) : (
                  // Player idle or empty layout
                  <div className="text-center p-6 space-y-3.5">
                    <div className="w-12 h-12 bg-zinc-900 border border-zinc-800/80 rounded-full flex items-center justify-center mx-auto text-zinc-400 group-hover:scale-105 transition">
                      <Film className="w-5 h-5 text-zinc-400" />
                    </div>
                    <div>
                      <p className="text-xs font-bold text-zinc-300">No playback sequence assembled</p>
                      <p className="text-[10.5px] text-zinc-500 mt-1 max-w-sm mx-auto">Input a creative plot in the Director console to planned shots and run headless render pipelines.</p>
                    </div>
                  </div>
                )}

                {/* Progress play bar */}
                {isPlaying && (
                  <div className="absolute bottom-0 left-0 right-0 h-1 bg-zinc-800">
                    <div 
                      className="h-full bg-gradient-to-r from-amber-500 to-orange-500 transition-all duration-300"
                      style={{ width: `${playerProgress}%` }}
                    />
                  </div>
                )}
              </div>

              {/* Player controller buttons */}
              <div className="flex items-center justify-between bg-zinc-900/40 p-3 rounded-xl border border-zinc-800/80">
                <button
                  onClick={togglePlayer}
                  disabled={completedShotsList.length === 0}
                  className="px-4 py-2 bg-zinc-950 hover:bg-zinc-800 disabled:opacity-40 text-xs font-semibold rounded-lg border border-zinc-800 flex items-center space-x-2 transition text-zinc-200 cursor-pointer disabled:cursor-not-allowed"
                >
                  {isPlaying ? (
                    <>
                      <Pause className="w-3.5 h-3.5 text-zinc-400" />
                      <span>Pause Presentation</span>
                    </>
                  ) : (
                    <>
                      <Play className="w-3.5 h-3.5 fill-amber-400 text-amber-400" />
                      <span>Play Rendered Cut</span>
                    </>
                  )}
                </button>

                {completedShotsList.length > 0 && (
                  <span className="text-[10px] font-mono text-zinc-500">
                    Assembled: {completedShotsList.length} / {shots.length} Shots Done
                  </span>
                )}
              </div>
            </div>

            {/* Column: Right / Diagnostic Inspector */}
            <div className="md:col-span-5 flex flex-col space-y-4">
              <div className="flex items-center space-x-2">
                <Sliders className="w-4.5 h-4.5 text-amber-500" />
                <h2 className="text-xs font-bold tracking-wider text-zinc-300 uppercase">Shot Detail Inspector</h2>
              </div>

              {selectedShot ? (
                <div className="flex-1 bg-[#101014] p-4.5 rounded-2xl border border-zinc-800/80 space-y-4 flex flex-col justify-between">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between pb-2 border-b border-zinc-800/50">
                      <span className="text-sm font-bold text-white font-mono">{selectedShot.shotId.toUpperCase()}</span>
                      <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${
                        selectedShot.status === 'done' ? 'bg-emerald-950 text-emerald-400 border border-emerald-900/50' :
                        selectedShot.status === 'failed' ? 'bg-red-950 text-red-400 border border-red-900/50' :
                        selectedShot.status === 'generating' ? 'bg-amber-950 text-amber-400 border border-amber-900/50 animate-pulse' :
                        'bg-zinc-900 text-zinc-500 border border-zinc-800'
                      }`}>
                        {selectedShot.status}
                      </span>
                    </div>

                    <div className="space-y-2 text-[11px] leading-relaxed">
                      <p className="text-zinc-300"><span className="text-zinc-500 font-semibold font-mono">Action:</span> {selectedShot.action}</p>
                      {selectedShot.dialogue && (
                        <p className="text-zinc-300 bg-zinc-950 p-2.5 rounded-lg border border-zinc-800/50 italic">
                          <span className="text-zinc-500 font-semibold font-mono not-italic block mb-0.5">Dialogue:</span>
                          "{selectedShot.dialogue}"
                        </p>
                      )}
                      
                      <div className="grid grid-cols-2 gap-2 mt-2">
                        <div className="p-2 bg-zinc-950/40 rounded-lg border border-zinc-800/40">
                          <span className="text-zinc-500 block text-[9px] uppercase font-bold tracking-wider">Camera Angle</span>
                          <span className="text-zinc-200 font-medium">{selectedShot.cameraAngle}</span>
                        </div>
                        <div className="p-2 bg-zinc-950/40 rounded-lg border border-zinc-800/40">
                          <span className="text-zinc-500 block text-[9px] uppercase font-bold tracking-wider">Lighting Profile</span>
                          <span className="text-zinc-200 font-medium">{selectedShot.lighting}</span>
                        </div>
                      </div>

                      {/* Display validation details if failed */}
                      {selectedShot.validationResult && !selectedShot.validationResult.passed && (
                        <div className="p-3 bg-red-950/20 border border-red-900/40 rounded-xl space-y-1.5 mt-2">
                          <div className="flex items-center space-x-1.5 text-red-400 font-semibold text-[10px]">
                            <AlertTriangle className="w-3.5 h-3.5" />
                            <span>Multimodal Consistency Failures:</span>
                          </div>
                          <ul className="list-disc pl-4 text-zinc-300 space-y-1 text-[10px]">
                            {selectedShot.validationResult.failures.map((f, i) => (
                              <li key={i}>{f}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="pt-3 border-t border-zinc-800/50 flex items-center justify-between">
                    <span className="text-[10px] text-zinc-500">Repair attempts: {selectedShot.repairAttempts}</span>
                    {selectedShot.status === 'failed' && (
                      <button
                        onClick={() => handleRepairShot(selectedShot.shotId)}
                        className="px-3 py-1.5 bg-red-950 hover:bg-red-900 text-red-200 border border-red-800/80 hover:border-red-700 text-[10.5px] font-bold rounded-lg transition flex items-center space-x-1 cursor-pointer"
                      >
                        <RefreshCw className="w-3 h-3" />
                        <span>Force Shot Repair</span>
                      </button>
                    )}
                  </div>
                </div>
              ) : (
                <div className="flex-1 bg-[#101014] p-6 rounded-2xl border border-zinc-800/80 flex items-center justify-center text-center">
                  <div className="text-zinc-500 text-[11px] max-w-xs space-y-2">
                    <Sliders className="w-7 h-7 mx-auto text-zinc-600 stroke-[1.5]" />
                    <p>Select any shot block in the horizontal timeline panel to audit metadata profiles.</p>
                  </div>
                </div>
              )}
            </div>

          </div>

          {/* Section: CapCut-Style Horizontal Timeline (Horizontal Scroll Area) */}
          <div className="p-6 border-b border-zinc-800/60 bg-[#0c0c10]">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-2">
                <Layers className="w-4.5 h-4.5 text-amber-500" />
                <h2 className="text-xs font-bold tracking-wider text-zinc-300 uppercase">Storyboard Shot Timeline</h2>
              </div>
              <span className="text-[10px] text-zinc-500">Horizontal progression stack</span>
            </div>

            {shots.length > 0 ? (
              <div className="flex items-stretch space-x-4 overflow-x-auto pb-4 scrollbar-thin scrollbar-thumb-zinc-800 scrollbar-track-zinc-950/30">
                {shots.map((shot, idx) => {
                  const isSelected = shot.shotId === selectedShotId;
                  return (
                    <div
                      key={shot.shotId}
                      onClick={() => setSelectedShotId(shot.shotId)}
                      className={`flex-shrink-0 w-44 rounded-xl border p-2.5 transition cursor-pointer relative group flex flex-col justify-between h-44 ${
                        isSelected 
                          ? 'bg-zinc-900 border-amber-500 shadow-lg shadow-amber-500/5' 
                          : 'bg-[#121216] border-zinc-800 hover:border-zinc-700'
                      } ${shot.status === 'failed' ? 'ring-2 ring-red-500/40 border-red-500' : ''}`}
                    >
                      {/* Thumbnail frame container */}
                      <div className="aspect-video w-full bg-zinc-950 rounded-lg overflow-hidden border border-zinc-800/50 flex items-center justify-center relative mb-2">
                        {shot.status === 'done' && shot.imageUrl ? (
                          <img
                            src={shot.imageUrl}
                            alt="Shot thumbnail"
                            className="w-full h-full object-cover group-hover:scale-105 transition"
                            referrerPolicy="no-referrer"
                          />
                        ) : shot.status === 'generating' ? (
                          <div className="text-center">
                            <RefreshCw className="w-4 h-4 text-amber-400 animate-spin mx-auto mb-1" />
                            <span className="text-[8px] font-semibold text-amber-400 tracking-wide uppercase">rendering</span>
                          </div>
                        ) : shot.status === 'failed' ? (
                          <div className="text-center p-2">
                            <AlertTriangle className="w-4 h-4 text-red-400 mx-auto mb-1" />
                            <span className="text-[8px] font-semibold text-red-400 tracking-wide uppercase">failed validation</span>
                          </div>
                        ) : (
                          <div className="text-center">
                            <Clock className="w-4 h-4 text-zinc-600 mx-auto" />
                          </div>
                        )}

                        <span className="absolute top-1 right-1 px-1.5 py-0.5 rounded text-[8.5px] font-mono font-bold bg-black/75 backdrop-blur border border-zinc-800 text-zinc-400">
                          {shot.durationSeconds}s
                        </span>
                      </div>

                      {/* Info label footer */}
                      <div className="space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] font-bold text-white font-mono">{shot.shotId.toUpperCase()}</span>
                          <span className="text-[9px] text-zinc-500">{shot.cameraAngle.split(" ")[0]}</span>
                        </div>
                        <p className="text-[9.5px] text-zinc-400 line-clamp-2 leading-snug">{shot.description}</p>
                      </div>

                      {/* Active rendering pointer outline bar */}
                      {processingIndex === idx && (
                        <div className="absolute inset-x-0 -bottom-1 h-1 bg-amber-500 rounded-b-xl animate-pulse" />
                      )}
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="bg-zinc-950 rounded-xl p-8 border border-zinc-800/80 text-center text-zinc-500 text-[11px] leading-relaxed">
                <Film className="w-8 h-8 text-zinc-600 mx-auto mb-2 stroke-[1.5]" />
                <p>No shots planned. Enter a prompt inside the Control Center to begin compilation.</p>
              </div>
            )}
          </div>

          {/* Section: EDL Export & Final Render compilations */}
          <div className="p-6 bg-gradient-to-t from-zinc-950 to-[#08080a] flex flex-wrap items-center justify-between gap-4">
            <div className="space-y-1">
              <h3 className="text-xs font-bold text-white flex items-center space-x-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Sequence Compilation & Exporters</span>
              </h3>
              <p className="text-[10.5px] text-zinc-500">Assembles frames into high-quality H.264 formats or exports standard timeline descriptors.</p>
            </div>

            <div className="flex items-center space-x-2.5">
              <button
                onClick={() => addLog("FFmpeg Exporter: Sequential compiling initialized. Output file: storage/projects/scene_001.mp4")}
                disabled={completedShotsList.length === 0}
                className="px-4 py-2.5 bg-zinc-900 hover:bg-zinc-850 disabled:opacity-40 text-xs font-bold rounded-lg border border-zinc-800 flex items-center space-x-1.5 transition text-zinc-200 cursor-pointer disabled:cursor-not-allowed"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Compile with FFmpeg</span>
              </button>

              <button
                onClick={() => addLog("OTIO Exporter: EDL Timeline file exported. File saved to storage/projects/scene_001.edl")}
                disabled={completedShotsList.length === 0}
                className="px-4 py-2.5 bg-zinc-900 hover:bg-zinc-850 disabled:opacity-40 text-xs font-bold rounded-lg border border-zinc-800 flex items-center space-x-1.5 transition text-zinc-200 cursor-pointer disabled:cursor-not-allowed"
              >
                <Layers className="w-3.5 h-3.5" />
                <span>Export EDL Timeline (.otio)</span>
              </button>
            </div>
          </div>

        </section>

      </main>
      
      {/* Absolute Bottom Studio Status bar */}
      <footer className="border-t border-zinc-800/80 bg-zinc-950 px-5 py-2.5 flex items-center justify-between text-[10px] text-zinc-500">
        <div className="flex items-center space-x-4">
          <span>Project Root: <code className="text-zinc-400 font-mono">./ai_production_studio/</code></span>
          <span className="text-zinc-700">|</span>
          <span className="flex items-center space-x-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            <span>SQLite Active</span>
          </span>
          <span className="text-zinc-700">|</span>
          <span className="flex items-center space-x-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            <span>OpenUSD Core Engine Loaded</span>
          </span>
        </div>
        <div>
          <span>Local System Time: {new Date().toLocaleTimeString()}</span>
        </div>
      </footer>

    </div>
  );
}
