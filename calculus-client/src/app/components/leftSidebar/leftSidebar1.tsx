"use client"

import { useState, useRef } from "react"
import { useRouter } from "next/navigation"
import {
  IoMdAdd
} from "react-icons/io"

import { FaBookOpen, FaUser, FaHistory } from "react-icons/fa";

import { GiArchiveResearch } from "react-icons/gi";
import AccountModal from "../modals/AccountModal";
import LearningList from "./LearningList";

interface SidebarItem {
  id: string
  label: string
  icon: React.ReactNode
  path?: string
  hasNotification?: boolean
}

export default function LeftSideBar1({ changeSidebarState, expanded , onProfileClick}: { changeSidebarState: () => void, expanded: boolean, onProfileClick: () => void }) {
  const router = useRouter()
  const [hasNotifications] = useState(true)
  const [activeItem, setActiveItem] = useState<string>("library")
  const [isAccountModalOpen, setIsAccountModalOpen] = useState(false)
  const accountButtonRef = useRef<HTMLButtonElement>(null)
  const [accountButtonPosition, setAccountButtonPosition] = useState({ top: 0, left: 0 })

  const navigationItems: SidebarItem[] = [
    {
      id: "learning",
      label: "learning",
      icon: <FaBookOpen className="w-6 h-6" />
    },
    {
      id: "research",
      label: "research",
      icon: <GiArchiveResearch className="w-6 h-6" />
    },
    {
      id: "history",
      label: "history",
      icon: <FaHistory className="w-6 h-6" />
    }
  ]

  const handleNavigation = (item: SidebarItem) => {
    setActiveItem(item.id)

    changeSidebarState()
    if (item.path) {
      router.push(item.path)
    }

  }

  const handleAddClick = () => {
    console.log("Add button clicked")
    changeSidebarState()
  }

  const handleNotificationClick = () => {
    console.log("Notifications clicked")
  }

  const handleAccountClick = () => {
    if (accountButtonRef.current) {
      const rect = accountButtonRef.current.getBoundingClientRect()
      setAccountButtonPosition({
        top: rect.top - 20, // Move higher up, 20px above button top
        left: rect.right + 8 // 8px gap to the right of button
      })
    }
    setIsAccountModalOpen(true)
  }

  const handleProfileClick = () => {
    onProfileClick()
  }

  const handleLogoutClick = () => {
    console.log("Logout clicked")
    // Add logout logic here
  }

  const handleUpgradeClick = () => {
    console.log("Upgrade clicked")
  }

  const handleInstallClick = () => {
    console.log("Install clicked")
  }

  return (
    <div className={`flex h-full bg-white border-r border-gray-200 w-full ${expanded ? "flex-row" : "flex-col"}`}
    
    >
      {/* Red Container - Always 80px, never shrink */}
      <div className="flex flex-col h-full w-[80px] flex-shrink-0 justify-between items-center pb-6">


       <div>
            <div className="flex items-center justify-center w-full pb-6">
              <img 
                src="/calculus2.svg" 
                alt="company logo" 
                className="w-full h-30 object-contain" 
              />
            </div>


            <div className="flex flex-col gap-2 px-2">
              {navigationItems.map((item) => (
                <button
                  key={item.id}
                  onClick={() => handleNavigation(item)}
                  className={`flex flex-col items-center justify-center gap-1 p-2 rounded-lg transition-colors duration-200 ${
                    activeItem === item.id
                      ? "bg-teal-50 text-teal-600"
                      : "text-gray-600 hover:bg-gray-100"
                  }`}
                  title={item.label}
                >
                  <span className={activeItem === item.id ? "text-teal-600" : "text-gray-600"}>
                    {item.icon}
                  </span>
                  <span className="text-xs">{item.label}</span>
                </button>
              ))}
            </div>

        </div>  

         <div>
          <button
            ref={accountButtonRef}
            onClick={handleAccountClick}
            className="flex flex-col items-center justify-center gap-1 p-2 rounded-lg transition-colors duration-200"
            title="Account"
          >
            <FaUser className="w-6 h-6" />
            <span className="text-xs">Account</span>
          </button>
         </div>


         
      </div>

      {/* Expanded Container - Only visible when expanded, takes remaining space */}
      <div 
        className={`flex-col bg-gray-50 h-full border-l border-gray-200 ${expanded ? "flex flex-1" : "hidden"}`}
      >
        {activeItem === "learning" ? (
          <LearningList onAddClick={handleAddClick} />
        ) : (
          <div className="flex items-center justify-center h-full">
            <button
              onClick={handleAddClick}
              title="Add New Interest"
              className="flex flex-col items-center gap-2 p-2 text-gray-500 hover:text-teal-600 transition-colors"
            >
              <IoMdAdd className="w-5 h-5" />
              <span className="text-xs">Add New</span>
            </button>
          </div>
        )}
      </div>

      {/* Modals */}
      <AccountModal
        isOpen={isAccountModalOpen}
        onClose={() => setIsAccountModalOpen(false)}
        onProfileClick={handleProfileClick}
        onLogoutClick={handleLogoutClick}
        position={accountButtonPosition}
      />
      
    </div>
  )
}