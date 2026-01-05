// filepath: c:\my_project\calculus_p\calculus-client\src\app\(auth)\signin\page.tsx
"use client";

import { FormEvent, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "../../context/auth";

export default function SignIn() {
  const router = useRouter();
  const { 
    login, 
    isLoading, 
    error, 
    clearError,
    isLoggedIn 
  } = useAuthStore();

  const [formData, setFormData] = useState({
    email: "",
    password: "",
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
    
    const { email, password } = formData;

    // Basic validation
    if (!email || !password) {
      return;
    }

    // Attempt login
    const result = await login({ email, password });

    if (result.success) {
      setSuccess("Sign in successful! Redirecting...");
      setFormData({
        email: "",
        password: "",
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
          Sign in to your account
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
            <label htmlFor="email" className="block text-sm font-medium leading-6 text-gray-900">
              Email address
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
                className="block w-full p-2 rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-black sm:text-sm sm:leading-6"
              />
            </div>
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium leading-6 text-gray-900">
              Password
            </label>
            <div className="mt-2">
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                value={formData.password}
                onChange={handleChange}
                required
                className="block w-full p-2 rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-black sm:text-sm sm:leading-6"
              />
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={isLoading}
              className="flex w-full justify-center rounded-md bg-black px-3 py-1.5 text-sm font-semibold leading-6 text-white shadow-sm hover:bg-grey-400 focus-visible:outline focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? "Signing in..." : "Sign in"}
            </button>
          </div>
          <div className="text-sm text-center text-gray-500">
            Don't have an account?{" "}
            <a href="/join" className="font-semibold text-black hover:text-gray-800">
              Join now
            </a>
          </div>
        </form>
      </div>
    </>
  );
}