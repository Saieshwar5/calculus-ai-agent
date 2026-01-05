"use client";

import { FormEvent, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "../../context/auth";

export default function ForgotPassword() {
  const router = useRouter();
  const { 
    signup, 
    validateAuthData, 
    isLoading, 
    error, 
    clearError,
    isLoggedIn,
  } = useAuthStore();

  const [formData, setFormData] = useState({
    email: "",
    password: "",
    retypePassword: ""  
  });

  const [success, setSuccess] = useState<string | null>(null);

  // Redirect if already logged in
  useEffect(() => {
    if (isLoggedIn()) {
      router.push("/profile");
    }
  }, [isLoggedIn, router]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prevData) => ({
      ...prevData,
      [name]: value,
    }));
    
    // Clear error when user starts typing
    if (error) clearError();
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const { email, password, retypePassword } = formData;

    // Validate form data
    const validation = validateAuthData({ 
      email, 
      password, 
      confirmPassword: retypePassword 
    });

    if (!validation.isValid) {
      // Errors are automatically set by the store
      return;
    }

    const validData = { email, password };
    console.log("Form submitted:", validData);

    // Attempt signup
    const result = await signup(validData);

    if (result.success) {
      setSuccess("Password reset successful! Redirecting...");
      setFormData({
        email: "",
        password: "",
        retypePassword: ""
      });
      
      setTimeout(() => {
        router.push("/profile");
      }, 1500);
    }
    // Errors are automatically handled by the store
  };


  return (
      <>
      
     
      <div className="sm:mx-auto sm:w-full sm:max-w-lg">
        <h2 className="mt-10 text-center text-2xl font-bold leading-9 tracking-tight text-gray-900">
          Reset Password
        </h2>

        {error && (
          <div className="mt-4 p-3 text-red-600 bg-red-100 border border-red-300 rounded-md text-center">
            {error}
          </div>
        )}

        {success && (
          <div className="mt-4 p-3 text-green-600 bg-green-100 border border-green-300 rounded-md text-center">
            {success}
          </div>
        )}
      </div>

      <div className="mt-10 sm:mx-auto sm:w-full sm:max-w-lg">
        <form className="space-y-6" onSubmit={handleSubmit}>
          <div>
            <label
              htmlFor="email"
              className="block text-sm font-medium leading-6 text-gray-900"
            >
              Email address:
            </label>
            <div className="mt-2">
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                value={formData.email}
                onChange={handleChange}
                required
                className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset sm:text-sm sm:leading-6"
              />
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between">
              <label
                htmlFor="password"
                className="block text-sm font-medium leading-6 text-gray-900"
              >
                Password:
              </label>
            </div>
            <div className="mt-2">
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="new-password"
                value={formData.password}
                onChange={handleChange}
                required
                className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset sm:text-sm sm:leading-6"
              />
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between">
              <label
                htmlFor="retype-password"
                className="block text-sm font-medium leading-6 text-gray-900"
              >
                Retype Password:
              </label>
            </div>
            <div className="mt-2">
              <input
                id="retype-password"
                name="retypePassword"
                type="password"
                autoComplete="new-password"
                value={formData.retypePassword}
                onChange={handleChange}
                required
                className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset  sm:text-sm sm:leading-6"
              />
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={isLoading}
              className="flex w-full justify-center rounded-md bg-black px-3 py-1.5 text-sm font-semibold leading-6 text-white shadow-sm hover:bg-grey-400 focus-visible:outline focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? "Resetting password..." : "Reset Password"}
            </button>
          </div>
        </form>
      </div>
     </>
  );
}
 
