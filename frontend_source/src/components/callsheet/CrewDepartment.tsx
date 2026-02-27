import { ChevronDown, ChevronRight, MoreVertical, Trash2, User, Phone, EyeOff, Plus, Check, X } from "lucide-react";
import { useState, useRef } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Switch } from "@/components/ui/switch";
import { AddCrewDropdown, AvailableCrewMember } from "./AddCrewDropdown";
import { CrewMember } from "@/lib/api";

interface CrewDepartmentProps {
  name: string;
  count: number;
  crew: CrewMember[];
  expanded: boolean;
  onToggle: () => void;
  onAddPerson?: (role: string, member: AvailableCrewMember) => void;
  onUpdateCrewMember?: (index: number, field: 'callTime' | 'location', value: string) => void;
}

export function CrewDepartment({ name, count, crew, expanded, onToggle, onAddPerson, onUpdateCrewMember }: CrewDepartmentProps) {
  const [hideContactInfo, setHideContactInfo] = useState<Record<number, boolean>>({});
  const [activeDropdown, setActiveDropdown] = useState<{ type: 'role' | 'general'; role?: string; index?: number } | null>(null);
  const [editingCell, setEditingCell] = useState<{ index: number; field: 'callTime' | 'location' } | null>(null);
  const [editValue, setEditValue] = useState("");
  
  const addButtonRefs = useRef<Map<number, HTMLButtonElement>>(new Map());
  const generalAddButtonRef = useRef<HTMLButtonElement>(null);

  const toggleHideContact = (index: number) => {
    setHideContactInfo(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  const startEditing = (index: number, field: 'callTime' | 'location', currentValue?: string) => {
    setEditingCell({ index, field });
    setEditValue(currentValue || "");
  };

  const cancelEditing = () => {
    setEditingCell(null);
    setEditValue("");
  };

  const saveEditing = () => {
    if (editingCell && onUpdateCrewMember) {
      onUpdateCrewMember(editingCell.index, editingCell.field, editValue);
    }
    setEditingCell(null);
    setEditValue("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      saveEditing();
    } else if (e.key === "Escape") {
      cancelEditing();
    }
  };

  const isUnassigned = (member: CrewMember) => !member.name || member.name.trim() === "";

  const handleOpenDropdown = (type: 'role' | 'general', role?: string, index?: number) => {
    setActiveDropdown({ type, role, index });
  };

  const handleCloseDropdown = () => {
    setActiveDropdown(null);
  };

  const handleSelectMember = (member: AvailableCrewMember) => {
    if (activeDropdown?.role) {
      onAddPerson?.(activeDropdown.role, member);
    }
    handleCloseDropdown();
  };

  const getAnchorRef = () => {
    if (activeDropdown?.type === 'general') {
      return generalAddButtonRef;
    }
    if (activeDropdown?.index !== undefined) {
      const button = addButtonRefs.current.get(activeDropdown.index);
      return { current: button || null };
    }
    return { current: null };
  };

  return (
    <div className="rounded-lg border border-border bg-card">
      <button
        onClick={onToggle}
        className="flex w-full items-center gap-2 px-4 py-3 text-left hover:bg-accent"
      >
        {expanded ? (
          <ChevronDown className="h-4 w-4 text-muted-foreground" />
        ) : (
          <ChevronRight className="h-4 w-4 text-muted-foreground" />
        )}
        <span className="text-sm font-medium text-foreground">
          {name} ({count})
        </span>
      </button>

      {expanded && crew.length > 0 && (
        <div className="border-t border-border overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead className="w-[140px] md:w-[180px] text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Role
                </TableHead>
                <TableHead className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Name
                </TableHead>
                <TableHead className="hidden sm:table-cell text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Phone
                </TableHead>
                <TableHead className="hidden md:table-cell text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Email
                </TableHead>
                <TableHead className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Call Time
                </TableHead>
                <TableHead className="hidden lg:table-cell text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Loc.
                </TableHead>
                <TableHead className="w-[50px]" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {crew.map((member, index) => {
                const unassigned = isUnassigned(member);
                const isHidden = hideContactInfo[index] || false;
                return (
                <TableRow key={index} className={`group hover:bg-accent transition-opacity ${isHidden ? "opacity-40" : ""}`}>
                  <TableCell className="text-sm text-foreground">
                    <span className={isHidden ? "line-through" : ""}>{member.role}</span>
                  </TableCell>
                  <TableCell className="text-sm text-foreground relative">
                    {unassigned ? (
                      <div className="relative">
                        <button
                          ref={(el) => {
                            if (el) addButtonRefs.current.set(index, el);
                          }}
                          onClick={() => handleOpenDropdown('role', member.role, index)}
                          className="flex items-center gap-1.5 text-muted-foreground hover:text-primary transition-colors group/add"
                        >
                          <span className="flex items-center justify-center w-5 h-5 rounded-full border border-dashed border-muted-foreground/50 group-hover/add:border-primary group-hover/add:bg-primary/5 transition-colors">
                            <Plus className="h-3 w-3" />
                          </span>
                          <span className="text-xs">Add person</span>
                        </button>
                        <AddCrewDropdown
                          isOpen={activeDropdown?.type === 'role' && activeDropdown?.index === index}
                          onClose={handleCloseDropdown}
                          onSelect={handleSelectMember}
                          anchorRef={getAnchorRef()}
                          suggestedRole={member.role}
                        />
                      </div>
                    ) : (
                      <span className={isHidden ? "line-through" : ""}>{member.name}</span>
                    )}
                  </TableCell>
                  <TableCell className="hidden sm:table-cell text-sm text-muted-foreground">
                    {unassigned ? "—" : (isHidden ? "Hidden" : member.phone)}
                  </TableCell>
                  <TableCell className="hidden md:table-cell text-sm text-muted-foreground">
                    {unassigned ? "—" : (isHidden ? "Hidden" : member.email)}
                  </TableCell>
                  <TableCell className="text-sm font-medium text-primary">
                    {unassigned ? (
                      "—"
                    ) : editingCell?.index === index && editingCell?.field === 'callTime' ? (
                      <div className="flex items-center gap-1">
                        <input
                          type="text"
                          value={editValue}
                          onChange={(e) => setEditValue(e.target.value)}
                          onKeyDown={handleKeyDown}
                          className="w-20 px-1 py-0.5 text-sm border border-primary rounded focus:outline-none focus:ring-1 focus:ring-primary bg-input"
                          autoFocus
                        />
                        <button onClick={saveEditing} className="p-0.5 hover:bg-green-100/10 rounded">
                          <Check className="h-3 w-3 text-green-500" />
                        </button>
                        <button onClick={cancelEditing} className="p-0.5 hover:bg-red-100/10 rounded">
                          <X className="h-3 w-3 text-red-500" />
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => startEditing(index, 'callTime', member.callTime)}
                        className="hover:underline cursor-pointer text-left"
                      >
                        {member.callTime}
                      </button>
                    )}
                  </TableCell>
                  <TableCell className="hidden lg:table-cell text-sm text-foreground">
                    {unassigned ? (
                      "—"
                    ) : editingCell?.index === index && editingCell?.field === 'location' ? (
                      <div className="flex items-center gap-1">
                        <input
                          type="text"
                          value={editValue}
                          onChange={(e) => setEditValue(e.target.value)}
                          onKeyDown={handleKeyDown}
                          className="w-20 px-1 py-0.5 text-sm border border-primary rounded focus:outline-none focus:ring-1 focus:ring-primary bg-input"
                          autoFocus
                        />
                        <button onClick={saveEditing} className="p-0.5 hover:bg-green-100/10 rounded">
                          <Check className="h-3 w-3 text-green-500" />
                        </button>
                        <button onClick={cancelEditing} className="p-0.5 hover:bg-red-100/10 rounded">
                          <X className="h-3 w-3 text-red-500" />
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => startEditing(index, 'location', member.location)}
                        className="hover:underline cursor-pointer text-left"
                      >
                        {member.location}
                      </button>
                    )}
                  </TableCell>
                  <TableCell className="text-right">
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <button className="h-8 w-8 rounded-md p-0 opacity-0 hover:bg-accent group-hover:opacity-100 transition-opacity flex items-center justify-center">
                          <MoreVertical className="h-4 w-4 text-muted-foreground" />
                        </button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end" className="w-72 bg-popover z-50">
                        <DropdownMenuItem className="flex items-center gap-2 cursor-pointer">
                          <User className="h-4 w-4" />
                          <span>See Profile</span>
                        </DropdownMenuItem>
                        <DropdownMenuItem className="flex items-center gap-2 cursor-pointer">
                          <Phone className="h-4 w-4" />
                          <span>Contact</span>
                        </DropdownMenuItem>
                        <div 
                          className="flex items-center justify-between px-2 py-1.5 text-sm cursor-pointer hover:bg-accent rounded-sm"
                          onClick={(e) => {
                            e.preventDefault();
                            e.stopPropagation();
                            toggleHideContact(index);
                          }}
                        >
                          <div className="flex items-center gap-2">
                            <EyeOff className="h-4 w-4" />
                            <span>Hide contact info on export</span>
                          </div>
                          <Switch 
                            checked={hideContactInfo[index] || false}
                            onCheckedChange={(checked) => {
                              setHideContactInfo(prev => ({
                                ...prev,
                                [index]: checked
                              }));
                            }}
                            onClick={(e) => e.stopPropagation()}
                            className="data-[state=unchecked]:bg-muted"
                          />
                        </div>
                        <DropdownMenuItem className="flex items-center gap-2 cursor-pointer text-red-600 focus:text-red-600">
                          <Trash2 className="h-4 w-4 text-red-600" />
                          <span>Delete</span>
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
                );
              })}
            </TableBody>
          </Table>
          
          {/* Add Crew Member Button */}
          <div className="border-t border-border px-4 py-3 relative">
            <button 
              ref={generalAddButtonRef}
              onClick={() => handleOpenDropdown('general', undefined, -1)}
              className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              <Plus className="h-4 w-4" />
              <span>Add crew member</span>
            </button>
            <AddCrewDropdown
              isOpen={activeDropdown?.type === 'general'}
              onClose={handleCloseDropdown}
              onSelect={handleSelectMember}
              anchorRef={generalAddButtonRef}
            />
          </div>
        </div>
      )}
    </div>
  );
}
