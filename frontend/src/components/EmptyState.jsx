export default function EmptyState({ message = 'No results found.' }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div className="mb-3 text-3xl opacity-30 grayscale">🔍</div>
      <p className="max-w-xs text-sm text-white/55">{message}</p>
      <p className="mt-2 text-xs text-white/40">
        Try adjusting your filters or using a different topic.
      </p>
    </div>
  )
}
