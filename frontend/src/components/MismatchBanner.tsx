export function MismatchBanner() {
  return (
    <div className="rounded-md border border-owed/30 bg-owed-tint px-4 py-3 text-sm text-owed">
      The line items don't add up to the receipt total — double-check the amounts below.
    </div>
  )
}
