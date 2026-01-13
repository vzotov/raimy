interface EditIconProps {
  className?: string;
}

export default function EditIcon({ className = '' }: EditIconProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <path
        d="M16.8622 3.28768L20.7123 7.13776C21.0959 7.52134 21.0959 8.14283 20.7123 8.52641L9.71229 19.5264C9.52476 19.7139 9.26844 19.8196 9.0013 19.8196H5.15122C4.59893 19.8196 4.15122 19.3719 4.15122 18.8196V14.9695C4.15122 14.7024 4.25693 14.4461 4.44447 14.2585L15.4445 3.25854C15.8281 2.87496 16.4496 2.87496 16.8332 3.25854L16.8622 3.28768Z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M13.5 5.25L18.75 10.5"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M19.5 13.5V19.125C19.5 19.6773 19.0523 20.125 18.5 20.125H5.5C4.94772 20.125 4.5 19.6773 4.5 19.125V18.75"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
