import { useEffect, useState } from 'react';
import { Search, Loader2 } from 'lucide-react';
import GlobeView from './components/GlobeView';

export default function App() {
  const [rows, setRows] = useState([]);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/expertise');
      const json = await res.json();
      setRows(json.data || []);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  useEffect(() => {
    loadData();
  }, []);

  const filtered = rows.filter((r) => {
    const q = query.toLowerCase();
    return (
      r.author_name?.toLowerCase().includes(q) ||
      r.l1_field?.toLowerCase().includes(q) ||
      r.l2_domain?.toLowerCase().includes(q) ||
      r.subfield_name?.toLowerCase().includes(q)
    );
  });

  return (
    <div className="min-h-screen bg-green-500 text-[#E6EDF3] flex flex-col items-center">

      {/* 🔝 HEADER */}
      <div className="w-full max-w-5xl px-6 pt-12">
        <div className="flex flex-col items-center gap-4">

          <h1 className="text-2xl font-semibold tracking-tight">
            Research Intelligence
          </h1>

          <p className="text-sm text-[#8B949E]">
            Explore global expertise through interactive visualization
          </p>

          {/* 🔍 SEARCH BAR */}
          <div className="relative w-full max-w-xl mt-4">
            <Search size={18} className="absolute left-4 top-3.5 text-[#8B949E]" />

            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search authors, domains, research fields..."
              className="
                w-full pl-12 pr-4 py-3
                bg-[#161B22]/80
                backdrop-blur-md
                border border-[#30363D]
                rounded-xl
                text-sm
                placeholder:text-[#6E7681]
                focus:outline-none
                focus:ring-2 focus:ring-[#238636]
                transition
              "
            />
          </div>
        </div>
      </div>

      {/* 🌍 MAIN CONTENT */}
      <div className="flex-1 w-full flex flex-col items-center justify-center px-6">

        {loading ? (
          <div className="flex flex-col items-center gap-3 mt-10">
            <Loader2 className="animate-spin text-[#8B949E]" />
            <span className="text-sm text-[#8B949E]">Loading data...</span>
          </div>
        ) : (
          <>
            {/* 🌍 GLOBE HERO */}
            <div className="relative mt-10 mb-12">

              {/* glow background */}
              <div className="absolute inset-0 blur-3xl opacity-20 bg-gradient-to-tr from-blue-500 via-purple-500 to-emerald-500 rounded-full" />

              <div className="relative w-[70vh] h-[70vh]">
                <GlobeView rows={filtered} />
              </div>
            </div>

            {/* 📊 RESULT LIST */}
            <div className="w-full max-w-2xl space-y-3 pb-16">

              {filtered.slice(0, 8).map((r, i) => (
                <div
                  key={i}
                  className="
                    group
                    px-5 py-4
                    border border-[#30363D]
                    rounded-xl
                    bg-[#161B22]/80
                    backdrop-blur-md
                    hover:bg-[#1C2128]
                    hover:border-[#3B82F6]
                    transition-all
                    cursor-pointer
                  "
                >
                  <div className="flex items-center justify-between">

                    <div>
                      <div className="text-sm font-medium group-hover:text-white">
                        {r.author_name}
                      </div>

                      <div className="text-xs text-[#8B949E] mt-1">
                        {r.l1_field} · {r.l2_domain}
                      </div>
                    </div>

                    {/* score badge */}
                    {r.expertise_score && (
                      <div className="
                        text-xs px-2 py-1
                        rounded-md
                        bg-[#238636]/20
                        text-[#3FB950]
                        border border-[#238636]/30
                      ">
                        {Number(r.expertise_score).toFixed(2)}
                      </div>
                    )}

                  </div>
                </div>
              ))}

              {filtered.length === 0 && (
                <div className="text-center text-sm text-[#8B949E] pt-10">
                  No results found
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}