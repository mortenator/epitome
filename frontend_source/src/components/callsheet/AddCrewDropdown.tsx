import { useState, useRef, useEffect } from "react";
import { createPortal } from "react-dom";
import { Search, User, X } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export interface AvailableCrewMember {
  id: string;
  name: string;
  role: string;
  phone: string;
  email: string;
}

// Mock database of available crew members
export const availableCrewDatabase: AvailableCrewMember[] = [
  { id: "1", name: "Alex Rodriguez", role: "Camera Operator", phone: "(310) 555-0200", email: "alex.r@crew.com" },
  { id: "2", name: "Sam Chen", role: "Camera Operator", phone: "(310) 555-0201", email: "sam.c@crew.com" },
  { id: "3", name: "Jordan Williams", role: "Steadicam Operator", phone: "(310) 555-0202", email: "jordan.w@crew.com" },
  { id: "4", name: "Taylor Martinez", role: "Steadicam Operator", phone: "(310) 555-0203", email: "taylor.m@crew.com" },
  { id: "5", name: "Morgan Lee", role: "Best Boy Grip", phone: "(310) 555-0204", email: "morgan.l@crew.com" },
  { id: "6", name: "Casey Thompson", role: "Best Boy Grip", phone: "(310) 555-0205", email: "casey.t@crew.com" },
  { id: "7", name: "Riley Johnson", role: "Grip", phone: "(310) 555-0206", email: "riley.j@crew.com" },
  { id: "8", name: "Avery Brown", role: "Grip", phone: "(310) 555-0207", email: "avery.b@crew.com" },
  { id: "9", name: "Quinn Davis", role: "Grip", phone: "(310) 555-0208", email: "quinn.d@crew.com" },
  { id: "10", name: "Jamie Wilson", role: "Production Coordinator", phone: "(323) 555-0209", email: "jamie.w@crew.com" },
  { id: "11", name: "Drew Garcia", role: "Production Coordinator", phone: "(323) 555-0210", email: "drew.g@crew.com" },
  { id: "12", name: "Cameron White", role: "Production Assistant", phone: "(323) 555-0211", email: "cameron.w@crew.com" },
  { id: "13", name: "Skyler Moore", role: "2nd Production Assistant", phone: "(323) 555-0212", email: "skyler.m@crew.com" },
  { id: "14", name: "Reese Taylor", role: "Photo Assistant", phone: "(310) 555-0213", email: "reese.t@crew.com" },
  { id: "15", name: "Finley Anderson", role: "Digital Tech", phone: "(310) 555-0214", email: "finley.a@crew.com" },
  { id: "16", name: "Parker Thomas", role: "1st AC", phone: "(310) 555-0215", email: "parker.t@crew.com" },
  { id: "17", name: "Emerson Jackson", role: "2nd AC", phone: "(310) 555-0216", email: "emerson.j@crew.com" },
  { id: "18", name: "Dakota Harris", role: "DIT", phone: "(310) 555-0217", email: "dakota.h@crew.com" },
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
  const [position, setPosition] = useState({ top: 0, left: 0 });
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Calculate position based on anchor element
  useEffect(() => {
    if (isOpen && anchorRef.current) {
      const rect = anchorRef.current.getBoundingClientRect();
      setPosition({
        top: rect.bottom + window.scrollY + 4,
        left: rect.left + window.scrollX,
      });
    }
  }, [isOpen, anchorRef]);

  // Filter crew by name OR role
  const filteredCrew = availableCrewDatabase.filter((member) => {
    const query = searchQuery.toLowerCase();
    return (
      member.name.toLowerCase().includes(query) ||
      member.role.toLowerCase().includes(query)
    );
  });

  // Sort results: prioritize suggested role matches, then alphabetical
  const sortedCrew = [...filteredCrew].sort((a, b) => {
    if (suggestedRole) {
      const aMatchesRole = a.role.toLowerCase().includes(suggestedRole.toLowerCase());
      const bMatchesRole = b.role.toLowerCase().includes(suggestedRole.toLowerCase());
      if (aMatchesRole && !bMatchesRole) return -1;
      if (!aMatchesRole && bMatchesRole) return 1;
    }
    return a.name.localeCompare(b.name);
  });

  // Focus input when opened
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
      // Pre-fill with suggested role if provided
      if (suggestedRole && !searchQuery) {
        setSearchQuery(suggestedRole);
      }
    }
  }, [isOpen, suggestedRole]);

  // Reset search when closed
  useEffect(() => {
    if (!isOpen) {
      setSearchQuery("");
    }
  }, [isOpen]);

  // Close on click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node) &&
        anchorRef.current &&
        !anchorRef.current.contains(event.target as Node)
      ) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [isOpen, onClose, anchorRef]);

  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Escape") {
      onClose();
    }
  };

  const handleSelect = (member: AvailableCrewMember) => {
    onSelect(member);
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
          className="fixed w-72 rounded-lg border border-border bg-white shadow-lg"
          onKeyDown={handleKeyDown}
        >
          {/* Search Input */}
          <div className="p-2 border-b border-border">
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <input
                ref={inputRef}
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by name or role..."
                className="w-full pl-8 pr-8 py-2 text-sm rounded-md border border-border bg-white focus:outline-none focus:ring-2 focus:ring-primary/10 focus:border-border"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery("")}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>
          </div>

          {/* Results List */}
          <div className="max-h-64 overflow-y-auto">
            {sortedCrew.length > 0 ? (
              <ul className="py-1">
                {sortedCrew.map((member) => (
                  <li key={member.id}>
                    <button
                      onClick={() => handleSelect(member)}
                      className="w-full flex items-start gap-3 px-3 py-2 text-left hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center mt-0.5">
                        <User className="h-4 w-4 text-primary" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-foreground truncate">
                          {member.name}
                        </p>
                        <p className="text-xs text-muted-foreground truncate">
                          {member.role}
                        </p>
                      </div>
                    </button>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="py-6 text-center">
                <p className="text-sm text-muted-foreground">No crew members found</p>
                <p className="text-xs text-muted-foreground mt-1">Try a different search term</p>
              </div>
            )}
          </div>

          {/* Footer hint */}
          <div className="px-3 py-2 border-t border-border bg-gray-50 rounded-b-lg">
            <p className="text-xs text-muted-foreground">
              Search by name or role (e.g., "camera operator")
            </p>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );

  return createPortal(dropdownContent, document.body);
}
