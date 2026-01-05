"use client"

import { useState, useEffect } from "react"
import { IoMdClose } from "react-icons/io"
import { useProfileStore } from "@/app/context/profileStore"
import { ProfileData } from "@/app/api/profileApis"

interface ProfileModalProps {
  isOpen: boolean
  onClose: () => void
}

export default function ProfileModal({ isOpen, onClose }: ProfileModalProps) {
  const {
    profile,
    isSaving,
    error,
    saveProfileData,
    updateProfileData,
    hasAllRequiredFields,
    validateProfile,
    setError,
    clearError,
  } = useProfileStore()

  const [formData, setFormData] = useState<ProfileData>({
    username: "",
    dateOfBirth: "",
    country: "",
    education: "",
    motherTongue: "",
    gender: "",
    learningPace: ""
  })

  const [isEditing, setIsEditing] = useState(false)
  const [validationErrors, setValidationErrors] = useState<string[]>([])

  // Load profile data from store when modal opens or profile changes
  useEffect(() => {
    if (isOpen && profile) {
      setFormData(profile)
    } else if (isOpen && !profile) {
      // Reset form if no profile exists
      setFormData({
        username: "",
        dateOfBirth: "",
        country: "",
        education: "",
        motherTongue: "",
        gender: "",
        learningPace: ""
      })
    }
  }, [isOpen, profile])

  // Clear validation errors when form data changes
  useEffect(() => {
    if (validationErrors.length > 0) {
      setValidationErrors([])
      clearError()
    }
  }, [formData])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleSave = async () => {
    // Clear previous errors
    setValidationErrors([])
    clearError()

    // Validate data before sending
    const validation = validateProfile(formData)
    if (!validation.isValid) {
      setValidationErrors(validation.errors)
      setError(validation.errors.join(', '))
      return
    }

    // Check if profile exists (update) or is new (save)
    const isUpdate = profile !== null
    const result = isUpdate 
      ? await updateProfileData(formData)
      : await saveProfileData(formData)

    if (result.success) {
      setIsEditing(false)
      setValidationErrors([])
      console.log(`✅ Profile ${isUpdate ? 'updated' : 'saved'} successfully`)
    } else {
      setError(result.error || 'Failed to save profile')
      console.error('❌ Failed to save profile:', result.error)
    }
  }

  const handleEdit = () => {
    setIsEditing(true)
  }

  const handleCancel = () => {
    // Reload from store
    if (profile) {
      setFormData(profile)
    } else {
      setFormData({
        username: "",
        dateOfBirth: "",
        country: "",
        education: "",
        motherTongue: "",
        gender: "",
        learningPace: ""
      })
    }
    setValidationErrors([])
    clearError()
    setIsEditing(false)
  }

  if (!isOpen) return null

  return (
    <>
      {/* Backdrop with blur */}
      <div 
        className="fixed inset-0 bg-opacity-50 backdrop-blur-sm z-[100]"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="fixed inset-0 flex items-center justify-center z-[101] p-4">
        <div 
          className="bg-white rounded-lg shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto border border-gray-300"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200">
            <h2 className="text-2xl font-bold text-black">Profile</h2>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-full transition-colors duration-200"
            >
              <IoMdClose className="w-6 h-6 text-black" />
            </button>
          </div>

          {/* Content */}
          <div className="p-6">
            {/* Error Display */}
            {(error || validationErrors.length > 0) && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-700 font-medium mb-1">Please fix the following errors:</p>
                <ul className="list-disc list-inside text-sm text-red-600">
                  {validationErrors.map((err, index) => (
                    <li key={index}>{err}</li>
                  ))}
                  {error && !validationErrors.includes(error) && (
                    <li>{error}</li>
                  )}
                </ul>
              </div>
            )}

            <div className="space-y-6">
              {/* Username */}
              <div>
                <label className="block text-sm font-medium text-black mb-2">
                  Username
                </label>
                {isEditing ? (
                  <input
                    type="text"
                    name="username"
                    value={formData.username}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-black text-black bg-white"
                    placeholder="Enter your username"
                  />
                ) : (
                  <div className="w-full px-4 py-2 border border-gray-200 rounded-lg bg-gray-50 text-black">
                    {formData.username || "Not set"}
                  </div>
                )}
              </div>

              {/* Date of Birth */}
              <div>
                <label className="block text-sm font-medium text-black mb-2">
                  Date of Birth
                </label>
                {isEditing ? (
                  <input
                    type="date"
                    name="dateOfBirth"
                    value={formData.dateOfBirth}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-black text-black bg-white"
                  />
                ) : (
                  <div className="w-full px-4 py-2 border border-gray-200 rounded-lg bg-gray-50 text-black">
                    {formData.dateOfBirth || "Not set"}
                  </div>
                )}
              </div>

              {/* Country */}
              <div>
                <label className="block text-sm font-medium text-black mb-2">
                  Country
                </label>
                {isEditing ? (
                  <input
                    type="text"
                    name="country"
                    value={formData.country}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-black text-black bg-white"
                    placeholder="Enter your country"
                  />
                ) : (
                  <div className="w-full px-4 py-2 border border-gray-200 rounded-lg bg-gray-50 text-black">
                    {formData.country || "Not set"}
                  </div>
                )}
              </div>

              {/* Education */}
              <div>
                <label className="block text-sm font-medium text-black mb-2">
                  Education
                </label>
                {isEditing ? (
                  <input
                    type="text"
                    name="education"
                    value={formData.education}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-black text-black bg-white"
                    placeholder="Enter your education"
                  />
                ) : (
                  <div className="w-full px-4 py-2 border border-gray-200 rounded-lg bg-gray-50 text-black">
                    {formData.education || "Not set"}
                  </div>
                )}
              </div>

              {/* Mother Tongue */}
              <div>
                <label className="block text-sm font-medium text-black mb-2">
                  Mother Tongue
                </label>
                {isEditing ? (
                  <input
                    type="text"
                    name="motherTongue"
                    value={formData.motherTongue}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-black text-black bg-white"
                    placeholder="Enter your mother tongue"
                  />
                ) : (
                  <div className="w-full px-4 py-2 border border-gray-200 rounded-lg bg-gray-50 text-black">
                    {formData.motherTongue || "Not set"}
                  </div>
                )}
              </div>
              {/* Gender */}
              <div>
                <label className="block text-sm font-medium text-black mb-2">
                  Gender
                </label>
                {isEditing ? (
                  <select
                    name="gender"
                    value={formData.gender}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-black text-black bg-white"
                  >
                    <option value="">Select gender</option>
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Others">Others</option>
                  </select>
                ) : (
                  <div className="w-full px-4 py-2 border border-gray-200 rounded-lg bg-gray-50 text-black">
                    {formData.gender || "Not set"}
                  </div>
                )}
              </div>
              {/* Learning Pace */}
              <div>
                <label className="block text-sm font-medium text-black mb-2">
                  Learning Pace
                </label>
                {isEditing ? (
                  <select
                    name="learningPace"
                    value={formData.learningPace}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-black text-black bg-white"
                  >
                    <option value="">Select learning pace</option>
                    <option value="Low">Low</option>
                    <option value="Medium">Medium</option>
                    <option value="High">High</option>
                  </select>
                ) : (
                  <div className="w-full px-4 py-2 border border-gray-200 rounded-lg bg-gray-50 text-black">
                    {formData.learningPace || "Not set"}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end gap-3 p-6 border-t border-gray-200">
            {isEditing ? (
              <>
                <button
                  onClick={handleCancel}
                  className="px-6 py-2 border border-gray-300 text-black rounded-lg hover:bg-gray-100 transition-colors duration-200 font-medium"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSave}
                  disabled={isSaving}
                  className="px-6 py-2 bg-black text-white rounded-lg hover:bg-gray-800 transition-colors duration-200 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isSaving ? 'Saving...' : profile ? 'Update' : 'Save'}
                </button>
              </>
            ) : (
              <button
                onClick={handleEdit}
                className="px-6 py-2 bg-black text-white rounded-lg hover:bg-gray-800 transition-colors duration-200 font-medium"
              >
                Edit
              </button>
            )}
          </div>
        </div>
      </div>
    </>
  )
}

