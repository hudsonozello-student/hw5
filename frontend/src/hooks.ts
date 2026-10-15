import { useEffect, useRef, useState } from "react";

const reducedMotion = () => window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false;

/** Smoothly counts a number toward its new value (used for the checking balance).
 *  The first real value (from null) shows at once; only later changes animate. */
export function useAnimatedNumber(target: number | null, durationMs = 1100): number | null {
  const [shown, setShown] = useState(target);
  const from = useRef(target);

  useEffect(() => {
    if (target === null || from.current === null || reducedMotion() || from.current === target) {
      from.current = target;
      setShown(target);
      return;
    }
    const start = performance.now();
    const begin: number = from.current;
    let frame = 0;
    const step = (now: number) => {
      const t = Math.min((now - start) / durationMs, 1);
      const eased = 1 - Math.pow(1 - t, 3);
      setShown(begin + (target - begin) * eased);
      if (t < 1) frame = requestAnimationFrame(step);
      else from.current = target;
    };
    frame = requestAnimationFrame(step);
    return () => {
      cancelAnimationFrame(frame);
      from.current = target;
    };
  }, [target, durationMs]);

  return shown;
}

/** A string that survives page reloads (the approver's name). */
export function useStoredString(key: string, initial = ""): [string, (v: string) => void] {
  const [value, setValue] = useState(() => localStorage.getItem(key) ?? initial);
  const update = (v: string) => {
    setValue(v);
    localStorage.setItem(key, v);
  };
  return [value, update];
}
