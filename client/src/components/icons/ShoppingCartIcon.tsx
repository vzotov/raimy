interface ShoppingCartIconProps {
  className?: string;
}

export default function ShoppingCartIcon({
  className = '',
}: ShoppingCartIconProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <path
        d="M2 3H4.5L5.5 5M5.5 5L8 14H18L21 5H5.5Z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="9" cy="19" r="2" fill="currentColor" />
      <circle cx="17" cy="19" r="2" fill="currentColor" />
    </svg>
  );
}
