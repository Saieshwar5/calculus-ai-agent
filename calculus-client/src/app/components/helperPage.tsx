"use client";

import { useEffect, useRef } from "react";

interface HelperPageProps {
  isVisible: boolean;
}

// Example helper content for testing
const getExampleHelperContent = () => {
  return [
    {
      id: "helper-1",
      title: "Quick Tips",
      content: "Use the search bar to ask questions about calculus concepts, derivatives, integrals, and more.",
    },
    {
      id: "helper-2",
      title: "Document Upload",
      content: "You can upload PDF, DOC, DOCX, TXT, or MD files to get context-aware answers.",
    },
    {
      id: "helper-3",
      title: "Keyboard Shortcuts",
      content: "Press Enter to send messages. Use Shift+Enter for new lines.",
    },
    {
      id: "helper-4",
      title: "Common Questions",
      content: "Try asking about:\n• Derivatives and rules\n• Integration techniques\n• Limits and continuity\n• Series and sequences",
    },
    {
      id: "helper-5",
      title: "Study Tips",
      content: "Break down complex problems into smaller steps. Practice regularly and review previous conversations.",
    },
  ];
};

export default function HelperPage({ isVisible }: HelperPageProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  if (!isVisible) {
    return null;
  }

  const helperContent = getExampleHelperContent();

  return (
    <div
      ref={containerRef}
      className="flex-1 overflow-y-auto px-4 py-6 h-full bg-white border-l border-gray-200"
    >
      <div className="space-y-4">
        <div className="mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-2">Helper</h2>
          <p className="text-sm text-gray-500">
            Quick reference and tips for using the chat
          </p>
        </div>

        {helperContent.map((item) => (
          <div
            key={item.id}
            className="bg-gray-50 rounded-lg p-4 border border-gray-200 hover:shadow-md transition-shadow"
          >
            <h3 className="font-semibold text-gray-800 mb-2 text-sm">
              {item.title}
            </h3>
            <p className="text-xs text-gray-600 whitespace-pre-wrap">
              {item.content}
            </p>
          </div>
        ))}

        <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
          <h3 className="font-semibold text-blue-800 mb-2 text-sm">
            Need More Help?
          </h3>
          <p className="text-xs text-blue-700">
            Check the documentation or contact support for additional assistance.
          </p>
        </div>
      </div>
    </div>
  );
}

