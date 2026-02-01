import React, { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { TasksView } from './views/TasksView';
import { RunsView } from './views/RunsView';
import { WorkersView } from './views/WorkersView';
import { QueuesView } from './views/QueuesView';

function App() {
  const [activeSection, setActiveSection] = useState('runs');

  const renderContent = () => {
    switch (activeSection) {
      case 'tasks':
        return <TasksView />;
      case 'runs':
        return <RunsView />;
      case 'workers':
        return <WorkersView />;
      case 'queues':
        return <QueuesView />;
      default:
        return <RunsView />;
    }
  };

  return (
    <div className="flex min-h-screen bg-bg text-fg">
      <Sidebar 
        activeSection={activeSection} 
        onSectionChange={setActiveSection} 
      />
      <main className="flex-1 flex flex-col min-w-0">
        {renderContent()}
      </main>
    </div>
  );
}

export default App;