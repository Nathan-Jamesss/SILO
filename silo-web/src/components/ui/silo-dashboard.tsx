import React, { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';

export const SiloDashboard: React.FC = () => {
  const [opportunities, setOpportunities] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Filters
  const [q, setQ] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [sourceFilter, setSourceFilter] = useState("");
  const [deadlineFilter, setDeadlineFilter] = useState("");
  const [stageFilter, setStageFilter] = useState("");
  const [sectorFilter, setSectorFilter] = useState("");
  const [sort, setSort] = useState("newest");

  useEffect(() => {
    fetch('/data.json')
      .then(res => res.json())
      .then(data => {
        setOpportunities(data.opportunities || []);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to load data", err);
        setLoading(false);
      });
  }, []);

  const getDeadlineBadge = (deadline: string | null) => {
    if (!deadline) return { text: "No deadline", class: "deadline-none" };
    const dlDate = new Date(deadline);
    const today = new Date();
    const days = Math.ceil((dlDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
    
    if (days < 0) return { text: "Expired", class: "deadline-expired" };
    if (days <= 7) return { text: `${days}d left`, class: "deadline-urgent" };
    if (days <= 30) return { text: `${days}d left`, class: "deadline-soon" };
    return { text: `${days}d left`, class: "deadline-ok" };
  };

  const getTypeBadge = (type: string) => {
    const map: Record<string, string> = {
      "Grant": "type-badge-grant",
      "Accelerator": "type-badge-accelerator",
      "Conference": "type-badge-conference",
      "Competition": "type-badge-competition",
      "Fellowship": "type-badge-fellowship"
    };
    return map[type] || "type-badge-default";
  };

  const filteredOpps = useMemo(() => {
    let result = opportunities.filter(o => o.status === "active");

    if (q) {
      const lowerQ = q.toLowerCase();
      result = result.filter(o => 
        (o.title || "").toLowerCase().includes(lowerQ) ||
        (o.description || "").toLowerCase().includes(lowerQ) ||
        (o.organizer || "").toLowerCase().includes(lowerQ)
      );
    }

    if (typeFilter) result = result.filter(o => o.type === typeFilter);
    if (sourceFilter) result = result.filter(o => o.source_name === sourceFilter);
    if (stageFilter) result = result.filter(o => o.startup_stage === stageFilter);
    if (sectorFilter) result = result.filter(o => o.sector === sectorFilter);

    if (deadlineFilter) {
      const today = new Date();
      result = result.filter(o => {
        if (!o.deadline) return false;
        const dlDate = new Date(o.deadline);
        const days = (dlDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24);
        if (deadlineFilter === "this_week") return days >= 0 && days <= 7;
        if (deadlineFilter === "this_month") return days >= 0 && days <= 30;
        if (deadlineFilter === "next_3_months") return days >= 0 && days <= 90;
        return true;
      });
    }

    // Sort
    result.sort((a, b) => {
      if (sort === "deadline_asc") {
        if (!a.deadline) return 1;
        if (!b.deadline) return -1;
        return new Date(a.deadline).getTime() - new Date(b.deadline).getTime();
      }
      if (sort === "prize_desc") {
        return (b.prize_pool || 0) - (a.prize_pool || 0);
      }
      if (sort === "applicants_desc") {
        return (b.num_applicants || 0) - (a.num_applicants || 0);
      }
      // default: newest scraped_at
      return new Date(b.scraped_at).getTime() - new Date(a.scraped_at).getTime();
    });

    return result;
  }, [opportunities, q, typeFilter, sourceFilter, deadlineFilter, stageFilter, sectorFilter, sort]);

  const activeCount = opportunities.filter(o => o.status === "active").length;
  const expiringSoonCount = opportunities.filter(o => o.status === "active" && o.deadline && (new Date(o.deadline).getTime() - Date.now()) / (1000 * 60 * 60 * 24) <= 7 && (new Date(o.deadline).getTime() - Date.now()) > 0).length;

  return (
    <div className="min-h-screen font-sans text-coffee-900 bg-[#fdfbf7] selection:bg-coffee-600/20 selection:text-coffee-800">
      <header className="sticky top-0 z-40 w-full glass-panel shadow-sm border-b border-[#eadecc]">
        <div className="max-w-[90rem] mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2.5 group">
            <div>
              <h1 className="text-2xl font-light tracking-[0.05em] text-[#3c2f2f] group-hover:opacity-90 transition-opacity font-serif">
                SILO
              </h1>
              <p className="text-[8px] text-[#6f4e37] font-bold uppercase tracking-[0.18em] -mt-0.5 hidden sm:block">
                Startup Intelligence for Launch & Outreach
              </p>
            </div>
          </Link>
          <div className="flex items-center gap-4 text-sm font-medium">
              <a href="/data.json" download="silo_export.json"
                  className="bg-coffee-600 hover:bg-coffee-700 text-white px-3.5 py-1.5 rounded-lg shadow-sm transition-all flex items-center gap-1 cursor-pointer">
                  Export JSON
              </a>
          </div>
        </div>
      </header>

      <main className="max-w-[90rem] mx-auto px-4 sm:px-6 py-6">
        <div className="mb-8 p-6 rounded-2xl glass-panel-heavy relative overflow-hidden shadow-sm">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
            <div>
              <h2 className="text-2xl font-extrabold font-outfit text-coffee-900 tracking-tight">Intelligence Dashboard</h2>
              <p className="text-sm text-coffee-600 mt-1">Aggregating global competitive opportunities statically generated via GitHub Actions.</p>
            </div>
            
            <div className="flex flex-wrap gap-4 text-xs font-semibold">
              <div className="px-4 py-3 rounded-xl stats-badge-glass flex items-center gap-3">
                <span className="w-2.5 h-2.5 rounded-full bg-coffee-600"></span>
                <div>
                  <div className="text-[10px] text-coffee-600 font-bold uppercase tracking-wider">Active Opportunities</div>
                  <div className="text-base font-extrabold text-coffee-900 mt-0.5">{activeCount}</div>
                </div>
              </div>
              {expiringSoonCount > 0 && (
                <div className="px-4 py-3 rounded-xl stats-badge-glass flex items-center gap-3">
                  <span className="w-2.5 h-2.5 rounded-full bg-coffee-600 animate-pulse"></span>
                  <div>
                    <div className="text-[10px] text-coffee-600 font-bold uppercase tracking-wider">Expiring Soon</div>
                    <div className="text-base font-extrabold text-coffee-900 mt-0.5">{expiringSoonCount} <span className="text-xs text-coffee-600 font-normal">(&lt; 7d)</span></div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="mb-8 space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-3.5">
            <div className="relative lg:col-span-6">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                  <svg className="h-4 w-4 text-coffee-600" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                  </svg>
              </div>
              <input type="text" value={q} onChange={e => setQ(e.target.value)} placeholder="Search competitions, hackathons, organizers, tech stack..." 
                     className="block w-full pl-10 pr-3 py-2.5 text-sm input-glass rounded-xl leading-5 text-coffee-900 placeholder-coffee-600/50 focus:outline-none focus:border-coffee-600 focus:ring-1 focus:ring-coffee-600 shadow-sm transition-colors" />
            </div>
            
            <div className="lg:col-span-6 flex items-center text-xs text-coffee-600 bg-beige-100/50 px-4 rounded-xl border border-beige-200">
               <span className="font-semibold mr-2">Note:</span> Past project matching is disabled in the static version.
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3.5 pt-1">
            <select value={typeFilter} onChange={e => setTypeFilter(e.target.value)} className="block w-full sm:w-auto pl-3 pr-10 py-2.5 text-xs input-glass rounded-xl text-coffee-800 focus:outline-none focus:border-coffee-600 appearance-none shadow-sm cursor-pointer">
              <option value="">All Types</option>
              <option value="Grant">Grants</option>
              <option value="Accelerator">Accelerators</option>
              <option value="Conference">Conferences</option>
              <option value="Competition">Competitions</option>
              <option value="Fellowship">Fellowships</option>
            </select>
            <select value={sourceFilter} onChange={e => setSourceFilter(e.target.value)} className="block w-full sm:w-auto pl-3 pr-10 py-2.5 text-xs input-glass rounded-xl text-coffee-800 focus:outline-none focus:border-coffee-600 appearance-none shadow-sm cursor-pointer">
              <option value="">All 8 Sources</option>
              <option value="Grants">Grants</option>
              <option value="Devpost">Devpost</option>
              <option value="Devfolio">Devfolio</option>
              <option value="Unstop">Unstop</option>
              <option value="Hack2Skill">Hack2Skill</option>
              <option value="F6S">F6S</option>
              <option value="Eventbrite">Eventbrite</option>
              <option value="Graham & Walker">Graham & Walker</option>
              <option value="MassChallenge">MassChallenge</option>
            </select>
            <select value={deadlineFilter} onChange={e => setDeadlineFilter(e.target.value)} className="block w-full sm:w-auto pl-3 pr-10 py-2.5 text-xs input-glass rounded-xl text-coffee-800 focus:outline-none focus:border-coffee-600 appearance-none shadow-sm cursor-pointer">
              <option value="">Any Deadline</option>
              <option value="this_week">Next 7 Days</option>
              <option value="this_month">Next 30 Days</option>
              <option value="next_3_months">Next 90 Days</option>
            </select>
            <select value={sectorFilter} onChange={e => setSectorFilter(e.target.value)} className="block w-full sm:w-auto pl-3 pr-10 py-2.5 text-xs input-glass rounded-xl text-coffee-800 focus:outline-none focus:border-coffee-600 appearance-none shadow-sm cursor-pointer">
              <option value="">All Sectors</option>
              <option value="AI / ML">AI / ML</option>
              <option value="FinTech">FinTech</option>
              <option value="HealthTech">HealthTech</option>
              <option value="AgriTech">AgriTech</option>
              <option value="EdTech">EdTech</option>
              <option value="CleanTech">CleanTech</option>
              <option value="Web3">Web3 / Blockchain</option>
              <option value="SaaS">SaaS / Enterprise</option>
              <option value="Hardware">Hardware / IoT</option>
              <option value="General">General / Open</option>
            </select>
            <div className="flex-grow"></div>
            <select value={sort} onChange={e => setSort(e.target.value)} className="block w-full sm:w-auto pl-3 pr-10 py-2.5 text-xs input-glass rounded-xl text-coffee-600 font-bold focus:outline-none focus:border-coffee-600 appearance-none shadow-sm cursor-pointer">
              <option value="newest">Sort: Newest First</option>
              <option value="deadline_asc">Sort: Deadline Soonest</option>
              <option value="prize_desc">Sort: Highest Prize Pool</option>
              <option value="applicants_desc">Sort: Most Applicants</option>
            </select>
          </div>
        </div>

        <div className="mb-6 text-coffee-600 text-xs font-semibold uppercase tracking-wider flex items-center justify-between">
            <div>Showing <span className="font-extrabold text-coffee-800">{filteredOpps.length}</span> of <span className="font-extrabold text-coffee-800">{activeCount}</span> Opportunities</div>
        </div>

        {/* Opportunities List */}
        {loading ? (
          <div className="text-center py-24 text-coffee-600 font-semibold">Loading intelligence...</div>
        ) : filteredOpps.length === 0 ? (
          <div className="text-center py-24 rounded-2xl bg-beige-100 border border-beige-200 border-dashed max-w-lg mx-auto">
              <h3 className="text-lg font-bold font-outfit text-coffee-800">No opportunities found</h3>
              <p className="mt-2 text-sm text-coffee-600">We scanned the horizon but found no matches. Adjust your filters.</p>
              <button onClick={() => { setQ(""); setTypeFilter(""); setSourceFilter(""); setDeadlineFilter(""); setSectorFilter(""); }} className="mt-5 inline-block px-4 py-2 bg-coffee-600 hover:bg-coffee-500 text-white font-bold text-sm rounded-xl transition-all shadow-sm">
                  Reset All Filters
              </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredOpps.map((opp, i) => {
              const dlBadge = getDeadlineBadge(opp.deadline);
              const typeCls = getTypeBadge(opp.type);
              
              return (
                <article key={i} className="opportunity-card rounded-2xl flex flex-col h-full relative cursor-default">
                  <div className="px-5 pt-5 pb-3 flex justify-between items-center gap-3">
                    <div className="flex items-center gap-1.5">
                      <span className={typeCls}>{opp.type}</span>
                      {opp.sector && opp.sector !== 'General' && (
                        <span className="px-2 py-0.5 rounded text-[9px] font-extrabold uppercase tracking-wider bg-beige-200 text-coffee-800 border border-beige-300/40">
                            {opp.sector}
                        </span>
                      )}
                    </div>
                    <span className={dlBadge.class}>{dlBadge.text}</span>
                  </div>

                  <div className="px-5 pb-4 flex-grow flex flex-col">
                    <h3 className="text-base font-extrabold font-outfit text-coffee-900 leading-snug mb-1.5 transition-colors title-clamp">
                        <a href={opp.source_url} target="_blank" rel="noopener noreferrer" className="hover:text-coffee-600 transition-colors">
                            {opp.title}
                        </a>
                    </h3>
                    <div className="text-xs text-coffee-600 mb-3 flex flex-col gap-1">
                        {opp.organizer && (
                        <div className="flex items-center gap-1.5 font-medium">
                            <svg className="w-3.5 h-3.5 text-coffee-600 flex-shrink-0" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"></path></svg>
                            <span className="truncate">{opp.organizer}</span>
                        </div>
                        )}
                        <div className="flex items-center gap-1.5 font-medium">
                            <svg className="w-3.5 h-3.5 text-coffee-600 flex-shrink-0" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path><path strokeLinecap="round" strokeLinejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
                            <span className="truncate">{opp.location || "Global"}</span>
                        </div>
                    </div>
                    
                    <div className="relative flex-grow min-h-[56px] mb-3">
                        <p className="text-xs text-coffee-600 leading-relaxed description-clamp">
                            {opp.description || "No description provided."}
                        </p>
                    </div>

                    <div className="grid grid-cols-2 gap-2 mb-3 mt-auto">
                        <div className="px-2.5 py-1.5 rounded-lg bg-beige-100 border border-beige-200">
                            <div className="text-[8px] text-coffee-600 font-extrabold uppercase tracking-wider leading-none">Prize / Funding</div>
                            <span className="text-[10px] font-extrabold text-coffee-800 leading-tight">
                                {opp.prize_pool_display || 'See listing'}
                            </span>
                        </div>
                        <div className="px-2.5 py-1.5 rounded-lg bg-beige-100 border border-beige-200">
                            <div className="text-[8px] text-coffee-600 font-extrabold uppercase tracking-wider leading-none">Applicants</div>
                            <span className="text-[10px] font-extrabold text-coffee-800 leading-tight">
                                {opp.num_applicants ? `${opp.num_applicants} registered` : 'N/A'}
                            </span>
                        </div>
                    </div>
                  </div>

                  <div className="bg-beige-100/50 px-5 py-3 border-t border-beige-200 flex flex-col gap-2 rounded-b-2xl">
                      <div className="flex items-center justify-between">
                          <a href={opp.source_url} target="_blank" rel="noopener noreferrer" 
                            className="text-xs font-extrabold text-coffee-600 hover:text-coffee-800 transition-colors flex items-center gap-1 group">
                              View & Apply
                              <svg className="w-3.5 h-3.5 transform group-hover:translate-x-0.5 transition-transform" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" d="M14 5l7 7m0 0l-7 7m7-7H3"></path>
                              </svg>
                          </a>
                          
                          <div className="flex items-center gap-2">
                              <span className="text-[9px] text-coffee-600 font-extrabold uppercase tracking-wider">Via {opp.source_name}</span>
                          </div>
                      </div>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </main>

      {/* SAILO Bot Chat Interface */}
      <SailoBot />
    </div>
  );
};

const SailoBot: React.FC = () => {
  const [open, setOpen] = useState(false);
  const [inputMsg, setInputMsg] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [messages, setMessages] = useState([
    { sender: 'bot', text: 'Hello founder! I am **SAILO Bot**, your personal startup mentor. Ask me anything about how/when to secure government or private grants, entity registration workflows, pitch structures, or milestone planning!' }
  ]);

  const messagesEndRef = React.useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isSending]);

  const sendQuickMessage = (txt: string) => {
    sendMessage(txt);
  };

  const sendMessage = async (text?: string) => {
    const msgText = text || inputMsg.trim();
    if (!msgText) return;

    setMessages(prev => [...prev, { sender: 'user', text: msgText }]);
    setInputMsg("");
    setIsSending(true);

    try {
      const res = await fetch('/api/sailo-bot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msgText })
      });
      const data = await res.json();
      setMessages(prev => [...prev, { sender: 'bot', text: data.response }]);
    } catch (err) {
      setMessages(prev => [...prev, { sender: 'bot', text: 'I hit a network error. Please try again in a bit!' }]);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end">
      <button type="button" onClick={() => setOpen(!open)} 
              className="w-14 h-14 bg-gradient-to-tr from-[#3c2f2f] to-[#6f4e37] hover:from-[#5a3d2a] hover:to-[#8c6239] text-[#fdfbf7] rounded-full flex items-center justify-center shadow-xl hover:scale-105 active:scale-95 transition-all duration-300 relative group cursor-pointer focus:outline-none">
          <span className="absolute inset-0 rounded-full bg-[#6f4e37]/20 animate-ping group-hover:animate-none pointer-events-none"></span>
          <svg className="w-6 h-6 transform group-hover:rotate-12 transition-transform duration-300" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
          </svg>
          <span className="absolute -top-1 -right-1 w-3.5 h-3.5 bg-green-500 border-2 border-white rounded-full"></span>
      </button>

      {open && (
        <div className="absolute bottom-16 right-0 w-[22rem] sm:w-[24rem] h-[500px] rounded-[2rem] shadow-2xl flex flex-col overflow-hidden border border-white/40 bg-white/20 backdrop-blur-2xl">
          <div className="px-5 py-4 bg-gradient-to-b from-white/30 to-transparent border-b border-white/30 flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                  <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-[#3c2f2f] to-[#6f4e37] flex items-center justify-center text-[#fdfbf7] font-bold text-sm shadow-md">
                      S
                  </div>
                  <div>
                      <h4 className="text-sm font-bold tracking-wider text-coffee-800 uppercase font-serif">SAILO Bot</h4>
                      <span className="text-[9px] text-[#6f4e37]/75 font-semibold flex items-center gap-1">
                          <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></span>
                          AI Startup Mentor Active
                      </span>
                  </div>
              </div>
              <button type="button" onClick={() => setOpen(false)} className="text-coffee-600 hover:text-coffee-900 transition-colors p-1.5 rounded-lg hover:bg-white/20 focus:outline-none">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12"></path>
                  </svg>
              </button>
          </div>

          <div className="flex-grow overflow-y-auto px-5 py-4 flex flex-col gap-3.5 scrollbar-thin">
            {messages.map((msg, i) => (
              <div key={i} className={`flex flex-col max-w-[85%] ${msg.sender === 'user' ? 'self-end items-end' : 'self-start items-start'}`}>
                <div className={`px-4 py-2.5 text-[11px] leading-relaxed prose prose-sm max-w-none ${msg.sender === 'user' ? 'bg-[#3c2f2f] text-[#fdfbf7] rounded-2xl rounded-tr-none shadow-md' : 'bg-white/40 backdrop-blur-md text-coffee-950 border border-white/40 rounded-2xl rounded-tl-none shadow-sm'}`}>
                    <p dangerouslySetInnerHTML={{ __html: msg.text.replace(/\n/g, '<br>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }}></p>
                </div>
                <span className="text-[8px] text-coffee-600/60 font-semibold mt-1 uppercase tracking-wider">{msg.sender === 'user' ? 'Founder' : 'SAILO Bot'}</span>
              </div>
            ))}
            {isSending && (
              <div className="self-start flex flex-col max-w-[85%] animate-pulse">
                  <div className="px-4 py-3 bg-white/40 border border-white/40 rounded-2xl rounded-tl-none shadow-sm flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 bg-coffee-600 rounded-full animate-bounce"></span>
                      <span className="w-1.5 h-1.5 bg-coffee-600 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></span>
                      <span className="w-1.5 h-1.5 bg-coffee-600 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></span>
                  </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="px-4 py-2 bg-white/10 border-t border-white/20 flex flex-wrap gap-1.5 justify-start">
              <button type="button" onClick={() => sendQuickMessage('How do I apply for MSME grants?')} className="text-[9px] font-bold px-2.5 py-1 bg-white/50 hover:bg-white/80 border border-white/40 text-coffee-700 hover:text-coffee-950 rounded-lg transition-colors cursor-pointer focus:outline-none">MSME Grants?</button>
              <button type="button" onClick={() => sendQuickMessage('What is the registration workflow?')} className="text-[9px] font-bold px-2.5 py-1 bg-white/50 hover:bg-white/80 border border-white/40 text-coffee-700 hover:text-coffee-950 rounded-lg transition-colors cursor-pointer focus:outline-none">Registration?</button>
              <button type="button" onClick={() => sendQuickMessage('When should I pitch private grants?')} className="text-[9px] font-bold px-2.5 py-1 bg-white/50 hover:bg-white/80 border border-white/40 text-coffee-700 hover:text-coffee-950 rounded-lg transition-colors cursor-pointer focus:outline-none">Pitching?</button>
          </div>

          <div className="px-4 py-3 bg-gradient-to-t from-white/30 to-transparent border-t border-white/30">
              <form onSubmit={(e) => { e.preventDefault(); sendMessage(); }} className="flex gap-2">
                  <input type="text" placeholder="Ask SAILO Bot how to navigate grants..." value={inputMsg} onChange={e => setInputMsg(e.target.value)} disabled={isSending}
                         className="block w-full px-3.5 py-2 text-xs bg-white/50 backdrop-blur-md border border-white/40 rounded-xl text-coffee-900 focus:outline-none focus:border-coffee-600 placeholder-coffee-600/50" />
                  <button type="submit" disabled={isSending} className="p-2 bg-[#3c2f2f] hover:bg-[#5a3d2a] text-[#fdfbf7] rounded-xl transition-all shadow-md flex items-center justify-center cursor-pointer focus:outline-none">
                      <svg className="w-4.5 h-4.5" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>
                  </button>
              </form>
          </div>
        </div>
      )}
    </div>
  );
};
