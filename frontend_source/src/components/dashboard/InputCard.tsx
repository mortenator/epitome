import { ArrowUp, X, FileText, Loader2 } from "lucide-react";
import { useState, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { generateWorkbook } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

export function InputCard() {
  const [message, setMessage] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();
  const { toast } = useToast();

  const handleSubmit = async () => {
    if (!message.trim() && !file) return;

    setIsSubmitting(true);
    try {
      const { job_id } = await generateWorkbook(message, file || undefined);
      // Navigate to loading page with job_id and prompt
      const params = new URLSearchParams({ job: job_id });
      // Include prompt in URL params if provided (will be used for display)
      const promptText = message.trim() || '';
      if (promptText) {
        params.set('prompt', promptText);
      }
      navigate(`/loading?${params.toString()}`);
    } catch (error) {
      console.error('Failed to start generation:', error);
      toast({
        title: "Generation Failed",
        description: error instanceof Error ? error.message : "Something went wrong",
        variant: "destructive",
      });
      setIsSubmitting(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey && (message.trim() || file)) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      const validExtensions = ['.csv', '.pdf', '.txt', '.xlsx', '.xls'];
      const ext = droppedFile.name.toLowerCase().slice(droppedFile.name.lastIndexOf('.'));
      if (validExtensions.includes(ext)) {
        setFile(droppedFile);
      } else {
        toast({
          title: "Invalid File Type",
          description: "Please upload a CSV, PDF, TXT, or Excel file",
          variant: "destructive",
        });
      }
    }
  }, [toast]);

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
    }
  };

  const removeFile = () => {
    setFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const canSubmit = (message.trim() || file) && !isSubmitting;

  return (
    <motion.div
      className={`w-full max-w-3xl lg:max-w-4xl xl:max-w-5xl rounded-3xl bg-white shadow-[0px_1px_3px_0px_rgba(0,0,0,0.1),0px_1px_2px_-1px_rgba(0,0,0,0.1)] transition-all ${
        isDragging ? 'ring-2 ring-nav-active ring-offset-2' : ''
      }`}
      initial={{ y: 60, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{
        duration: 0.5,
        ease: [0.25, 0.46, 0.45, 0.94],
        delay: 1.8
      }}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".csv,.pdf,.txt,.xlsx,.xls"
        onChange={handleFileInputChange}
        className="hidden"
      />

      {/* Drop Zone Area */}
      <div
        className={`flex flex-col items-center justify-center px-6 py-8 bg-gradient-to-t from-[#f9fafb] to-transparent cursor-pointer transition-colors ${
          isDragging ? 'bg-nav-active/5' : ''
        }`}
        onClick={() => fileInputRef.current?.click()}
      >
        {file ? (
          // File preview
          <div className="flex items-center gap-3 px-4 py-3 bg-white rounded-xl border border-gray-200 shadow-sm">
            <FileText className="h-8 w-8 text-nav-active" />
            <div className="flex flex-col">
              <span className="text-sm font-medium text-foreground">{file.name}</span>
              <span className="text-xs text-nav-inactive">
                {(file.size / 1024).toFixed(1)} KB
              </span>
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation();
                removeFile();
              }}
              className="p-1 hover:bg-gray-100 rounded-full transition-colors"
            >
              <X className="h-4 w-4 text-nav-inactive" />
            </button>
          </div>
        ) : (
          <>
            {/* Upload Icon */}
            <div className="mb-6">
              <svg width="64" height="64" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path
                  d="M50 2V12.6667C50 14.0812 49.4381 15.4377 48.4379 16.4379C47.4377 17.4381 46.0812 18 44.6667 18H7.33333C5.91885 18 4.56229 17.4381 3.5621 16.4379C2.5619 15.4377 2 14.0812 2 12.6667V2"
                  stroke={isDragging ? "#4F46E5" : "#99A1AF"}
                  strokeWidth="4"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  transform="translate(7, 43)"
                />
                <path
                  d="M28.6667 15.3333L15.3333 2L2 15.3333"
                  stroke={isDragging ? "#4F46E5" : "#99A1AF"}
                  strokeWidth="4"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  transform="translate(17, 11)"
                />
                <path
                  d="M2 2V34"
                  stroke={isDragging ? "#4F46E5" : "#99A1AF"}
                  strokeWidth="4"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  transform="translate(30.3, 11)"
                />
              </svg>
            </div>

            {/* Help Text */}
            <div className="text-center text-nav-inactive text-base leading-7">
              <p>{isDragging ? 'Drop your file here' : 'Drop your crew list for a call sheet'}</p>
              <p>or, describe your shoot</p>
            </div>
          </>
        )}
      </div>

      {/* Text Input Area */}
      <div className="px-6 pb-4">
        <div className="flex items-end gap-4">
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Describe your shoot here..."
            className="flex-1 resize-none bg-transparent text-lg text-foreground placeholder:text-nav-inactive focus:outline-none min-h-[60px]"
            rows={2}
            disabled={isSubmitting}
          />
          <button
            onClick={handleSubmit}
            className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-full transition-colors ${
              canSubmit
                ? "bg-nav-active text-white hover:bg-nav-active/90"
                : "bg-[#d1d5dc] text-white cursor-not-allowed"
            }`}
            disabled={!canSubmit}
          >
            {isSubmitting ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <ArrowUp className="h-5 w-5" />
            )}
          </button>
        </div>
      </div>
    </motion.div>
  );
}
