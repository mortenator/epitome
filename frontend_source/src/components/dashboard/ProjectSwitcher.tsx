import { useState } from 'react';
import { ChevronsUpDown, PlusCircle, Folder } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';

// Mock project data
const projects = [
  { id: 'proj_1', name: 'Spring \'26 Campaign - Nike' },
  { id: 'proj_2', name: '"Mirage" Music Video - FKA Twigs' },
  { id: 'proj_3', name: 'Brand Launch Event - Glossier' },
];

const currentProjectId = 'proj_1';

export function ProjectSwitcher() {
  const [isOpen, setIsOpen] = useState(false);
  const currentProject = projects.find(p => p.id === currentProjectId);

  return (
    <div className="relative px-1 mb-4">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-2 rounded-md bg-accent hover:bg-accent/80 transition-colors"
      >
        <div className="flex items-center gap-2 min-w-0">
          <Folder className="h-4 w-4 text-muted-foreground flex-shrink-0" />
          <span className="text-sm font-medium text-foreground truncate">
            {currentProject?.name || 'Select a project'}
          </span>
        </div>
        <ChevronsUpDown className="h-4 w-4 text-muted-foreground flex-shrink-0" />
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -5 }}
            transition={{ duration: 0.15 }}
            className="absolute top-full left-0 right-0 mt-2 w-full rounded-lg border border-glass-border bg-glass shadow-lg z-50 overflow-hidden"
          >
            <ul className="py-1">
              {projects.map(project => (
                <li key={project.id}>
                  <a
                    href={`/?project=${project.id}`}
                    className={cn(
                      "block w-full text-left px-3 py-1.5 text-sm hover:bg-accent transition-colors",
                      project.id === currentProjectId ? "font-semibold text-primary" : "text-foreground"
                    )}
                  >
                    {project.name}
                  </a>
                </li>
              ))}
            </ul>
            <div className="border-t border-border p-1">
              <button className="w-full flex items-center gap-2 px-3 py-1.5 text-sm text-muted-foreground hover:text-foreground hover:bg-accent rounded-sm transition-colors">
                <PlusCircle className="h-4 w-4" />
                <span>Create new project</span>
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
