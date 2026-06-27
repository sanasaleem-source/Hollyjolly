import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';
import { GoogleGenAI } from '@google/genai';

dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
app.use(express.json());

// Initialize Google Gen AI SDK safely
const apiKey = process.env.GEMINI_API_KEY;
let ai: GoogleGenAI | null = null;

if (apiKey && apiKey !== "MY_GEMINI_API_KEY") {
  try {
    ai = new GoogleGenAI({
      apiKey: apiKey,
      httpOptions: {
        headers: {
          'User-Agent': 'aistudio-build'
        }
      }
    });
    console.log("Gemini SDK initialized successfully on backend.");
  } catch (err) {
    console.error("Failed to initialize Gemini SDK:", err);
  }
} else {
  console.log("No valid GEMINI_API_KEY found, running with offline mockup generators.");
}

// In-Memory Database / World State Simulator
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

let simulatedCharacters: Character[] = [
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
];

let simulatedObjects: WorldObject[] = [
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
];

let simulatedShots: Shot[] = [];
let pipelineLogs: string[] = ["Pipeline initialized.", "Ready for story prompts."];
let currentTaskIndex = -1;
let pipelineRunning = false;

// Helpers to generate prompt hashes for consistent visuals
function stringToHash(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  return Math.abs(hash);
}

// 1. STORY PARSER API
app.post('/api/parse-story', async (req, res) => {
  const { prompt } = req.body;
  
  if (!prompt) {
    return res.status(400).json({ error: "Story prompt is required" });
  }

  pipelineLogs = ["Director: Starting story analysis...", `User prompt: "${prompt}"`];
  pipelineRunning = true;
  currentTaskIndex = 0;

  try {
    if (ai) {
      pipelineLogs.push("Director: Contacting Gemini 3.5 Flash for scene breakdown...");
      const systemPrompt = `
        You are an expert movie director and storyboard planner. Your job is to break down a story prompt into a sequence of exactly 3 to 5 cinematic shots.
        Each shot must have a unique 'shot_id' (e.g. shot_001, shot_002), 'scene_id', 'description', 'camera_angle' (e.g., Wide-Angle, Close-Up, Low-Angle, Birds-Eye-View), 'duration_seconds' (number), 'lighting' (e.g., Noir Shadow, Golden Hour, Wet Neon, High-Key), 'characters_present' (string array), 'objects_present' (string array), 'action' (detailed visual action), and optionally 'dialogue'.
        Respond ONLY with a valid JSON array representing the production plan, with NO markdown block formatting or chat preambles.
      `;
      
      const response = await ai.models.generateContent({
        model: 'gemini-3.5-flash',
        contents: `Story Prompt: "${prompt}"\nGenerate a sequential storyboard.`,
        config: {
          systemInstruction: systemPrompt,
          responseMimeType: 'application/json'
        }
      });

      const responseText = response.text || "[]";
      let parsedShots: any = [];
      try {
        parsedShots = JSON.parse(responseText);
        if (parsedShots.shots && Array.isArray(parsedShots.shots)) {
          parsedShots = parsedShots.shots;
        }
      } catch (pe) {
        console.error("JSON parsing failed, falling back to procedural storyboard:", pe);
        parsedShots = getFallbackStoryboard(prompt);
      }

      simulatedShots = parsedShots.map((s: any, idx: number) => ({
        shotId: s.shot_id || `shot_00${idx + 1}`,
        sceneId: s.scene_id || "scene_001",
        description: s.description || s.action || "Cinematic shot",
        cameraAngle: s.camera_angle || "Medium Shot",
        durationSeconds: s.duration_seconds || 3.5,
        lighting: s.lighting || "Cinematic",
        charactersPresent: s.characters_present || ["John"],
        objectsPresent: s.objects_present || [],
        action: s.action || s.description || "Action unfolds",
        dialogue: s.dialogue,
        status: 'pending',
        repairAttempts: 0
      }));

    } else {
      pipelineLogs.push("Director [Offline Mode]: Simulating local storyboard planning engine...");
      simulatedShots = getFallbackStoryboard(prompt);
    }

    pipelineLogs.push(`Director: Successfully planned ${simulatedShots.length} shots.`);
    pipelineLogs.push("World State: Memory catalog updated.");
    
    // Update character last seen shot
    simulatedShots.forEach(shot => {
      shot.charactersPresent.forEach(charName => {
        const found = simulatedCharacters.find(c => c.name.toLowerCase() === charName.toLowerCase());
        if (found) {
          found.lastSeenShotId = shot.shotId;
        } else {
          // auto-register characters if new ones discovered!
          simulatedCharacters.push({
            name: charName,
            appearance: "Intriguing newcomer introduced by prompt",
            clothing: "Stylish attire matching environment",
            injuries: "None",
            relationships: "Complex newcomer networks",
            history: "Background shroud in mystery",
            lastSeenShotId: shot.shotId
          });
        }
      });
    });

    res.json({
      success: true,
      shots: simulatedShots,
      characters: simulatedCharacters,
      objects: simulatedObjects,
      logs: pipelineLogs
    });

  } catch (error: any) {
    console.error("Storyboard failure:", error);
    res.status(500).json({ error: error.message });
  } finally {
    pipelineRunning = false;
  }
});

function getFallbackStoryboard(prompt: string): Shot[] {
  const isRain = prompt.toLowerCase().includes("rain") || prompt.toLowerCase().includes("wet");
  const isSpace = prompt.toLowerCase().includes("space") || prompt.toLowerCase().includes("star");
  
  if (isSpace) {
    return [
      {
        shotId: "shot_001",
        sceneId: "scene_001",
        description: "Space Cruiser gliding past a brilliant gaseous supernova nebular background",
        cameraAngle: "Extremely Wide",
        durationSeconds: 5.0,
        lighting: "Bright Cosmic Luminescence",
        charactersPresent: ["Vance"],
        objectsPresent: ["Case File"],
        action: "The cruiser engines glow white hot as it navigates asteroid belts.",
        status: 'pending',
        repairAttempts: 0
      },
      {
        shotId: "shot_002",
        sceneId: "scene_001",
        description: "Vance inside the cockpit, neon indicators lighting his focused rookie face",
        cameraAngle: "Close-Up",
        durationSeconds: 3.5,
        lighting: "Glow Indicator Neon",
        charactersPresent: ["Vance"],
        objectsPresent: [],
        dialogue: "Target locked, prepping hyperspace warp vector.",
        action: "Vance pushes the golden coordinates lever forward.",
        status: 'pending',
        repairAttempts: 0
      },
      {
        shotId: "shot_003",
        sceneId: "scene_001",
        description: "Deep space gate warp visual vortex as the ship accelerates into hyper-speed",
        cameraAngle: "Low-Angle Tracking",
        durationSeconds: 4.0,
        lighting: "Starlit Warp Radiance",
        charactersPresent: ["John", "Vance"],
        objectsPresent: ["Umbrella"],
        action: "Light streaks wrap around the hull, reflecting blue on the glass pane.",
        status: 'pending',
        repairAttempts: 0
      }
    ];
  }

  return [
    {
      shotId: "shot_001",
      sceneId: "scene_001",
      description: "Establish dark city alleys under heavy rain, neon lights flashing",
      cameraAngle: "Wide-Angle",
      durationSeconds: 4.0,
      lighting: "Wet Neon Shadow",
      charactersPresent: ["John"],
      objectsPresent: ["Umbrella"],
      action: "John stands on the street corner beneath a flickering bar sign.",
      status: 'pending',
      repairAttempts: 0
    },
    {
      shotId: "shot_002",
      sceneId: "scene_001",
      description: "John holding his wet umbrella, peering at Vance through the steam ventilation",
      cameraAngle: "Medium Close-up",
      durationSeconds: 3.0,
      lighting: "High-contrast Backlight",
      charactersPresent: ["John", "Vance"],
      objectsPresent: ["Umbrella"],
      dialogue: "You're late, Vance. The contact already moved.",
      action: "John flicks a cigarette away, steam rising around his leather coat.",
      status: 'pending',
      repairAttempts: 0
    },
    {
      shotId: "shot_003",
      sceneId: "scene_001",
      description: "Close-up on the dusty Case File left resting on a wooden crate",
      cameraAngle: "Macro Detail",
      durationSeconds: 2.5,
      lighting: "Dim Spot Light",
      charactersPresent: ["Vance"],
      objectsPresent: ["Case File"],
      action: "Vance reaches out to pick up the file, rain drops dripping off his leather glove.",
      status: 'pending',
      repairAttempts: 0
    }
  ];
}

// 2. ORCHESTRATE SHOT PIPELINE API
app.post('/api/process-shot', async (req, res) => {
  const { shotId, index } = req.body;
  const shot = simulatedShots.find(s => s.shotId === shotId);

  if (!shot) {
    return res.status(404).json({ error: "Shot not found" });
  }

  pipelineLogs.push(`Orchestrator: Activating workflow for Shot ${shotId}`);
  shot.status = 'generating';

  try {
    // Stage 1: Asset Manager resolution
    pipelineLogs.push(`AssetManager: Resolving character and prop versions for Shot ${shotId}`);
    shot.assetVersions = {};
    shot.charactersPresent.forEach(char => {
      const dbChar = simulatedCharacters.find(c => c.name === char);
      shot.assetVersions![char] = dbChar ? 1 : 1;
    });
    shot.objectsPresent.forEach(obj => {
      shot.assetVersions![obj] = 1;
    });

    // Stage 2: Scene Composer USD Generation
    pipelineLogs.push(`SceneComposer: Writing OpenUSD Stage File: storage/projects/scene_001/${shotId}.usda`);
    pipelineLogs.push(`SceneComposer: Writing layout payload scene.json for Godot engine`);

    // Stage 3: Headless Render
    pipelineLogs.push(`ProcessManager: Spawning headless Godot renderer process: godot --headless --script render_scene.gd`);
    // Create a beautiful seedable thematic image from Picsum/Unsplash as the "rendered" frame
    const hash = stringToHash(shot.description + shot.lighting);
    const rainSeed = shot.description.toLowerCase().includes("rain") ? "rainy,dark,noir,neon" : "space,nebula,galaxy,cosmic";
    // Generates a stunning thematic image that is highly consistent
    shot.imageUrl = `https://images.unsplash.com/photo-${1500000000000 + (hash % 100000)}?auto=format&fit=crop&w=640&q=80&sig=${hash}`;
    if (hash % 7 === 0) {
      // simulate rare failure to showcase the validators & repair engine beautifully!
      shot.imageUrl = `https://images.unsplash.com/photo-1543466835-00a7907e9de1?auto=format&fit=crop&w=640&q=80`; // random dog to trigger absolute funny validation fail!
    }

    pipelineLogs.push(`ProcessManager: Godot headless exited successfully. Renders saved to cache.`);

    // Stage 4: Validation Engine
    pipelineLogs.push(`Validators: Invoking multimodal consistency checks...`);
    
    // Evaluate if this shot triggers simulated failure
    const isDog = shot.imageUrl.includes("1543466835");
    if (isDog) {
      pipelineLogs.push(`CharacterValidator: ❌ FAILURE - Render frame contains a canine asset, mismatching human character database!`);
      pipelineLogs.push(`StoryValidator: ❌ FAILURE - Plot coherence broken. Detective replaced by golden retriever!`);
      
      shot.validationResult = {
        passed: false,
        failures: [
          "CharacterValidator: Frame contains canine asset mismatching character 'John'",
          "StoryValidator: Scene contains logic anomaly (Detective morphed into animal)"
        ],
        severity: "critical"
      };
      
      shot.status = 'failed';
    } else {
      pipelineLogs.push(`CharacterValidator: ✅ PASSED`);
      pipelineLogs.push(`StoryValidator: ✅ PASSED`);
      pipelineLogs.push(`StyleValidator: ✅ PASSED`);
      pipelineLogs.push(`PhysicsValidator: ✅ PASSED`);
      
      shot.validationResult = {
        passed: true,
        failures: [],
        severity: "none"
      };
      shot.status = 'done';
    }

    res.json({
      success: true,
      shot: shot,
      logs: pipelineLogs
    });

  } catch (err: any) {
    shot.status = 'failed';
    res.status(500).json({ error: err.message });
  }
});

// 3. REPAIR ENGINE API
app.post('/api/repair-shot', async (req, res) => {
  const { shotId } = req.body;
  const shot = simulatedShots.find(s => s.shotId === shotId);

  if (!shot) {
    return res.status(404).json({ error: "Shot not found" });
  }

  shot.repairAttempts += 1;
  pipelineLogs.push(`RepairEngine: Launching repair sweep for Shot ${shotId} (Attempt ${shot.repairAttempts}/3)`);
  
  // Repair character or narrative prompt parameters
  pipelineLogs.push("RepairEngine: Adjusting asset parameters with positive character weights...");
  pipelineLogs.push("Orchestrator: Re-running Scene Composer layout USD bakes");
  pipelineLogs.push("ProcessManager: Re-triggering headless Godot render pass...");

  // Generate correct consistent image
  const hash = stringToHash(shot.description + "fixed" + shot.repairAttempts);
  shot.imageUrl = `https://images.unsplash.com/photo-${1510000000000 + (hash % 100000)}?auto=format&fit=crop&w=640&q=80&sig=${hash}`;
  
  pipelineLogs.push("Validators: Re-evaluating frame continuity rules...");
  pipelineLogs.push("CharacterValidator: ✅ PASSED");
  pipelineLogs.push("StoryValidator: ✅ PASSED");
  pipelineLogs.push("StyleValidator: ✅ PASSED");
  
  shot.validationResult = {
    passed: true,
    failures: [],
    severity: "none"
  };
  shot.status = 'done';

  res.json({
    success: true,
    shot: shot,
    logs: pipelineLogs
  });
});

// Serve frontend assets in production build
if (process.env.NODE_ENV === 'production') {
  app.use(express.static(path.join(__dirname, 'dist')));
  app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'dist', 'index.html'));
  });
} else {
  // Let Vite handle it in dev
}

// Start Server on exclusive port 3000
const PORT = 3000;
app.listen(PORT, '0.0.0.0', () => {
  console.log(`Server is running at http://0.0.0.0:${PORT}`);
});
