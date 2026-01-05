import Button from './Button';
import { ReactNode } from 'react';

interface ToggleButtonProps {
  children: ReactNode;
  isActive: boolean;
  onClick: () => void;
  disabled?: boolean;
  title?: string;
  size?: 'sm' | 'md' | 'lg' |'rect';
  shape?: 'rounded' | 'circle';
  className?: string;
}

export function ToggleButton({
  children,
  isActive,
  onClick,
  disabled = false,
  title,
  size = 'lg',
  shape = 'circle',
  className = '',
}: ToggleButtonProps) {
  return (
    <Button
      onClick={onClick}
      disabled={disabled}
      title={title}
      variant="toggle"
      size={size}
      shape={shape}
      isActive={isActive}
      className={className}
    >
      {children}
    </Button>
  );
}