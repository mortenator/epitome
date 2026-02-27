import { useState } from "react";
import { X, User } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { createPortal } from "react-dom";
import { AvailableCrewMember } from "./AddCrewDropdown";

interface AddCrewModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAdd: (member: AvailableCrewMember) => void;
  prefillName?: string;
  suggestedRole?: string;
}

const ROLE_SUGGESTIONS = [
  "Director of Photography",
  "Camera Operator",
  "1st AC",
  "2nd AC",
  "DIT",
  "Gaffer",
  "Key Grip",
  "Best Boy Grip",
  "Grip",
  "Production Coordinator",
  "Production Assistant",
  "Art Director",
  "Set Designer",
  "Prop Master",
  "Hair & Makeup",
  "Wardrobe Stylist",
  "Sound Mixer",
  "Boom Operator",
  "Director",
  "Producer",
  "Line Producer",
  "Production Manager",
];

export function AddCrewModal({ isOpen, onClose, onAdd, prefillName = "", suggestedRole = "" }: AddCrewModalProps) {
  const [name, setName]   = useState(prefillName);
  const [role, setRole]   = useState(suggestedRole);
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validate = () => {
    const e: Record<string, string> = {};
    if (!name.trim())  e.name  = "Name is required";
    if (!role.trim())  e.role  = "Role is required";
    return e;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length) { setErrors(errs); return; }

    onAdd({
      id: `manual_${Date.now()}`,
      name:  name.trim(),
      role:  role.trim(),
      phone: phone.trim(),
      email: email.trim(),
    });

    // Reset
    setName(""); setRole(""); setPhone(""); setEmail(""); setErrors({});
    onClose();
  };

  const handleClose = () => {
    setName(prefillName); setRole(suggestedRole);
    setPhone(""); setEmail(""); setErrors({});
    onClose();
  };

  const content = (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={handleClose}
          />

          {/* Modal */}
          <motion.div
            className="fixed left-1/2 top-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2"
            initial={{ opacity: 0, scale: 0.95, y: 12 }}
            animate={{ opacity: 1, scale: 1,    y: 0  }}
            exit={{   opacity: 0, scale: 0.95, y: 12 }}
            transition={{ duration: 0.2 }}
          >
            <div className="rounded-xl border border-glass-border bg-popover shadow-2xl p-6">
              {/* Header */}
              <div className="flex items-center justify-between mb-5">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-full bg-primary/10 flex items-center justify-center">
                    <User className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <h2 className="text-base font-semibold text-foreground">Add crew member</h2>
                    <p className="text-xs text-muted-foreground">This person will be added to the call sheet</p>
                  </div>
                </div>
                <button onClick={handleClose} className="p-1.5 rounded-md hover:bg-accent text-muted-foreground hover:text-foreground transition-colors">
                  <X className="h-4 w-4" />
                </button>
              </div>

              {/* Form */}
              <form onSubmit={handleSubmit} className="space-y-4">
                {/* Name */}
                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                    Full name <span className="text-destructive">*</span>
                  </label>
                  <input
                    autoFocus
                    type="text"
                    value={name}
                    onChange={e => { setName(e.target.value); setErrors(v => ({ ...v, name: "" })); }}
                    placeholder="e.g. Jordan Smith"
                    className={`w-full rounded-md border px-3 py-2 text-sm bg-input text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/20 ${errors.name ? "border-destructive" : "border-border"}`}
                  />
                  {errors.name && <p className="mt-1 text-xs text-destructive">{errors.name}</p>}
                </div>

                {/* Role */}
                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                    Role <span className="text-destructive">*</span>
                  </label>
                  <input
                    type="text"
                    value={role}
                    list="role-suggestions"
                    onChange={e => { setRole(e.target.value); setErrors(v => ({ ...v, role: "" })); }}
                    placeholder="e.g. Camera Operator"
                    className={`w-full rounded-md border px-3 py-2 text-sm bg-input text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/20 ${errors.role ? "border-destructive" : "border-border"}`}
                  />
                  <datalist id="role-suggestions">
                    {ROLE_SUGGESTIONS.map(r => <option key={r} value={r} />)}
                  </datalist>
                  {errors.role && <p className="mt-1 text-xs text-destructive">{errors.role}</p>}
                </div>

                {/* Phone + Email side by side */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-muted-foreground mb-1.5">Phone</label>
                    <input
                      type="tel"
                      value={phone}
                      onChange={e => setPhone(e.target.value)}
                      placeholder="(310) 555-0100"
                      className="w-full rounded-md border border-border px-3 py-2 text-sm bg-input text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-muted-foreground mb-1.5">Email</label>
                    <input
                      type="email"
                      value={email}
                      onChange={e => setEmail(e.target.value)}
                      placeholder="name@email.com"
                      className="w-full rounded-md border border-border px-3 py-2 text-sm bg-input text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
                    />
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-3 pt-1">
                  <button
                    type="button"
                    onClick={handleClose}
                    className="flex-1 rounded-md border border-border px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="flex-1 rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90 transition-colors"
                  >
                    Add to call sheet
                  </button>
                </div>
              </form>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );

  return createPortal(content, document.body);
}
