'use client';

import { motion } from 'framer-motion';

interface AIProcessingProps {
  text?: string;
  className?: string;
}

export const AIProcessing = ({ 
  text = "AI Processing", 
  className = "mt-8 flex items-center gap-2 text-saramsa-brand" 
}: AIProcessingProps) => {
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, x: -20 }}
      animate={{ 
        opacity: [0, 1, 0], 
        x: [-20, 20, 60] 
      }}
      transition={{
        duration: 4,
        repeat: Infinity,
        ease: "easeInOut",
        repeatDelay: 2
      }}
    >
      <span className="text-xs font-medium">{text}</span>
      <motion.div className="w-4 h-4 border-2 border-saramsa-brand rounded-full border-t-transparent animate-spin" />
    </motion.div>
  );
};
