import React from "react";

const S = ({ children, size = 22, stroke = 1.8, fill = "none", className = "" }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill={fill}
    stroke="currentColor"
    strokeWidth={stroke}
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
    aria-hidden="true"
  >
    {children}
  </svg>
);

export const Home = (p) => (
  <S {...p}>
    <path d="M3 10.5 12 3l9 7.5" />
    <path d="M5 9.5V21h14V9.5" />
  </S>
);
export const Hash = (p) => (
  <S {...p}>
    <path d="M5 9h14M5 15h14M9 4 7 20M17 4l-2 16" />
  </S>
);
export const Bell = (p) => (
  <S {...p}>
    <path d="M18 8a6 6 0 1 0-12 0c0 7-3 9-3 9h18s-3-2-3-9" />
    <path d="M13.7 21a2 2 0 0 1-3.4 0" />
  </S>
);
export const Mail = (p) => (
  <S {...p}>
    <rect x="3" y="5" width="18" height="14" rx="2" />
    <path d="m3 7 9 6 9-6" />
  </S>
);
export const Bookmark = (p) => (
  <S {...p}>
    <path d="M6 3h12v18l-6-4-6 4z" />
  </S>
);
export const People = (p) => (
  <S {...p}>
    <circle cx="9" cy="8" r="3" />
    <path d="M3 20c0-3 3-5 6-5s6 2 6 5" />
    <path d="M16 6a3 3 0 0 1 0 6M22 20c0-2.5-1.5-4-4-4.5" />
  </S>
);
export const Profile = (p) => (
  <S {...p}>
    <circle cx="12" cy="8" r="4" />
    <path d="M4 21c0-4 3.5-6 8-6s8 2 8 6" />
  </S>
);
export const More = (p) => (
  <S {...p}>
    <circle cx="5" cy="12" r="1.6" fill="currentColor" stroke="none" />
    <circle cx="12" cy="12" r="1.6" fill="currentColor" stroke="none" />
    <circle cx="19" cy="12" r="1.6" fill="currentColor" stroke="none" />
  </S>
);
export const Settings = (p) => (
  <S {...p}>
    <circle cx="12" cy="12" r="3" />
    <path d="M19.4 12a7.4 7.4 0 0 0-.1-1.2l2-1.6-2-3.4-2.4 1a7 7 0 0 0-2-1.2L16.5 2h-4l-.4 2.6a7 7 0 0 0-2 1.2l-2.4-1-2 3.4 2 1.6a7.4 7.4 0 0 0 0 2.4l-2 1.6 2 3.4 2.4-1a7 7 0 0 0 2 1.2l.4 2.6h4l.4-2.6a7 7 0 0 0 2-1.2l2.4 1 2-3.4-2-1.6c.07-.4.1-.8.1-1.2z" />
  </S>
);
export const Reply = (p) => (
  <S {...p}>
    <path d="M21 11.5a8.5 8.5 0 0 1-12 7.7L3 21l1.8-5.4A8.5 8.5 0 1 1 21 11.5z" />
  </S>
);
export const Repost = (p) => (
  <S {...p}>
    <path d="M4 9V7a2 2 0 0 1 2-2h11l-3-3M20 15v2a2 2 0 0 1-2 2H7l3 3" />
    <path d="M17 2l3 3-3 3M7 22l-3-3 3-3" />
  </S>
);
export const Heart = (p) => (
  <S {...p}>
    <path d="M12 20s-7-4.6-9.3-9A4.8 4.8 0 0 1 12 6a4.8 4.8 0 0 1 9.3 5C19 15.4 12 20 12 20z" />
  </S>
);
export const Share = (p) => (
  <S {...p}>
    <path d="M4 12v7a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-7" />
    <path d="M12 3v13M7 8l5-5 5 5" />
  </S>
);
export const Image = (p) => (
  <S {...p}>
    <rect x="3" y="4" width="18" height="16" rx="3" />
    <circle cx="8.5" cy="9.5" r="1.6" />
    <path d="m4 18 5-5 4 4 3-3 4 4" />
  </S>
);
export const Poll = (p) => (
  <S {...p}>
    <path d="M6 20V10M12 20V4M18 20v-7" />
  </S>
);
export const Emoji = (p) => (
  <S {...p}>
    <circle cx="12" cy="12" r="9" />
    <path d="M8.5 14a4 4 0 0 0 7 0" />
    <path d="M9 9.5h.01M15 9.5h.01" />
  </S>
);
export const Calendar = (p) => (
  <S {...p}>
    <rect x="3" y="5" width="18" height="16" rx="2" />
    <path d="M3 9h18M8 3v4M16 3v4" />
  </S>
);
export const Location = (p) => (
  <S {...p}>
    <path d="M12 21s-7-5.5-7-11a7 7 0 0 1 14 0c0 5.5-7 11-7 11z" />
    <circle cx="12" cy="10" r="2.5" />
  </S>
);
export const Globe = (p) => (
  <S {...p}>
    <circle cx="12" cy="12" r="9" />
    <path d="M3 12h18M12 3c2.5 2.5 2.5 15 0 18M12 3c-2.5 2.5-2.5 15 0 18" />
  </S>
);
export const Caret = (p) => (
  <S {...p}>
    <path d="m6 9 6 6 6-6" />
  </S>
);
export const Search = (p) => (
  <S {...p}>
    <circle cx="11" cy="11" r="7" />
    <path d="m20 20-3.5-3.5" />
  </S>
);

export const Verified = ({ size = 16, className = "" }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" className={className} aria-hidden="true">
    <path
      fill="#7c3aed"
      d="M12 1.5l2.3 1.7 2.8-.3 1.2 2.6 2.6 1.2-.3 2.8L22 12l-1.7 2.3.3 2.8-2.6 1.2-1.2 2.6-2.8-.3L12 22.5l-2.3-1.7-2.8.3-1.2-2.6-2.6-1.2.3-2.8L2 12l1.7-2.3-.3-2.8 2.6-1.2L7.2 3l2.8.3z"
    />
    <path fill="#fff" d="m10.6 14.6-2.2-2.2-1.1 1.1 3.3 3.3 6-6-1.1-1.1z" />
  </svg>
);
