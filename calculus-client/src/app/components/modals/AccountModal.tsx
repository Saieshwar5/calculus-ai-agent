"use client"

import { useEffect, useState } from "react"
import { createPortal } from "react-dom"
import { useRouter } from "next/navigation"
import { FaUser, FaSignOutAlt, FaSignInAlt } from "react-icons/fa"
import { useAuthStore } from "@/app/context/auth"

interface AccountModalProps {
  isOpen: boolean
  onClose: () => void
  onProfileClick: () => void
  onLogoutClick: () => void
  position: { top: number; left: number }
}

export default function AccountModal({ isOpen, onClose, onProfileClick, onLogoutClick, position }: AccountModalProps) {
  const [mounted, setMounted] = useState(false)
  const router = useRouter()
  const { isLoggedIn, logout } = useAuthStore()
  const isAuthenticated = isLoggedIn()

  // Ensure we only render portal on client side
  useEffect(() => {
    setMounted(true)
    return () => setMounted(false)
  }, [])

  if (!isOpen || !mounted) return null

  const handleProfileClick = () => {
    console.log("Profile clicked")
    onProfileClick()
    onClose()
  }

  const handleSignInClick = () => {
    console.log("Sign In clicked")
    onClose()
    router.push("/signin")
  }

  const handleLogoutClick = async () => {
    console.log("Logout clicked")
    try {
      await logout()
      onLogoutClick()
      onClose()
    } catch (error) {
      console.error("Logout error:", error)
      // Still close modal even if logout fails
      onClose()
    }
  }

  const modalContent = (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0  bg-opacity-10 z-[9998]"
        onClick={onClose}
      />
      
      {/* Modal - positioned next to account button */}
      <div 
        className="fixed bg-white rounded-lg shadow-xl z-[9999] min-w-[220px] border border-gray-200"
        style={{
          top: `${position.top}px`,
          left: `${position.left}px`
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex flex-col w-full">
          {isAuthenticated && (
            <button
              onClick={handleProfileClick}
              type="button"
              className="flex items-center gap-3 px-4 py-3 hover:bg-gray-100 transition-colors duration-200 border-b border-gray-200 w-full text-left cursor-pointer"
            >
              <FaUser className="w-5 h-5 text-black flex-shrink-0 pointer-events-none" />
              <span className="text-sm text-black font-medium pointer-events-none">Profile</span>
            </button>
          )}
          
          {isAuthenticated ? (
            <button
              onClick={handleLogoutClick}
              type="button"
              className="flex items-center gap-3 px-4 py-3 hover:bg-gray-100 transition-colors duration-200 w-full text-left cursor-pointer"
            >
              <FaSignOutAlt className="w-5 h-5 text-black flex-shrink-0 pointer-events-none" />
              <span className="text-sm text-black font-medium pointer-events-none">Logout</span>
            </button>
          ) : (
            <button
              onClick={handleSignInClick}
              type="button"
              className="flex items-center gap-3 px-4 py-3 hover:bg-gray-100 transition-colors duration-200 w-full text-left cursor-pointer"
            >
              <FaSignInAlt className="w-5 h-5 text-black flex-shrink-0 pointer-events-none" />
              <span className="text-sm text-black font-medium pointer-events-none">Sign In</span>
            </button>
          )}
        </div>
      </div>
    </>
  )

  // Use portal to render modal at document.body level, escaping stacking context
  return createPortal(modalContent, document.body)
}

