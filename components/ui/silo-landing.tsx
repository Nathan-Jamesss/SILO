import React from 'react';
import { MorphicBackground } from './morphic-background';
import { Component as BackgroundGradientGlow } from './background-gradient-glow';

export const SiloLanding: React.FC = () => {
  return (
    <div className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden selection:bg-[#6f4e37]/20 selection:text-[#3c2f2f]">
      
      {/* 1. Base Gradient Canvas (Warm Beige-Coffee Aurora Glow) */}
      <BackgroundGradientGlow />

      {/* 2. Secondary Layer: Dynamic flowing morphic coffee bubbles (darker #5a3d2a) */}
      <MorphicBackground 
        ballColor="#5a3d2a" 
        className="absolute inset-0 -z-10 pointer-events-none" 
      />

      {/* 3. Decorative Radial Screen Overlay for premium focus */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_rgba(255,255,255,0.1),_transparent_80%)] -z-10 pointer-events-none" />

      {/* 4. Frosted Glass Centerpiece (Highly translucent glassmorphism, not opaque!) */}
      <div className="relative z-10 max-w-3xl mx-4 px-8 py-14 md:py-16 md:px-16 text-center bg-white/10 dark:bg-black/5 backdrop-blur-2xl border border-white/20 dark:border-white/5 rounded-[2.5rem] shadow-2xl flex flex-col items-center justify-center transition-all duration-300 hover:shadow-3xl hover:bg-white/15">
        
        {/* SILO wordmark logo styled in high-end editorial Ivory-like Serif font */}
        <h1 className="text-8xl sm:text-9xl md:text-[8rem] font-light font-serif tracking-[0.06em] text-[#3c2f2f] mb-3 drop-shadow-sm select-none">
          SILO
        </h1>

        {/* SILO Full Form Subheader - Set to one line */}
        <h2 className="text-sm sm:text-base font-bold uppercase tracking-[0.25em] text-[#6f4e37] mb-8 w-full whitespace-nowrap leading-relaxed font-sans">
          Startup Intelligence for Launch & Outreach
        </h2>

        {/* Simplified Tagline (Simpler, efficient, and no em-dash) */}
        <p className="text-lg sm:text-xl text-[#3c2f2f]/90 font-light leading-relaxed max-w-2xl mb-12 font-sans tracking-wide">
          Find what to build, move forward, secure funding, and map projections in one complete startup pack.
        </p>

        {/* Call to Action: View Dashboard */}
        <div className="w-full flex justify-center">
          <a
            href="http://localhost:8000"
            className="group relative w-full sm:w-auto px-10 py-5 rounded-2xl bg-[#3c2f2f] text-[#fdfbf7] font-bold text-lg sm:text-xl shadow-xl hover:shadow-2xl hover:bg-[#5a3d2a] hover:scale-105 active:scale-95 transition-all flex items-center justify-center gap-3 border border-[#3c2f2f]/20"
          >
            <span>View Intelligence Dashboard</span>
            <svg 
              className="w-6 h-6 transform group-hover:translate-x-1 transition-transform stroke-2" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M14 5l7 7m0 0l-7 7m7-7H3" />
            </svg>
          </a>
        </div>
      </div>
      
    </div>
  );
};
