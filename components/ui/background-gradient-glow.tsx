import { cn } from "../../lib/utils";
import { useState } from "react";

export const Component = () => {
  const [count, setCount] = useState(0);

  return (
    <div 
      className={cn("absolute inset-0 w-full h-full -z-20")} 
      onClick={() => setCount(prev => prev + 1)}
      data-count={count}
      style={{
        background: `
          radial-gradient(ellipse 85% 65% at 8% 8%, rgba(210, 180, 140, 0.45), transparent 60%),
          radial-gradient(ellipse 75% 60% at 75% 35%, rgba(245, 222, 179, 0.65), transparent 62%),
          radial-gradient(ellipse 70% 60% at 15% 80%, rgba(160, 120, 90, 0.45), transparent 62%),
          radial-gradient(ellipse 70% 60% at 92% 92%, rgba(139, 90, 43, 0.35), transparent 62%),
          linear-gradient(180deg, #fdfbf7 0%, #eadecc 100%)
        `
      }}
    />
  );
};
