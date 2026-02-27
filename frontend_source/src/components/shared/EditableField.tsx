import { useState, useRef, useEffect } from 'react';
import { Check, X } from 'lucide-react';
import { cn } from '@/lib/utils';

interface EditableFieldProps {
  initialValue: string;
  onSave: (newValue: string) => void;
  className?: string;
  inputClassName?: string;
  placeholder?: string;
}

export function EditableField({ initialValue, onSave, className, inputClassName, placeholder = "Enter value" }: EditableFieldProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [value, setValue] = useState(initialValue);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isEditing]);
  
  useEffect(() => {
    setValue(initialValue);
  }, [initialValue]);

  const handleSave = () => {
    if (value.trim() !== initialValue.trim()) {
      onSave(value);
    }
    setIsEditing(false);
  };

  const handleCancel = () => {
    setValue(initialValue);
    setIsEditing(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSave();
    } else if (e.key === 'Escape') {
      handleCancel();
    }
  };

  if (isEditing) {
    return (
      <div className={cn("flex items-center gap-1", className)}>
        <input
          ref={inputRef}
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onBlur={handleSave}
          placeholder={placeholder}
          className={cn(
            "w-full px-1 py-0.5 text-sm border rounded focus:outline-none focus:ring-1 bg-input border-primary focus:ring-primary",
            inputClassName
          )}
        />
        <button onClick={handleSave} className="p-0.5 hover:bg-green-500/10 rounded">
          <Check className="h-3 w-3 text-green-500" />
        </button>
        <button onClick={handleCancel} className="p-0.5 hover:bg-red-500/10 rounded">
          <X className="h-3 w-3 text-red-500" />
        </button>
      </div>
    );
  }

  return (
    <div
      onClick={() => setIsEditing(true)}
      className={cn("cursor-pointer hover:bg-accent p-1 -m-1 rounded transition-colors", className)}
      title="Click to edit"
    >
      {value || <span className="text-muted">{placeholder}</span>}
    </div>
  );
}
