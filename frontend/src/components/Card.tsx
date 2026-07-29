import React from "react";
import { cn } from "../utils/cn";

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  variant?: "default" | "blue" | "purple" | "emerald" | "pink" | "bordered";
  hoverable?: boolean;
  className?: string;
  key?: React.Key;
}

export function Card({
  children,
  variant = "default",
  hoverable = false,
  className,
  ...props
}: CardProps) {
  const variantStyles = {
    default: "bg-white border border-gray-100 shadow-sm",
    bordered: "bg-white border border-gray-200/80 shadow-sm",
    blue: "bento-card bento-card-blue bg-blue-50/50 border border-blue-100/50",
    purple: "bento-card bento-card-purple bg-purple-50/50 border border-purple-100/50",
    emerald: "bento-card bento-card-emerald bg-emerald-50/50 border border-emerald-100/50",
    pink: "bento-card bento-card-pink bg-pink-50/50 border border-pink-100/50",
  };

  return (
    <div
      className={cn(
        "rounded-3xl p-6 transition-all duration-300 relative overflow-hidden",
        variantStyles[variant],
        hoverable && "hover:shadow-md hover:border-gray-200 cursor-pointer",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardHeader({
  children,
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("flex items-center justify-between border-b border-gray-50 pb-4 mb-4", className)} {...props}>
      {children}
    </div>
  );
}

export function CardTitle({
  children,
  className,
  ...props
}: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3 className={cn("font-display font-bold text-sm text-gray-900 leading-none", className)} {...props}>
      {children}
    </h3>
  );
}

export function CardContent({
  children,
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("text-xs text-gray-600 leading-normal", className)} {...props}>
      {children}
    </div>
  );
}
