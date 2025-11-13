'use client';

import { motion } from 'framer-motion';

interface TaskCardsProps {
  variant?: 'login' | 'register';
}

export const TaskCards = ({ variant = 'login' }: TaskCardsProps) => {
  const tasks = variant === 'login' 
    ? [
        { id: 1, title: "Improve checkout flow", priority: "High", type: "Feature", x: 40, y: 600, delay: 0 },
        { id: 2, title: "Fix payment bug", priority: "Critical", type: "Bug", x: 440, y: 600, delay: 1 },
        { id: 3, title: "Add user analytics", priority: "Medium", type: "Task", x: 240, y: 600, delay: 2 }
      ]
    : [
        { id: 1, title: "Setup workspace", priority: "High", type: "Setup", x: 50, y: 140, delay: 0 },
        { id: 2, title: "Configure AI", priority: "Medium", type: "Config", x: 180, y: 220, delay: 1 }
      ];

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'Critical': return 'bg-red-500';
      case 'High': return 'bg-orange-500';
      case 'Medium': return 'bg-yellow-500';
      default: return 'bg-green-500';
    }
  };

  return (
    <div className="absolute inset-0 overflow-hidden">
      {tasks.map((task) => (
        <motion.div
          key={task.id}
          className="absolute"
          style={{ left: task.x, top: task.y }}
          initial={{ scale: 0, opacity: 0, rotateY: -90 }}
          animate={{ 
            scale: 1, 
            opacity: 1, 
            rotateY: 0,
            y: [0, -10, 0] 
          }}
          transition={{
            scale: { duration: 0.8, delay: task.delay },
            opacity: { duration: 0.8, delay: task.delay },
            rotateY: { duration: 0.8, delay: task.delay },
            y: {
              duration: 3,
              repeat: Infinity,
              ease: "easeInOut",
              delay: task.delay + 1
            }
          }}
        >
          <div className="bg-card/90 backdrop-blur-md rounded-lg shadow-lg border border-border/20 p-3 w-40">
            <div className="flex items-center justify-between mb-2">
              <div className={`w-2 h-2 rounded-full ${getPriorityColor(task.priority)}`} />
              <span className="text-xs text-muted-foreground bg-muted px-2 py-1 rounded">
                {task.type}
              </span>
            </div>
            <h4 className="text-xs font-medium text-foreground mb-2 line-clamp-2">
              {task.title}
            </h4>
            <div className="absolute -top-1 -right-1">
              <motion.div 
                className="w-4 h-4 bg-saramsa-brand rounded-full flex items-center justify-center animate-glow"
                animate={{ rotate: 360 }}
                transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
              >
                <div className="w-2 h-2 bg-white rounded-full" />
              </motion.div>
            </div>
          </div>
        </motion.div>
      ))}
    </div>
  );
};
