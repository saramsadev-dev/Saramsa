'use client';

import { motion } from 'framer-motion';

export const AINodes = () => {
  const nodes = [
    { id: 1, x: 60, y: 100, delay: 0 },
    { id: 2, x: 180, y: 180, delay: 0.5 },
    { id: 3, x: 120, y: 320, delay: 1 },
    { id: 4, x: 280, y: 240, delay: 1.5 },
  ];

  return (
    <div className="absolute inset-0 overflow-hidden">
      {nodes.map((node) => (
        <motion.div
          key={node.id}
          className="absolute"
          style={{ left: node.x, top: node.y }}
          initial={{ scale: 0, opacity: 0 }}
          animate={{ 
            scale: 1, 
            opacity: 1 
          }}
          transition={{
            duration: 1.5,
            delay: node.delay
          }}
        >
          <div className="relative">
            <div className="absolute inset-0 w-8 h-8 bg-saramsa-brand/20 rounded-full blur-xl animate-pulse-glow" />
            <div className="relative w-8 h-8 bg-gradient-to-br from-saramsa-brand/30 to-saramsa-gradient-to/30 rounded-full border border-saramsa-brand/50 backdrop-blur-sm flex items-center justify-center">
              <div className="w-3 h-3 bg-saramsa-brand rounded-full" />
            </div>
            <motion.div
              className="absolute inset-0 w-8 h-8 border-2 border-saramsa-brand/40 rounded-full"
              animate={{ 
                scale: [1, 1.8], 
                opacity: [0.8, 0] 
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                delay: node.delay
              }}
            />
          </div>
        </motion.div>
      ))}
    </div>
  );
};
