import Button from './Button';
import { ReactNode } from 'react';

interface IconButtonProps {
  icon: ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  title?: string;
  variant?: 'primary' | 'secondary';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function IconButton({
  icon,
  onClick,
  disabled = false,
  title,
  variant = 'secondary',
  size = 'md',
  className = '',
}: IconButtonProps) {
  return (
    <Button
      onClick={onClick}
      disabled={disabled}
      title={title}
      variant={variant}
      size={size}
      shape="rounded"
      className={className}
    >
      {icon}
    </Button>
  );
}