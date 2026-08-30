import React, { useState, useMemo, useCallback } from "react";

/* ------------------------------------------------------------------ */
/* Environmental simulator (ported from environmental_simulator.py)    */
/* ------------------------------------------------------------------ */

const SIM_START = new Date(2025, 5, 21, 9, 0); // June 21 2025, 09:00

function makeSimState(step = 0, current = SIM_START) {
  return { step, current };
}

function snapshot({ step, current }) {
  const hour = current.getHours() + current.getMinutes() / 60;
  const daylight = Math.max(0, 1 - Math.abs(hour - 12) / 7);
  const cloudCycle = (step % 5) / 4;

  const solar = Math.round(Math.max(0, 930 * daylight * (1 - 0.28 * cloudCycle)));
  const wind = Math.round((9 + 4 * ((step + 1) % 3) - 2 * cloudCycle) * 10) / 10;
  const temperature = Math.round((22 + 7 * daylight - cloudCycle * 2) * 10) / 10;
  const weather = cloudCycle < 0.4 ? "Clear" : cloudCycle < 0.8 ? "Partly cloudy" : "Cloudy";

  const pad = (n) => String(n).padStart(2, "0");
  const timeOfDay = `${pad(current.getHours())}:${pad(current.getMinutes())}`;
  const timestamp = `${current.getFullYear()}-${pad(current.getMonth() + 1)}-${pad(
    current.getDate()
  )}T${timeOfDay}`;

  return {
    timestamp,
    time_of_day: timeOfDay,
    solar_radiation: solar,
    wind_speed: wind,
    temperature,
    weather,
  };
}

function advance({ step, current }) {
  const next = new Date(current);
  next.setHours(next.getHours() + 1);
  return { step: step + 1, current: next };
}

/* ------------------------------------------------------------------ */
/* Decision engine (ported from decision_engine.py)                    */
/* ------------------------------------------------------------------ */

function round2(n) {
  return Math.round(n * 100) / 100;
}

function energyPotential(environment) {
  const solarKw = round2((environment.solar_radiation / 1000) * 4.0);
  const windKw = round2(Math.min(environment.wind_speed / 12, 1.5) * 1.8);
  const totalKw = round2(solarKw + windKw);
  const solarLevel = solarKw >= 2.5 ? "High" : solarKw >= 1 ? "Moderate" : "Low";
  const windLevel = windKw >= 1.5 ? "High" : windKw >= 0.8 ? "Moderate" : "Low";
  return { solar_kw: solarKw, wind_kw: windKw, total_kw: totalKw, solar_level: solarLevel, wind_level: windLevel };
}

function buildDecision(environment, resources) {
  const energy = energyPotential(environment);

  const ranked = resources
    .map((resource) => {
      const quantity = Math.max(parseFloat(resource.quantity) || 0, 0);
      const scarcity = 1 / Math.max(quantity, 1);
      let score = resource.priority * (1 + Math.min(scarcity * 100, 1.5));
      if (resource.name.toLowerCase() === "water" && environment.temperature >= 27) {
        score += 3;
      }
      return { ...resource, score: round2(score) };
    })
    .sort((a, b) => b.score - a.score);

  const top = ranked[0];
  const actions = [
    {
      title: `Prioritize ${top.name.toLowerCase()} operations`,
      detail: `Priority ${top.priority}/10 leads the current ranking, with ${top.quantity} ${top.unit} available.`,
      type: "priority",
    },
  ];

  if (energy.solar_level === "High") {
    actions.push({
      title: "Run high-load tasks on solar",
      detail: "Strong sunlight makes desalination, charging, and pumping the best use of current generation.",
      type: "energy",
    });
  } else if (energy.wind_level === "High") {
    actions.push({
      title: "Use wind generation first",
      detail: "Wind is the strongest renewable source right now; reserve fuel for critical backup.",
      type: "energy",
    });
  } else {
    actions.push({
      title: "Conserve and store energy",
      detail: "Renewable output is moderate or low, so defer flexible loads and protect the battery reserve.",
      type: "energy",
    });
  }

  actions.push({
    title: "Store remaining energy",
    detail: "Keep surplus in storage for the next low-production period and overnight demand.",
    type: "storage",
  });

  return { environment, energy, resources: ranked, recommendations: actions };
}

/* ------------------------------------------------------------------ */
/* Default resources                                                   */
/* ------------------------------------------------------------------ */

const DEFAULT_RESOURCES = [
  { name: "Water", quantity: 420, unit: "L", priority: 10 },
  { name: "Food", quantity: 160, unit: "kg", priority: 7 },
  { name: "Fuel", quantity: 85, unit: "L", priority: 6 },
  { name: "General supplies", quantity: 34, unit: "boxes", priority: 5 },
];

/* ------------------------------------------------------------------ */
/* UI helpers                                                          */
/* ------------------------------------------------------------------ */

const LEVEL_STYLES = {
  High: "text-[#5EEAD4] bg-[#134E4A]",
  Moderate: "text-[#F2C265] bg-[#4A3A14]",
  Low: "text-[#F2A08A] bg-[#4A2015]",
};

const TYPE_ICON = { priority: "◆", energy: "☀", storage: "⬢" };

function LevelBar({ label, value, max, level }) {
  const pct = Math.min(100, Math.round((value / max) * 100));
  return (
    <div className="flex-1">
      <div className="flex items-baseline justify-between mb-1.5">
        <span className="text-[11px] tracking-[0.15em] uppercase text-[#7C93A0] font-mono">{label}</span>
        <span className={`text-[10px] px-2 py-0.5 rounded-full font-mono ${LEVEL_STYLES[level]}`}>{level}</span>
      </div>
      <div className="text-2xl font-semibold text-[#E8F1F2] mb-2 tabular-nums">{value.toFixed(2)} <span className="text-sm text-[#7C93A0] font-normal">kW</span></div>
      <div className="h-1.5 w-full rounded-full bg-[#0B1E2D] overflow-hidden">
        <div
          className="h-full rounded-full bg-gradient-to-r from-[#2DD4BF] to-[#5EEAD4] transition-all duration-700 ease-out"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

function EnvMetric({ label, value, accent }) {
  return (
    <div className="rounded-lg border border-[#1D3A4F] bg-[#0F2637] px-4 py-3">
      <div className="text-[10px] tracking-[0.15em] uppercase text-[#5C7A8A] font-mono mb-1">{label}</div>
      <div className={`text-lg font-semibold tabular-nums ${accent || "text-[#E8F1F2]"}`}>{value}</div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Main app                                                             */
/* ------------------------------------------------------------------ */

export default function App() {
  const [simState, setSimState] = useState(makeSimState());
  const [resources, setResources] = useState(DEFAULT_RESOURCES);
  const [draft, setDraft] = useState(null); // resource editor draft
  const [log, setLog] = useState([]);

  const environment = useMemo(() => snapshot(simState), [simState]);
  const decision = useMemo(() => buildDecision(environment, resources), [environment, resources]);

  const handleAdvance = useCallback(() => {
    setSimState((prev) => {
      const next = advance(prev);
      const env = snapshot(next);
      setLog((l) => [
        { time: env.time_of_day, weather: env.weather, note: `Step ${next.step} — ${env.weather.toLowerCase()}, ${env.solar_radiation} W/m² solar, ${env.wind_speed} m/s wind.` },
        ...l,
      ].slice(0, 8));
      return next;
    });
  }, []);

  const openEditor = () => setDraft(resources.map((r) => ({ ...r })));
  const saveEditor = () => {
    setResources(draft);
    setDraft(null);
  };

  return (
    <div className="min-h-screen w-full bg-[#0B1E2D] text-[#E8F1F2]" style={{ fontFamily: "'Inter', system-ui, sans-serif" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');
        .font-display { font-family: 'Space Grotesk', system-ui, sans-serif; }
        .font-mono { font-family: 'JetBrains Mono', ui-monospace, monospace; }
      `}</style>

      {/* Header */}
      <header className="border-b border-[#1D3A4F] px-6 py-4 flex items-center justify-between sticky top-0 bg-[#0B1E2D]/95 backdrop-blur z-10">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-[#2DD4BF] to-[#0EA5A6] flex items-center justify-center text-[#0B1E2D] font-bold font-display text-sm">IR</div>
          <div>
            <h1 className="font-display font-semibold text-lg leading-tight">Island Resource Station</h1>
            <p className="text-[11px] text-[#5C7A8A] font-mono tracking-wide">simulation-first environmental resource management</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right hidden sm:block">
            <div className="text-[10px] uppercase tracking-[0.15em] text-[#5C7A8A] font-mono">Sim Time</div>
            <div className="font-mono text-sm text-[#E8F1F2]">{environment.time_of_day} · {environment.weather}</div>
          </div>
          <button
            onClick={handleAdvance}
            className="rounded-lg bg-[#2DD4BF] hover:bg-[#5EEAD4] text-[#0B1E2D] font-semibold text-sm px-4 py-2.5 transition-colors shadow-[0_0_0_1px_rgba(45,212,191,0.3)]"
          >
            ↻ Advance Simulation
          </button>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8 space-y-8">
        {/* Environment strip */}
        <section>
          <h2 className="font-display text-xs tracking-[0.2em] uppercase text-[#5C7A8A] mb-3">Environmental Conditions</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
            <EnvMetric label="Time of day" value={environment.time_of_day} />
            <EnvMetric label="Weather" value={environment.weather} />
            <EnvMetric label="Solar radiation" value={`${environment.solar_radiation} W/m²`} accent="text-[#F2C265]" />
            <EnvMetric label="Wind speed" value={`${environment.wind_speed} m/s`} accent="text-[#5EEAD4]" />
            <EnvMetric label="Temperature" value={`${environment.temperature} °C`} accent={environment.temperature >= 27 ? "text-[#F2A08A]" : undefined} />
          </div>
        </section>

        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* Energy panel */}
          <section className="lg:col-span-2 rounded-xl border border-[#1D3A4F] bg-[#0F2637] p-5">
            <h2 className="font-display text-xs tracking-[0.2em] uppercase text-[#5C7A8A] mb-4">Energy Potential</h2>
            <div className="space-y-5">
              <LevelBar label="Solar" value={decision.energy.solar_kw} max={4} level={decision.energy.solar_level} />
              <LevelBar label="Wind" value={decision.energy.wind_kw} max={1.8} level={decision.energy.wind_level} />
            </div>
            <div className="mt-5 pt-4 border-t border-[#1D3A4F] flex items-baseline justify-between">
              <span className="text-[11px] tracking-[0.15em] uppercase text-[#7C93A0] font-mono">Total generation</span>
              <span className="font-display text-2xl font-semibold text-[#E8F1F2] tabular-nums">{decision.energy.total_kw.toFixed(2)} kW</span>
            </div>
          </section>

          {/* Recommendations */}
          <section className="lg:col-span-3 rounded-xl border border-[#1D3A4F] bg-[#0F2637] p-5">
            <h2 className="font-display text-xs tracking-[0.2em] uppercase text-[#5C7A8A] mb-4">Recommended Actions</h2>
            <div className="space-y-3">
              {decision.recommendations.map((action, i) => (
                <div key={i} className="flex gap-3 rounded-lg bg-[#0B1E2D] border border-[#1D3A4F] px-4 py-3">
                  <span className="text-[#2DD4BF] text-lg leading-none mt-0.5">{TYPE_ICON[action.type] || "•"}</span>
                  <div>
                    <div className="font-semibold text-sm text-[#E8F1F2]">{action.title}</div>
                    <div className="text-[13px] text-[#93A9B5] mt-0.5 leading-snug">{action.detail}</div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>

        {/* Resources */}
        <section className="rounded-xl border border-[#1D3A4F] bg-[#0F2637] p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-display text-xs tracking-[0.2em] uppercase text-[#5C7A8A]">Resources — ranked by urgency</h2>
            {draft === null ? (
              <button
                onClick={openEditor}
                className="text-xs font-mono text-[#5EEAD4] hover:text-[#2DD4BF] border border-[#1D3A4F] rounded-md px-3 py-1.5 transition-colors"
              >
                Edit resources
              </button>
            ) : (
              <div className="flex gap-2">
                <button
                  onClick={() => setDraft(null)}
                  className="text-xs font-mono text-[#7C93A0] hover:text-[#E8F1F2] border border-[#1D3A4F] rounded-md px-3 py-1.5 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={saveEditor}
                  className="text-xs font-mono text-[#0B1E2D] bg-[#2DD4BF] hover:bg-[#5EEAD4] rounded-md px-3 py-1.5 font-semibold transition-colors"
                >
                  Save
                </button>
              </div>
            )}
          </div>

          {draft === null ? (
            <div className="space-y-2">
              {decision.resources.map((r, i) => (
                <div
                  key={r.name}
                  className={`flex items-center gap-4 rounded-lg px-4 py-3 border ${
                    i === 0 ? "border-[#2DD4BF]/50 bg-[#12352F]" : "border-[#1D3A4F] bg-[#0B1E2D]"
                  }`}
                >
                  <span className="font-mono text-[#5C7A8A] text-xs w-5">{i + 1}</span>
                  <span className="font-semibold text-sm flex-1">{r.name}</span>
                  <span className="font-mono text-sm text-[#93A9B5] w-28 text-right">{r.quantity} {r.unit}</span>
                  <span className="font-mono text-xs text-[#5C7A8A] w-20 text-right">P{r.priority}/10</span>
                  <span className={`font-mono text-sm w-16 text-right font-semibold ${i === 0 ? "text-[#5EEAD4]" : "text-[#7C93A0]"}`}>{r.score.toFixed(2)}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="space-y-2">
              <div className="grid grid-cols-[2fr_1fr_1fr_1fr] gap-3 text-[10px] uppercase tracking-wider text-[#5C7A8A] font-mono px-1">
                <span>Name</span><span>Quantity</span><span>Unit</span><span>Priority</span>
              </div>
              {draft.map((r, i) => (
                <div key={i} className="grid grid-cols-[2fr_1fr_1fr_1fr] gap-3">
                  <input
                    value={r.name}
                    onChange={(e) => setDraft((d) => d.map((x, j) => (j === i ? { ...x, name: e.target.value } : x)))}
                    className="bg-[#0B1E2D] border border-[#1D3A4F] rounded-md px-3 py-2 text-sm focus:outline-none focus:border-[#2DD4BF]"
                  />
                  <input
                    type="number"
                    value={r.quantity}
                    onChange={(e) => setDraft((d) => d.map((x, j) => (j === i ? { ...x, quantity: e.target.value } : x)))}
                    className="bg-[#0B1E2D] border border-[#1D3A4F] rounded-md px-3 py-2 text-sm font-mono focus:outline-none focus:border-[#2DD4BF]"
                  />
                  <input
                    value={r.unit}
                    onChange={(e) => setDraft((d) => d.map((x, j) => (j === i ? { ...x, unit: e.target.value } : x)))}
                    className="bg-[#0B1E2D] border border-[#1D3A4F] rounded-md px-3 py-2 text-sm font-mono focus:outline-none focus:border-[#2DD4BF]"
                  />
                  <input
                    type="number"
                    min="0"
                    max="10"
                    value={r.priority}
                    onChange={(e) => setDraft((d) => d.map((x, j) => (j === i ? { ...x, priority: Number(e.target.value) } : x)))}
                    className="bg-[#0B1E2D] border border-[#1D3A4F] rounded-md px-3 py-2 text-sm font-mono focus:outline-none focus:border-[#2DD4BF]"
                  />
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Event log */}
        {log.length > 0 && (
          <section className="rounded-xl border border-[#1D3A4F] bg-[#0F2637] p-5">
            <h2 className="font-display text-xs tracking-[0.2em] uppercase text-[#5C7A8A] mb-4">Event Log</h2>
            <div className="space-y-2 font-mono text-[13px]">
              {log.map((entry, i) => (
                <div key={i} className="flex gap-3 text-[#93A9B5]">
                  <span className="text-[#5C7A8A] w-12 shrink-0">{entry.time}</span>
                  <span>{entry.note}</span>
                </div>
              ))}
            </div>
          </section>
        )}
      </main>
    </div>
  );
}