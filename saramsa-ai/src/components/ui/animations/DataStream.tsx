'use client';

import { motion } from 'framer-motion';

export const DataStream = () => {
  return (
    <div className="absolute inset-0 overflow-hidden">
      <svg className="absolute w-full h-full" viewBox="0 0 800 600" fill="none">
        <motion.path
          d="M-100 300 Q 150 100, 400 250 T 900 200"
          stroke="url(#gradient1)"
          strokeWidth="3"
          fill="none"
          initial={{ pathLength: 0, opacity: 0 }}
          animate={{ 
            pathLength: 1, 
            opacity: [0, 0.8, 0] 
          }}
          transition={{ 
            duration: 4, 
            repeat: Infinity, 
            ease: "easeInOut",
            repeatDelay: 1 
          }}
        />
        <motion.path
          d="M-50 400 Q 200 150, 450 320 T 850 280"
          stroke="url(#gradient2)"
          strokeWidth="2"
          fill="none"
          initial={{ pathLength: 0, opacity: 0 }}
          animate={{ 
            pathLength: 1, 
            opacity: [0, 0.6, 0] 
          }}
          transition={{ 
            duration: 5, 
            repeat: Infinity, 
            ease: "easeInOut",
            repeatDelay: 0.5,
            delay: 1 
          }}
        />
        {Array.from({ length: 8 }, (_, i) => (
          <motion.circle
            key={i}
            r="4"
            fill="var(--saramsa-brand)"
            initial={{ opacity: 0 }}
            animate={{
              opacity: [0, 1, 0],
              cx: [-50, 400, 850],
              cy: [300 + i * 20, 250 - i * 10, 200 + i * 15]
            }}
            transition={{
              duration: 6,
              repeat: Infinity,
              delay: i * 0.3,
              ease: "easeInOut"
            }}
            className="animate-pulse-glow"
          />
        ))}
        <defs>
          <linearGradient id="gradient1" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="var(--saramsa-brand)" stopOpacity="0" />
            <stop offset="50%" stopColor="var(--saramsa-brand)" stopOpacity="0.8" />
            <stop offset="100%" stopColor="var(--saramsa-gradient-to)" stopOpacity="0" />
          </linearGradient>
          <linearGradient id="gradient2" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="var(--saramsa-gradient-to)" stopOpacity="0" />
            <stop offset="50%" stopColor="var(--primary)" stopOpacity="0.6" />
            <stop offset="100%" stopColor="var(--saramsa-brand)" stopOpacity="0" />
          </linearGradient>
        </defs>
      </svg>
    </div>
  );
};
