import React from "react";
import { cn } from "../utils/cn";

interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "text" | "circular" | "rectangular";
  className?: string;
}

export function Skeleton({
  variant = "rectangular",
  className,
  ...props
}: SkeletonProps) {
  return (
    <div
      className={cn(
        "animate-pulse bg-gray-200/75",
        variant === "text" && "h-3 w-3/4 rounded",
        variant === "circular" && "rounded-full",
        variant === "rectangular" && "rounded-2xl",
        className
      )}
      {...props}
    />
  );
}

export function DashboardSkeleton() {
  return (
    <div className="space-y-8">
      {/* Visual Header Skeleton */}
      <div className="bg-white border border-gray-100 rounded-3xl p-8 flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div className="space-y-3 w-full max-w-xl">
          <Skeleton variant="text" className="w-1/4 h-2.5" />
          <Skeleton variant="text" className="w-2/3 h-6" />
          <Skeleton variant="text" className="w-full h-3" />
        </div>
        <Skeleton variant="rectangular" className="w-36 h-20 shrink-0" />
      </div>

      {/* Grid Skeletons */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-white border border-gray-100 rounded-3xl p-6 space-y-4">
            <Skeleton variant="text" className="w-1/3 h-2.5" />
            <Skeleton variant="text" className="w-3/4 h-4" />
            <Skeleton variant="text" className="w-1/2 h-3" />
          </div>
        ))}
      </div>

      {/* Detail Block Skeletons */}
      <div className="bg-white border border-gray-100 rounded-3xl p-8 space-y-4">
        <Skeleton variant="text" className="w-1/5 h-4" />
        <Skeleton variant="text" className="w-full h-3" />
        <Skeleton variant="text" className="w-11/12 h-3" />
        <Skeleton variant="text" className="w-4/5 h-3" />
      </div>
    </div>
  );
}
