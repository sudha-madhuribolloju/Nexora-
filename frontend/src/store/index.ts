// Centralized Simple Store
// Exposes micro-state controls to support deep nested component communication without prop drilling.

import { useState, useEffect } from "react";

export interface GlobalStoreState {
  activeLecturesCount: number;
  unresolvedQuizCount: number;
  workspaceVolume: number; // 0-100
}

let storeState: GlobalStoreState = {
  activeLecturesCount: 2,
  unresolvedQuizCount: 5,
  workspaceVolume: 80,
};

const listeners = new Set<(state: GlobalStoreState) => void>();

export const nexoraStore = {
  getState() {
    return storeState;
  },
  setState(newState: Partial<GlobalStoreState>) {
    storeState = { ...storeState, ...newState };
    listeners.forEach((listener) => listener(storeState));
  },
  subscribe(listener: (state: GlobalStoreState) => void) {
    listeners.add(listener);
    return () => listeners.delete(listener);
  },
};

export function useGlobalStore(): [GlobalStoreState, (state: Partial<GlobalStoreState>) => void] {
  const [state, setState] = useState(storeState);

  useEffect(() => {
    return nexoraStore.subscribe(setState);
  }, []);

  const updateState = (newState: Partial<GlobalStoreState>) => {
    nexoraStore.setState(newState);
  };

  return [state, updateState];
}
