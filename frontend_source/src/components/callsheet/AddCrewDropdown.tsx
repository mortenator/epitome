import { useState, useRef, useEffect } from "react";
import { createPortal } from "react-dom";
import { Search, User, X, PlusCircle } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { AddCrewModal } from "./AddCrewModal";

export interface AvailableCrewMember {
  id: string;
  name: string;
  role: string;
  phone: string;
  email: string;
}

export const availableCrewDatabase: AvailableCrewMember[] = [
  { id: "1",  name: "Alex Rodriguez",  role: "Camera Operator",        phone: "(310) 555-0200", email: "alex.r@crew.com" },
  { id: "2",  name: "Sam Chen",         role: "Camera Operator",        phone: "(310) 555-0201", email: "sam.c@crew.com" },
  { id: "3",  name: "Jordan Williams",  role: "Steadicam Operator",     phone: "(310) 555-0202", email: "jordan.w@crew.com" },
  { id: "4",  name: "Taylor Martinez",  role: "Steadicam Operator",     phone: "(310) 555-0203", email: "taylor.m@crew.com" },
  { id: "5",  name: "Morgan Lee",       role: "Best Boy Grip",          phone: "(310) 555-0204", email: "morgan.l@crew.com" },
  { id: "6",  name: "Casey Thompson",   role: "Best Boy Grip",          phone: "(310) 555-0205", email: "casey.t@crew.com" },
  { id: "7",  name: "Riley Johnson",    role: "Grip",                   phone: "(310) 555-0206", email: "riley.j@crew.com" },
  { id: "8",  name: "Avery Brown",      role: "Grip",                   phone: "(310) 555-0207", email: "avery.b@crew.com" },
  { id: "9",  name: "Quinn Davis",      role: "Grip",                   phone: "(310) 555-0208", email: "quinn.d@crew.com" },
  { id: "10", name: "Jamie Wilson",     role: "Production Coordinator", phone: "(323) 555-0209", email: "jamie.w@crew.com" },
  { id: "11", name: "Drew Garcia",      role: "Production Coordinator", phone: "(323) 555-0210", email: "drew.g@crew.com" },
  { id: "12", name: "Cameron White",    role: "Production Assistant",   phone: "(323) 555-0211", email: "cameron.w@crew.com" },
  { id: "13", name: "Skyler Moore",     role: "2nd Production Assistant", phone: "(323) 555-0212", email: "skyler.m@crew.com" },
  { id: "14", name: "Reese Taylor",     role: "Photo Assistant",        phone: "(310) 555-0213", email: "reese.t@crew.com" },
  { id: "15", name: "Finley Anderson",  role: "Digital Tech",           phone: "(310) 555-0214", email: "finley.a@crew.com" },
  { id: "16", name: "Parker Thomas",    role: "1st AC",                 phone: "(310) 555-0215", email: "parker.t@crew.com" },
  { id: "17", name: "Emerson Jackson",  role: "2nd AC",                 phone: "(310) 555-0216", email: "emerson.j@crew.com" },
  { id: "18", name: "Dakota Harris",    role: "DIT",                    phone: "(310) 555-0217", email: "dakota.h@crew.com" },
];

interface AddCrewDropdownProps {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (member: AvailableCrewMember) => void;
  anchorRef: React.RefObject<HTMLElement>;
  suggestedRole?: string;
}

export function AddCrewDropdown({ isOpen, onClose, onSelect, anchorRef, suggestedRole }: AddCrewDropdownProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [position, setPosition]       = useState({ top: 0, left: 0 });
  const [isModalOpen, setIsModalOpen] = useState(false);

  const inputRef    = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Position dropdown below anchor
  useEffect(() => {
    if (isOpen && anchorRef.current) {
      const rect = anchorRef.current.getBoundingClientRect();
      setPosition({ top: rect.bottom + window.scrollY + 4, left: rect.left + window.scrollX });
    }
  }, [isOpen, anchorRef]);

  // Filter + sort
  const filteredCrew = availableCrewDatabase.filter(m => {
    const q = searchQuery.toLowerCase();
    return m.name.toLowerCase().includes(q) || m.role.toLowerCase().includes(q);
  });

  const sortedCrew = [...filteredCrew].sort((a, b) => {
    if (suggestedRole) {
      const aMatch = a.role.toLowerCase().includes(suggestedRole.toLowerCase());
      const bMatch = b.role.toLowerCase().includes(suggestedRole.toLowerCase());
      if (aMatch && !bMatch) return -1;
      if (!aMatch && bMatch) return 1;
    }
    return a.name.localeCompare(b.name);
  });

  // Focus + pre-fill on open
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
      if (suggestedRole && !searchQuery) setSearchQuery(suggestedRole);
    }
  }, [isOpen, suggestedRole]);

  // Reset on close
  useEffect(() => { if (!isOpen) setSearchQuery(""); }, [isOpen]);

  // Click outside
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (
        dropdownRef.current && !dropdownRef.current.contains(e.target as Node) &&
        anchorRef.current  && !anchorRef.current.contains(e.target as Node)
      ) onClose();
    };
    if (isOpen) document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [isOpen, onClose, anchorRef]);

  const handleKeyDown = (e: React.KeyboardEvent) => { if (e.key === "Escape") onClose(); };

  const handleSelect = (member: AvailableCrewMember) => { onSelect(member); onClose(); };

  const handleManualAdd = () => {
    // Close the search dropdown and open the full add modal
    // Pass the typed query as the prefill name
    setIsModalOpen(true);
    // Keep dropdown mounted so modal can portal above it; onClose called after modal closes
  };

  const handleModalAdd = (member: AvailableCrewMember) => {
    onSelect(member);
    setIsModalOpen(false);
    onClose();
  };

  const dropdownContent = (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          ref={dropdownRef}
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.15 }}
          style={{ top: position.top, left: position.left }}
          className="fixed w-72 rounded-lg border border-border bg-popover shadow-lg z-50"
          onKeyDown={handleKeyDown}
        >
          {/* Search */}
          <div className="p-2 border-b border-border">
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <input
                ref={inputRef}
                type="text"
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                placeholder="Search by name or role..."
                className="w-full pl-8 pr-8 py-2 text-sm rounded-md border bg-input border-border focus:outline-none focus:ring-2 focus:ring-primary/20"
              />
              {searchQuery && (
                <button onClick={() => setSearchQuery("")} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground">
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>
          </div>

          {/* Results */}
          <div className="max-h-64 overflow-y-auto">
            {sortedCrew.length > 0 ? (
              <ul className="py-1">
                {sortedCrew.map(member => (
                  <li key={member.id}>
                    <button
                      onClick={() => handleSelect(member)}
                      className="w-full flex items-start gap-3 px-3 py-2 text-left hover:bg-accent transition-colors"
                    >
                      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center mt-0.5">
                        <User className="h-4 w-4 text-primary" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-foreground truncate">{member.name}</p>
                        <p className="text-xs text-muted-foreground truncate">{member.role}</p>
                      </div>
                    </button>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="py-5 text-center px-3">
                <p className="text-sm text-muted-foreground">
                  {searchQuery ? `No results for "${searchQuery}"` : "No crew members found"}
                </p>
                <button
                  onClick={handleManualAdd}
                  className="mt-2 inline-flex items-center gap-1.5 text-sm font-medium text-primary hover:text-epitome-teal-light transition-colors"
                >
                  <PlusCircle className="h-4 w-4" />
                  Add {searchQuery ? `"${searchQuery}"` : "someone"} manually
                </button>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="px-3 py-2 border-t border-border bg-accent/40 rounded-b-lg flex items-center justify-between">
            <p className="text-xs text-muted-foreground">
              Not finding them? Add manually.
            </p>
            <button
              onClick={handleManualAdd}
              className="text-xs text-primary hover:text-epitome-teal-light font-medium transition-colors flex items-center gap-1"
            >
              <PlusCircle className="h-3.5 w-3.5" /> New person
            </button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );

  return (
    <>
      {createPortal(dropdownContent, document.body)}
      <AddCrewModal
        isOpen={isModalOpen}
        onClose={() => { setIsModalOpen(false); onClose(); }}
        onAdd={handleModalAdd}
        prefillName={searchQuery}
        suggestedRole={suggestedRole}
      />
    </>
  );
}
