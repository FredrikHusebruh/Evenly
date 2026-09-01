import { useRef } from 'react'
import { useParams } from 'react-router'
import { Camera } from 'lucide-react'
import { useReceiptUpload } from '../hooks/useReceiptUpload'

export function ReceiptCapturePage() {
  const { groupId } = useParams<{ groupId: string }>()
  const { upload, uploading, error } = useReceiptUpload(groupId!)
  const inputRef = useRef<HTMLInputElement>(null)

  return (
    <div className="mx-auto flex max-w-sm flex-col items-center gap-6 py-16 text-center">
      <h1 className="text-xl font-semibold tracking-tight">Add a receipt</h1>
      <p className="text-sm text-muted">Take a photo or choose an image of the receipt.</p>

      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        capture="environment"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0]
          if (file) upload(file)
        }}
      />

      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        disabled={uploading}
        className="flex w-full items-center justify-center gap-2 rounded-md bg-accent px-4 py-3 text-sm font-medium text-white transition-colors hover:bg-accent-hover disabled:opacity-60"
      >
        <Camera className="h-4 w-4" strokeWidth={1.75} />
        {uploading ? 'Uploading…' : 'Take photo / choose image'}
      </button>

      {error && <p className="text-sm text-owed">{error}</p>}
    </div>
  )
}
