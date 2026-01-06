"use client";
import { useState, useRef, useEffect } from "react";
import Button from "../ui/Button";
import { IconButton } from "../ui/IconButton";
import ConfigurationDropdown from "./ConfigurationDropdown";
import useLearningPreferenceStore from "@/app/context/learningPreferenceContext";
import { useButtonsStore } from "@/app/context/buttonsStore";
import { IoDocumentAttachOutline } from "react-icons/io5";
import { IoClose } from "react-icons/io5";
import { FaBookOpen } from "react-icons/fa";


interface SearchContainerProps {
  onSearch?: (query: string, files: File[]) => void; 
  placeholder?: string;
  disabled?: boolean;
}

export default function SearchContainer({
  onSearch,
  placeholder = "Search...",
  disabled = false,
}: SearchContainerProps) {
  const [query, setQuery] = useState("");
  const [showConfigPanel, setShowConfigPanel] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const tuneButtonRef = useRef<HTMLDivElement>(null);

 
  const [files, setFiles] = useState<File[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);


  const {
    preferences,
    isLoading,
    error,
    updatePreference,
    resetPreferences,
    savePreferences,
    clearError,
    hasChanges,
  } = useLearningPreferenceStore();

  const { isCreatingLearningPlan, setCreatingLearningPlan } = useButtonsStore();

  const handleCancelLearningPlan = () => {
    setCreatingLearningPlan(false);
  };

  const adjustTextareaHeight = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
    }
  };


  useEffect(() => {
    adjustTextareaHeight();
  }, [query]);



   const handleFileButtonClick = () => {
  
    fileInputRef.current?.click();
    console.log("File button clicked");
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
   
    if ((query.trim() || files.length > 0) && onSearch) {
      onSearch(query.trim(), files);
      setQuery('');
      setFiles([]); 
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = e.target.files;
    console.log("Selected files:", selectedFiles);
    if (selectedFiles) {

      setFiles(prevFiles => {
        const newFiles = Array.from(selectedFiles);
        const existingFileNames = new Set(prevFiles.map(f => f.name));
        const uniqueNewFiles = newFiles.filter(f => !existingFileNames.has(f.name));
        return [...prevFiles, ...uniqueNewFiles];
      });
    }
    // Reset the input value to allow re-selecting the same file
   // if (e.target) e.target.value = '';
  };

  const handleRemoveFile = (indexToRemove: number) => {
    setFiles(prevFiles => prevFiles.filter((_, index) => index !== indexToRemove));
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
   
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault(); // Prevent adding a new line
      handleSubmit(e as any); // Manually trigger the submit handler
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setQuery(e.target.value);
    
  };

 
  const handleTuneClick = () => {
    setShowConfigPanel(!showConfigPanel);
    clearError(); // Clear any previous errors when opening
  };

  const closeConfigPanel = () => {
    setShowConfigPanel(false);
  };


  const applyConfiguration = async () => {
    console.log('Applied configuration:', preferences);

    const result = await savePreferences();
    
    if (result.success) {
      console.log('Configuration applied successfully');
      setShowConfigPanel(false);
    } else {
      console.error('Error applying configuration:', result.error);

    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      {/* Learning Plan Mode Indicator */}
      {isCreatingLearningPlan && (
        <div className="flex items-center justify-between bg-teal-50 border border-teal-200 rounded-t-xl px-4 py-2 mb-0">
          <div className="flex items-center gap-2">
            <FaBookOpen className="w-4 h-4 text-teal-600" />
            <span className="text-sm font-medium text-teal-700">Creating Learning Plan</span>
          </div>
          <button
            type="button"
            onClick={handleCancelLearningPlan}
            className="p-1 rounded-full hover:bg-teal-100 transition-colors text-teal-600 hover:text-teal-800"
            title="Cancel learning plan creation"
          >
            <IoClose className="w-4 h-4" />
          </button>
        </div>
      )}
      <form onSubmit={handleSubmit} className="w-full">
        <div className={`relative flex flex-col bg-white border-2 border-gray-200 p-1 transition-all duration-200 focus-within:border-black focus-within:shadow-lg focus-within:shadow-blue-100 ${
          isCreatingLearningPlan 
            ? 'rounded-b-xl rounded-t-none border-t-0 border-teal-200 focus-within:border-teal-400' 
            : 'rounded-xl'
        }`}>
          
       
          {files.length > 0 && (
            <div className="flex flex-wrap gap-2 p-2">
              {files.map((file, index) => (
                <div key={`${file.name}-${index}`} className="flex items-center justify-between bg-blue-50 text-blue-800 text-sm pl-3 pr-1 py-1 rounded-full border border-blue-200">
                  <span>{file.name}</span>
                  <button type="button" onClick={() => handleRemoveFile(index)} className="ml-2 text-blue-600 hover:text-blue-900 font-bold text-lg leading-none w-5 h-5 flex items-center justify-center rounded-full hover:bg-blue-200">&times;</button>
                </div>
              ))}
            </div>
          )}

    
          <div className="flex items-end justify-between w-full gap-2">
        
            <div className="relative flex items-center" ref={tuneButtonRef}>
              <IconButton
                icon={
                  <img
                    src="/tune.svg"
                    alt="Tune"
                    width="20"
                    height="20"
                    className={`transition-transform duration-200 ${
                      showConfigPanel ? 'rotate-90' : ''
                    }`}
                  />
                }
                onClick={handleTuneClick}
                disabled={disabled}
                title="Open search options"
                className={`mr-2 flex-shrink-0 ${
                  showConfigPanel ? 'bg-blue-50 border-blue-200' : ''
                } ${hasChanges() ? 'bg-yellow-50 border-yellow-300' : ''}`}
              />

              {hasChanges() && (
                <div className="absolute -top-1 -right-1 w-3 h-3 bg-yellow-400 rounded-full border-2 border-white"></div>
              )}

     
              <ConfigurationDropdown
                isOpen={showConfigPanel}
                onClose={closeConfigPanel}
                onApplyConfiguration={applyConfiguration}
                triggerRef={tuneButtonRef}
              />
            </div>

   
            <IconButton
              icon={<IoDocumentAttachOutline size={20} />}
              onClick={handleFileButtonClick}
              disabled={disabled}
              title="Attach documents"
              className="flex-shrink-0"
            />
          

            <input
              type="file"
              ref={fileInputRef}
              // ADD THIS onClick HANDLER
              onClick={(event) => { 
                // This resets the input's value each time the file dialog is opened.
                (event.target as HTMLInputElement).value = '';
              }}
              onChange={handleFileChange}
              className="hidden"
              accept=".pdf,.doc,.docx,.txt,.md"
              multiple // Allow selecting multiple files
            />

      
            <textarea
              ref={textareaRef}
              value={query}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              placeholder={isCreatingLearningPlan ? "Describe what you want to learn..." : placeholder}
              disabled={disabled}
              rows={1}
              className="flex-1 border-none outline-none px-2 py-3 text-base bg-transparent text-gray-700 placeholder-gray-400 disabled:opacity-60 disabled:cursor-not-allowed resize-none overflow-y-auto min-h-[44px] max-h-[200px]"
            />

          
            <Button
              type="submit"
              disabled={disabled || (!query.trim() && files.length === 0)} // Disable if no query AND no files
              title="Send message"
              variant="primary"
              className="ml-2 flex-shrink-0"
            >
              <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                className="transition-transform duration-200"
              >
                <path
                  d="M2 21L23 12L2 3V10L17 12L2 14V21Z"
                  fill="currentColor"
                />
              </svg>
            </Button>
          </div>
        </div>
      </form>
    </div>
  );
}