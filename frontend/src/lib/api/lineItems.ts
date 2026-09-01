import { api, unwrap } from './client'

export type LineItemStatus = 'shared' | 'personal' | 'excluded'

export async function listLineItems(receiptId: string) {
  return unwrap(
    await api.GET('/api/v1/receipts/{receipt_id}/line-items', { params: { path: { receipt_id: receiptId } } }),
  )
}

export async function createLineItem(
  receiptId: string,
  item: { description: string; quantity: number; unit_price: number; total_price: number },
) {
  return unwrap(
    await api.POST('/api/v1/receipts/{receipt_id}/line-items', {
      params: { path: { receipt_id: receiptId } },
      body: item,
    }),
  )
}

export type LineItemPatch = Partial<{
  description: string
  quantity: number
  unit_price: number
  total_price: number
  status: LineItemStatus
  assigned_to: string | null
}>

export async function updateLineItem(lineItemId: string, patch: LineItemPatch) {
  return unwrap(
    await api.PATCH('/api/v1/line-items/{line_item_id}', {
      params: { path: { line_item_id: lineItemId } },
      body: patch,
    }),
  )
}

export async function deleteLineItem(lineItemId: string) {
  await api.DELETE('/api/v1/line-items/{line_item_id}', { params: { path: { line_item_id: lineItemId } } })
}
