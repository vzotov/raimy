interface HourglassIconProps {
  className?: string;
}

export default function HourglassIcon({ className = '' }: HourglassIconProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <path
        d="M6.75 4.5H17.25"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M6.75 19.5H17.25"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M8.25 4.5V7.5C8.25 9.15685 9.59315 10.5 11.25 10.5H12.75C14.4069 10.5 15.75 9.15685 15.75 7.5V4.5"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M8.25 19.5V16.5C8.25 14.8431 9.59315 13.5 11.25 13.5H12.75C14.4069 13.5 15.75 14.8431 15.75 16.5V19.5"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M11.25 10.5C10.5596 11.1904 10.5 12 10.5 12C10.5 12 10.5596 12.8096 11.25 13.5"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M12.75 10.5C13.4404 11.1904 13.5 12 13.5 12C13.5 12 13.4404 12.8096 12.75 13.5"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
