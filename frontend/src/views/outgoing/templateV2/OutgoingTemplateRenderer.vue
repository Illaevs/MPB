<script>
import { h, defineComponent, computed, ref, onMounted, onBeforeUnmount, watch } from 'vue'
import PlaceholderChip from './PlaceholderChip.vue'
import EditableRegion from './EditableRegion.vue'

/**
 * Render a template_v2 document inline.
 *
 * Walks `layoutHtml` as a DOM tree and produces a Vue VNode tree where:
 *  - elements with `data-placeholder` become <PlaceholderChip> bound to a field
 *  - elements with `data-editable` become <EditableRegion> (one per template)
 *  - everything else is rendered as the original element with recursively
 *    processed children
 *
 * Page break visualisation:
 *  - The document grows freely with content.
 *  - A ResizeObserver tracks article height.
 *  - We render N-1 absolute-positioned dividers (where N = ceil(height / pageHeight))
 *    to mark visual page boundaries. They're decorative — real pagination
 *    happens server-side when libreoffice produces the PDF.
 */

// A4 portrait at 96 dpi ≈ 1123 px. We round to a nicer 1100 for the visual
// — it doesn't have to match PDF pagination exactly; it just gives the user
// a sense of where pages will break.
const PAGE_HEIGHT = 1100

export default defineComponent({
  name: 'OutgoingTemplateRenderer',
  components: { PlaceholderChip, EditableRegion },
  props: {
    layoutHtml: { type: String, required: true },
    fieldValues: { type: Object, default: () => ({}) },
    placeholderFields: { type: Array, default: () => [] },
    editableContent: { type: Object, default: () => ({}) },
    activeFieldKey: { type: String, default: '' },
    resolvedContext: { type: Object, default: () => ({}) },
  },
  emits: ['select-field', 'update:editableContent', 'editable-focus', 'editable-blur'],
  setup(props, { emit }) {
    const docRef = ref(null)
    const docHeight = ref(PAGE_HEIGHT)
    let resizeObserver = null

    // ---- Parse layoutHtml once per change. -----------------------------
    const parsed = computed(() => {
      const parser = new DOMParser()
      const doc = parser.parseFromString(`<div>${props.layoutHtml || ''}</div>`, 'text/html')
      return doc.body.firstElementChild
    })

    const fieldLabel = (key) => {
      const def = props.placeholderFields.find((f) => f.key === key)
      return def ? def.label : key
    }

    // ---- Page break computation ---------------------------------------
    const pageCount = computed(() => Math.max(1, Math.ceil(docHeight.value / PAGE_HEIGHT)))
    const pageBreaks = computed(() => {
      const breaks = []
      for (let i = 1; i < pageCount.value; i++) {
        breaks.push({ index: i, top: i * PAGE_HEIGHT })
      }
      return breaks
    })

    onMounted(() => {
      if (!docRef.value || typeof ResizeObserver === 'undefined') return
      resizeObserver = new ResizeObserver((entries) => {
        for (const entry of entries) {
          const h = entry.borderBoxSize?.[0]?.blockSize ?? entry.contentRect.height
          docHeight.value = h
        }
      })
      resizeObserver.observe(docRef.value)
    })
    onBeforeUnmount(() => {
      if (resizeObserver) resizeObserver.disconnect()
    })

    // ---- Data tables (stages / payments) from resolvedContext ---------
    const renderDataTable = (kind) => {
      const ctx = props.resolvedContext || {}
      const isStages = kind === 'stages'
      const rows = isStages
        ? (Array.isArray(ctx.stages) ? ctx.stages : [])
        : (Array.isArray(ctx.linked_payment_items) ? ctx.linked_payment_items : [])

      const headCells = isStages
        ? ['№', 'Наименование', 'Сумма']
        : ['№', 'Назначение', 'Сумма']

      if (!rows.length) {
        return h('div', { class: 'doc-table doc-table--empty' },
          isStages ? 'Этапы не выбраны' : 'Платежи не выбраны')
      }

      const thead = h('thead', {}, h('tr', {},
        headCells.map((c) => h('th', {}, c))))
      const tbody = h('tbody', {}, rows.map((r, i) => h('tr', {}, [
        h('td', {}, String(i + 1)),
        h('td', {}, isStages ? (r.name || '—') : (r.note || 'Платёж')),
        h('td', { class: 'doc-table__amount' }, r.amount != null ? String(r.amount) : '—'),
      ])))
      return h('table', { class: 'doc-table', 'data-locked': 'true' }, [thead, tbody])
    }

    // ---- Tree walker --------------------------------------------------
    const renderNode = (node) => {
      if (node.nodeType === 3) return node.textContent
      if (node.nodeType !== 1) return null

      const el = node
      const tag = el.tagName.toLowerCase()

      const fieldKey = el.getAttribute('data-placeholder')
      if (fieldKey) {
        return h(PlaceholderChip, {
          fieldKey,
          value: props.fieldValues[fieldKey] ?? null,
          label: fieldLabel(fieldKey),
          active: props.activeFieldKey === fieldKey,
          onSelect: (k) => emit('select-field', k),
        })
      }

      // Data table marker → render rows from resolvedContext
      const tableKey = el.getAttribute('data-table')
      if (tableKey) {
        return renderDataTable(tableKey)
      }

      const regionKey = el.getAttribute('data-editable')
      if (regionKey) {
        return h(EditableRegion, {
          regionKey,
          modelValue: props.editableContent[regionKey] ?? el.innerHTML,
          'onUpdate:modelValue': (html) => {
            const next = { ...props.editableContent, [regionKey]: html }
            emit('update:editableContent', next)
          },
          onFocus: (info) => emit('editable-focus', info),
          onBlur: (info) => emit('editable-blur', info),
        })
      }

      const props2 = {}
      for (const attr of el.attributes) {
        const name = attr.name
        if (name.toLowerCase().startsWith('on')) continue
        props2[name] = attr.value
      }
      if (el.hasAttribute('data-locked')) {
        props2.contenteditable = 'false'
      }
      const children = []
      for (const child of el.childNodes) {
        const rendered = renderNode(child)
        if (rendered !== null && rendered !== undefined) children.push(rendered)
      }
      return h(tag, props2, children)
    }

    // ---- Render -------------------------------------------------------
    return () => {
      const root = parsed.value
      if (!root) {
        return h('div', { class: 'doc-stage' }, [
          h('article', { class: 'outgoing-doc outgoing-doc--empty' }, 'Шаблон не выбран'),
        ])
      }

      const articleChildren = []
      for (const child of root.childNodes) {
        const r = renderNode(child)
        if (r !== null && r !== undefined) articleChildren.push(r)
      }

      const breaks = pageBreaks.value.map(({ index, top }) =>
        h('div', {
          key: `pb-${index}`,
          class: 'doc-stage__page-break',
          style: { top: `${top}px` },
          'aria-hidden': 'true',
        }, [
          h('span', { class: 'doc-stage__page-break-label' }, `Стр. ${index + 1}`),
        ])
      )

      return h('div', { class: 'doc-stage' }, [
        h('article', {
          class: 'outgoing-doc',
          ref: docRef,
          style: { minHeight: `${PAGE_HEIGHT}px` },
        }, articleChildren),
        ...breaks,
      ])
    }
  }
})
</script>

<style scoped>
.doc-stage {
  position: relative;
  width: min(820px, 100%);
  margin: 0 auto;
}

/* A4 page-like surface */
.outgoing-doc {
  width: 100%;
  padding: 56px 80px;
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  color: var(--color-text);
  font-size: 14px;
  line-height: 1.55;
}

.outgoing-doc--empty {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-muted);
}

/* Page-break dividers — absolute-positioned over the document.
   Decorative: actual pagination happens server-side when libreoffice
   produces the PDF. */
.doc-stage__page-break {
  position: absolute;
  left: 0;
  right: 0;
  height: 1px;
  background: var(--color-border);
  pointer-events: none;
  display: flex;
  align-items: center;
  justify-content: center;
}
.doc-stage__page-break-label {
  display: inline-block;
  padding: 2px 10px;
  background: var(--color-surface-2);
  border: 1px solid var(--color-border-subtle);
  color: var(--color-text-muted);
  font-size: var(--text-xs);
  font-weight: var(--fw-semibold);
  letter-spacing: 0.04em;
  text-transform: uppercase;
  border-radius: var(--radius-pill);
  /* Centred over the line */
  transform: translateY(-50%);
  white-space: nowrap;
}

/* Document body — basic typography for locked/editable sections.
   These cascade into the rendered HTML (rules are unscoped via :deep). */
.outgoing-doc :deep(h1) {
  margin: 0 0 32px;
  text-align: center;
  font-size: 1.15rem;
  font-weight: var(--fw-bold);
  text-transform: uppercase;
  letter-spacing: 0.02em;
  color: var(--color-text);
}
.outgoing-doc :deep(p) {
  margin: 0 0 12px;
}
.outgoing-doc :deep(.doc-letter__recipient) {
  margin-bottom: 24px;
  text-align: right;
}
.outgoing-doc :deep(.doc-letter__recipient p) {
  margin: 0 0 4px;
}
.outgoing-doc :deep(.doc-letter__meta) {
  margin-bottom: 24px;
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}
.outgoing-doc :deep(.doc-letter__body) {
  margin: 24px 0;
}
.outgoing-doc :deep(.doc-letter__signature) {
  margin-top: 48px;
}
.outgoing-doc :deep([data-locked="true"]) {
  user-select: text;
  caret-color: transparent;
}

/* Data tables (stages / payments) injected from resolved context */
.outgoing-doc :deep(.doc-table) {
  width: 100%;
  border-collapse: collapse;
  margin: 16px 0;
  font-size: 13px;
}
.outgoing-doc :deep(.doc-table th),
.outgoing-doc :deep(.doc-table td) {
  border: 1px solid var(--color-border);
  padding: 6px 10px;
  text-align: left;
  vertical-align: top;
}
.outgoing-doc :deep(.doc-table th) {
  background: var(--color-surface-2);
  font-weight: var(--fw-semibold);
  color: var(--color-text-muted);
}
.outgoing-doc :deep(.doc-table__amount) {
  text-align: right;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}
.outgoing-doc :deep(.doc-table--empty) {
  margin: 16px 0;
  padding: 14px;
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-sm);
  text-align: center;
  color: var(--color-text-subtle);
  font-size: var(--text-sm);
}
</style>
