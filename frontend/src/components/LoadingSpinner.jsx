export default function LoadingSpinner({ message }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-12">
      <svg
        className="animate-spin"
        width="36"
        height="36"
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden
      >
        <circle cx="12" cy="12" r="10" stroke="rgba(255,255,255,0.12)" strokeWidth="3" />
        <path
          d="M12 2a10 10 0 0 1 10 10"
          stroke="rgba(255,255,255,0.75)"
          strokeWidth="3"
          strokeLinecap="round"
        />
      </svg>
      {message ? <p className="text-sm text-white/45">{message}</p> : null}
    </div>
  )
}
