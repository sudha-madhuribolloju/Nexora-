import React from "react";
import { SYSTEM_VERSION } from "../constants";

export default function Footer() {
  return (
    <footer className="py-6 px-10 border-t border-gray-100 bg-white/50 text-center sm:flex sm:items-center sm:justify-between text-[11px] text-gray-400 font-medium">
      <div className="space-y-1 sm:space-y-0 sm:flex sm:items-center sm:gap-4">
        <span>St. Mary’s Digital Hub Portal</span>
        <span className="hidden sm:inline text-gray-200">|</span>
        <span className="font-mono text-[10px]">Release {SYSTEM_VERSION} (Stable)</span>
      </div>
      <div className="mt-2 sm:mt-0">
        <span>© 2026 NEXORA AI Inc. All rights preserved.</span>
      </div>
    </footer>
  );
}
