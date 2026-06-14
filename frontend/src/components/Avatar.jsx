import React from "react";

// Circular avatar with initials over a deterministic brand color. Author
// identity is never used for analysis — this is purely decorative.
export default function Avatar({ user, size = 44 }) {
  const color = user?.color || "#7c3aed";
  return (
    <div
      className="shrink-0 rounded-full grid place-items-center text-white font-semibold select-none"
      style={{ width: size, height: size, background: color, fontSize: size * 0.42 }}
      aria-hidden="true"
    >
      {user?.initial || "?"}
    </div>
  );
}
