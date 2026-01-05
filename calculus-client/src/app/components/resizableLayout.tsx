"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { IoChevronBack, IoChevronForward } from "react-icons/io5";

interface ResizableLayoutProps {
  leftChild: React.ReactNode;
  rightChild: React.ReactNode;
  rightVisible: boolean;
  onRightToggle: () => void;
  defaultLeftWidth?: number; // Percentage
  defaultRightWidth?: number; // Percentage
}

export default function ResizableLayout({
  leftChild,
  rightChild,
  rightVisible,
  onRightToggle,
  defaultLeftWidth = 70,
  defaultRightWidth = 30,
}: ResizableLayoutProps) {
  const [leftWidth, setLeftWidth] = useState(defaultLeftWidth);
  const [rightWidth, setRightWidth] = useState(defaultRightWidth);
  const [isResizing, setIsResizing] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const handleMouseDown = useCallback(() => {
    setIsResizing(true);
  }, []);

  const handleMouseMove = useCallback(
    (e: MouseEvent) => {
      if (!isResizing || !containerRef.current) return;

      const container = containerRef.current;
      const containerWidth = container.offsetWidth;
      const mouseX = e.clientX - container.getBoundingClientRect().left;
      const newLeftWidth = (mouseX / containerWidth) * 100;

      // Constrain between 20% and 80%
      const constrainedLeftWidth = Math.max(20, Math.min(80, newLeftWidth));
      const constrainedRightWidth = 100 - constrainedLeftWidth;

      setLeftWidth(constrainedLeftWidth);
      setRightWidth(constrainedRightWidth);
    },
    [isResizing]
  );

  const handleMouseUp = useCallback(() => {
    setIsResizing(false);
  }, []);

  useEffect(() => {
    if (isResizing) {
      document.addEventListener("mousemove", handleMouseMove);
      document.addEventListener("mouseup", handleMouseUp);
      document.body.style.cursor = "col-resize";
      document.body.style.userSelect = "none";
    }

    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    };
  }, [isResizing, handleMouseMove, handleMouseUp]);

  // Reset widths when right panel visibility changes
  useEffect(() => {
    if (rightVisible) {
      setLeftWidth(defaultLeftWidth);
      setRightWidth(defaultRightWidth);
    }
  }, [rightVisible, defaultLeftWidth, defaultRightWidth]);

  return (
    <div ref={containerRef} className="flex h-full w-full relative">
      {/* Left Panel (ChatPage) */}
      <div
        className="flex-shrink-0 overflow-hidden"
        style={{ width: rightVisible ? `${leftWidth}%` : "100%" }}
      >
        {leftChild}
      </div>

      {/* Resizer */}
      {rightVisible && (
        <>
          <div
            className="w-1 bg-gray-300 hover:bg-blue-500 cursor-col-resize transition-colors flex items-center justify-center group relative z-10"
            onMouseDown={handleMouseDown}
          >
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-1 h-8 bg-gray-400 rounded group-hover:bg-blue-500 transition-colors"></div>
            </div>
          </div>

          {/* Right Panel (HelperPage) */}
          <div
            className="flex-shrink-0 overflow-hidden"
            style={{ width: `${rightWidth}%` }}
          >
            {rightChild}
          </div>
        </>
      )}

      {/* Toggle Button */}
      <button
        onClick={onRightToggle}
        className={`fixed top-4 ${
          rightVisible ? "right-4" : "right-4"
        } z-20 bg-white border border-gray-300 rounded-full p-2 shadow-md hover:shadow-lg transition-all hover:bg-gray-50`}
        title={rightVisible ? "Hide Helper" : "Show Helper"}
      >
        {rightVisible ? (
          <IoChevronForward className="w-5 h-5 text-gray-600" />
        ) : (
          <IoChevronBack className="w-5 h-5 text-gray-600" />
        )}
      </button>
    </div>
  );
}

