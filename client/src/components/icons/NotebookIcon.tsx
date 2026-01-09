interface NotebookIconProps {
  className?: string;
}

export default function NotebookIcon({ className = '' }: NotebookIconProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <path
        d="M7 3.75H17C17.9665 3.75 18.75 4.5335 18.75 5.5V18.5C18.75 19.4665 17.9665 20.25 17 20.25H7C6.0335 20.25 5.25 19.4665 5.25 18.5V5.5C5.25 4.5335 6.0335 3.75 7 3.75Z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M9 8.5H15M9 12H15M9 15.5H13"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M5.25 7H4.75C4.33579 7 4 7.33579 4 7.75V8.25C4 8.66421 4.33579 9 4.75 9H5.25"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M5.25 11H4.75C4.33579 11 4 11.3358 4 11.75V12.25C4 12.6642 4.33579 13 4.75 13H5.25"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M5.25 15H4.75C4.33579 15 4 15.3358 4 15.75V16.25C4 16.6642 4.33579 17 4.75 17H5.25"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
