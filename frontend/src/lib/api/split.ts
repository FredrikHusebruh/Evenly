import { api, unwrap } from './client'

export async function getReceiptSplit(receiptId: string) {
  return unwrap(await api.GET('/api/v1/receipts/{receipt_id}/split', { params: { path: { receipt_id: receiptId } } }))
}

export async function getSettleUp(groupId: string) {
  return unwrap(await api.GET('/api/v1/groups/{group_id}/settle-up', { params: { path: { group_id: groupId } } }))
}
