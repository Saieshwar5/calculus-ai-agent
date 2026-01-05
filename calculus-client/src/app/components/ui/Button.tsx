import { ReactNode } from 'react';

interface ButtonProps {
  children: ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  type?: 'button' | 'submit' | 'reset';
  variant?: 'primary' | 'secondary' | 'toggle';
  size?: 'sm' | 'md' | 'lg' | 'icon' | 'rect';
  shape?: 'rounded' | 'circle' | 'square';
  isActive?: boolean;
  title?: string;
  className?: string;
}

export default function Button({
  children,
  onClick,
  disabled = false,
  type = 'button',
  variant = 'primary',
  size = 'md',
  shape = 'rounded',
  isActive = false,
  title,
  className = '',
}: ButtonProps) {
  
  // Base styles
  const baseStyles = "flex items-center justify-center font-semibold transition-all duration-200 disabled:cursor-not-allowed disabled:transform-none";
  
  // Variant styles
  const variantStyles = {
    primary: "bg-black text-white hover:bg-gray-900 hover:scale-105 active:scale-95 disabled:bg-gray-300",
    secondary: "bg-gray-100 text-gray-600 hover:bg-gray-200 hover:scale-105 active:scale-95 disabled:bg-gray-100",
    toggle: isActive 
      ? "bg-black text-white hover:bg-gray-800" 
      : "bg-gray-400 text-white hover:bg-gray-500"
  };
  
  // Size styles
  const sizeStyles = {
    sm: "w-8 h-8 text-sm",
    md: "w-10 h-10 text-base",
    lg: "w-12 h-12 text-lg",
    icon: "w-10 h-10",
    rect: "w-24 h-10 text-base"
  };
  
  // Shape styles
  const shapeStyles = {
    rounded: "rounded-lg",
    circle: "rounded-full",
    square: "rounded-none"
  };
  
  const combinedClassName = `
    ${baseStyles}
    ${variantStyles[variant]}
    ${sizeStyles[size]}
    ${shapeStyles[shape]}
    ${className}
  `.trim().replace(/\s+/g, ' ');

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      title={title}
      className={combinedClassName}
    >
      {children}
    </button>
  );
}