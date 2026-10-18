import type { ReactNode } from 'react'
import { PackageSearch } from 'lucide-react'

interface Props {
  title?: string
  description?: string
  icon?: ReactNode
  action?: ReactNode
}

export default function EmptyState({
  title = 'No results found',
  description = 'Try adjusting your filters.',
  icon = <PackageSearch className="h-10 w-10 text-gray-300" />,
  action,
}: Props) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center gap-3">
      {icon}
      <h3 className="text-base font-semibold text-gray-700">{title}</h3>
      <p className="text-sm text-gray-400 max-w-xs">{description}</p>
      {action}
    </div>
  )
}
