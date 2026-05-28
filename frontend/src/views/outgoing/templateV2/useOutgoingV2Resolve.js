import { ref, watch } from 'vue'
import { resolveEditor } from '../../../services/api/outgoing'

/**
 * Drives placeholder auto-fill for template_v2.
 *
 * Collects the anchor inputs (recipient/our company, deal, contract, bank
 * account index, linked stages/payments, recipient overrides), debounce-calls
 * the existing `/editor/resolve` endpoint, then merges the flat
 * `resolved_fields` map (dotted FIELD_REGISTRY keys) into `fieldValues` so the
 * document chips fill in. `resolvedContext` exposes the nested payload used by
 * table sections (stages / payment items).
 *
 * Anchors are persisted as top-level OutgoingDocument columns by the caller,
 * which is what keeps the classic and v2 editors in sync.
 */
export function useOutgoingV2Resolve({
  documentKind,
  documentId,
  anchors,          // reactive object of anchor refs (see OutgoingRegistryV2)
  fieldValues,      // ref<object> — merged target for chips
  editableContent,  // ref<object> — passed through for backend context
}) {
  const resolving = ref(false)
  const resolveError = ref('')
  const resolvedContext = ref({})
  let timer = null
  let seq = 0

  const buildPayload = () => ({
    document_id: documentId.value || undefined,
    document_kind: documentKind.value,
    editor_mode: 'classic',
    editor_schema_version: 1,
    recipient_company_id: anchors.recipientCompanyId.value || undefined,
    our_company_key: anchors.ourCompanyKey.value || undefined,
    deal_id: anchors.dealId.value || undefined,
    contract_id: anchors.contractId.value || undefined,
    bank_account_index: anchors.bankAccountIndex.value ?? undefined,
    linked_stage_ids: anchors.linkedStageIds.value?.length ? anchors.linkedStageIds.value : undefined,
    linked_payment_items: anchors.linkedPaymentItems.value?.length ? anchors.linkedPaymentItems.value : undefined,
    recipient_eio: anchors.recipientEio.value || undefined,
    recipient_to_name: anchors.recipientToName.value || undefined,
    recipient_genitive_name: anchors.recipientGenitiveName.value || undefined,
    recipient_short_name: anchors.recipientShortName.value || undefined,
    recipient_appeal: anchors.recipientAppeal.value || undefined,
    recipient_salutation: anchors.recipientSalutation.value || undefined,
    status: 'draft',
  })

  const runResolve = async () => {
    // Nothing to resolve without at least a recipient.
    if (!anchors.recipientCompanyId.value) return
    const mySeq = ++seq
    resolving.value = true
    resolveError.value = ''
    try {
      const resp = await resolveEditor(buildPayload())
      if (mySeq !== seq) return // a newer request superseded this one
      const data = resp?.data ?? resp
      const resolved = data?.resolved_fields || {}
      resolvedContext.value = data?.resolved_context || {}
      // Merge resolved values WITHOUT clobbering keys the user typed manually
      // into anchor fields (those are re-derived anyway). We simply overlay
      // every resolved key — chips reflect the latest server truth.
      const next = { ...fieldValues.value }
      for (const [k, v] of Object.entries(resolved)) {
        if (v === null || v === undefined) continue
        // skip the repeater markers — tables read resolvedContext directly
        if (k === 'stages' || k === 'linked_payment_items') continue
        next[k] = typeof v === 'object' ? v : String(v)
      }
      fieldValues.value = next
    } catch (e) {
      resolveError.value = e?.response?.data?.detail || e.message || 'Не удалось подгрузить поля'
    } finally {
      if (mySeq === seq) resolving.value = false
    }
  }

  const scheduleResolve = (delay = 250) => {
    if (timer) clearTimeout(timer)
    timer = setTimeout(runResolve, delay)
  }

  // Re-resolve whenever any anchor changes.
  const anchorRefs = [
    () => documentKind.value,
    () => anchors.recipientCompanyId.value,
    () => anchors.ourCompanyKey.value,
    () => anchors.dealId.value,
    () => anchors.contractId.value,
    () => anchors.bankAccountIndex.value,
    () => JSON.stringify(anchors.linkedStageIds.value || []),
    () => JSON.stringify(anchors.linkedPaymentItems.value || []),
    () => anchors.recipientEio.value,
    () => anchors.recipientToName.value,
    () => anchors.recipientGenitiveName.value,
  ]
  watch(anchorRefs, () => scheduleResolve(), { flush: 'post' })

  return { resolving, resolveError, resolvedContext, runResolve, scheduleResolve }
}
