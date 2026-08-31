import { api, unwrap } from './client'

export type ReceiptFilters = {
  date_from?: string
  date_to?: string
  store?: string
  category_id?: string
}

export async function createReceipt(groupId: string, imagePath: string) {
  return unwrap(
    await api.POST('/api/v1/groups/{group_id}/receipts', {
      params: { path: { group_id: groupId } },
      body: { image_path: imagePath },
    }),
  )
}

export async function listReceipts(groupId: string, filters: ReceiptFilters = {}) {
  return unwrap(
    await api.GET('/api/v1/groups/{group_id}/receipts', {
      params: { path: { group_id: groupId }, query: filters },
    }),
  )
}

export async function getReceipt(receiptId: string) {
  return unwrap(await api.GET('/api/v1/receipts/{receipt_id}', { params: { path: { receipt_id: receiptId } } }))
}

export async function getReceiptStatus(receiptId: string) {
  return unwrap(
    await api.GET('/api/v1/receipts/{receipt_id}/status', { params: { path: { receipt_id: receiptId } } }),
  )
}

export async function updateReceipt(
  receiptId: string,
  patch: { merchant?: string; total_amount?: number; receipt_date?: string; category_id?: string },
) {
  return unwrap(
    await api.PATCH('/api/v1/receipts/{receipt_id}', { params: { path: { receipt_id: receiptId } }, body: patch }),
  )
}

export async function deleteReceipt(receiptId: string) {
  await api.DELETE('/api/v1/receipts/{receipt_id}', { params: { path: { receipt_id: receiptId } } })
}

export async function retryOcr(receiptId: string) {
  return unwrap(
    await api.POST('/api/v1/receipts/{receipt_id}/retry-ocr', { params: { path: { receipt_id: receiptId } } }),
  )
}
