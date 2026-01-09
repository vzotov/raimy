interface SaveIconProps {
  className?: string;
}

export default function SaveIcon({ className = '' }: SaveIconProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <path
        d="M17 3H7C5.89543 3 5 3.89543 5 5V21L12 17.5L19 21V5C19 3.89543 18.1046 3 17 3Z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
