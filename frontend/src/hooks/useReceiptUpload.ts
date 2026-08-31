import { useState } from 'react'
import { useNavigate } from 'react-router'
import { supabase } from '../lib/supabaseClient'
import * as receiptsApi from '../lib/api/receipts'

export function useReceiptUpload(groupId: string) {
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()

  async function upload(file: File) {
    setUploading(true)
    setError(null)
    try {
      const ext = file.name.split('.').pop() ?? 'jpg'
      const path = `${groupId}/${crypto.randomUUID()}.${ext}`

      const { error: uploadError } = await supabase.storage.from('receipts').upload(path, file)
      if (uploadError) throw uploadError

      const receipt = await receiptsApi.createReceipt(groupId, path)
      navigate(`/groups/${groupId}/receipts/${receipt.id}`, { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
      setUploading(false)
    }
  }

  return { upload, uploading, error }
}
