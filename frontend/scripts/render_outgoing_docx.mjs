#!/usr/bin/env node
import fs from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import PizZip from 'pizzip'
import Docxtemplater from 'docxtemplater'
import { JSDOM } from 'jsdom'
import createDOMPurify from 'dompurify'

const DOCX_BODY_PLACEHOLDER = '__DOCX_BODY_PLACEHOLDER__'
const DEFAULT_RECIPIENT_EIO = 'Генеральному директору'
const DEFAULT_BODY_FIRST_LINE_TWIPS = 709

const { window } = new JSDOM('<!DOCTYPE html><html><body></body></html>')
const { document, Node, DOMParser } = window
const DOMPurify = createDOMPurify(window)

const bodySanitizeConfig = {
  ALLOWED_TAGS: ['p', 'br', 'b', 'i', 'u', 'strong', 'em', 'ul', 'ol', 'li', 'div', 'span', 'table', 'thead', 'tbody', 'tr', 'th', 'td'],
  ALLOWED_ATTR: ['style', 'colspan', 'rowspan']
}

const companyTemplates = {
  normbud: 'outgoing_normbud.docx',
  bayer: 'outgoing_bayer.docx',
  morozov: 'outgoing_morozov.docx'
}
const scriptDir = path.dirname(fileURLToPath(import.meta.url))

const xmlEscape = (value = '') => String(value)
  .replace(/&/g, '&amp;')
  .replace(/</g, '&lt;')
  .replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;')
  .replace(/'/g, '&apos;')

const htmlEscape = (value = '') => String(value)
  .replace(/&/g, '&amp;')
  .replace(/</g, '&lt;')
  .replace(/>/g, '&gt;')

const stripHtml = (html) => {
  if (!html) return ''
  const tmp = document.createElement('div')
  tmp.innerHTML = html
    .replace(/<\/p>/gi, '</p>[[NL]]')
    .replace(/<\/div>/gi, '</div>[[NL]]')
    .replace(/<br\s*\/?>/gi, '<br>[[NL]]')
    .replace(/<\/li>/gi, '</li>[[NL]]')
  const text = tmp.textContent || ''
  return text.replace(/\[\[NL\]\]/g, '\n')
}

const flattenObject = (value, prefix = '', target = {}) => {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return target
  Object.entries(value).forEach(([key, entry]) => {
    const nextKey = prefix ? `${prefix}.${key}` : key
    if (entry && typeof entry === 'object' && !Array.isArray(entry)) {
      flattenObject(entry, nextKey, target)
      return
    }
    target[nextKey] = entry ?? ''
  })
  return target
}

const formatDateLong = (value) => {
  if (!value) return ''
  const date = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  const months = [
    'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
    'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'
  ]
  return `${String(date.getDate()).padStart(2, '0')} ${months[date.getMonth()]} ${date.getFullYear()}`
}

const resolveTemplatePath = (docData) => {
  if (docData?.template_file_path) {
    return path.resolve(docData.template_file_path)
  }
  const key = docData?.our_company_key || 'normbud'
  const templateName = companyTemplates[key] || companyTemplates.normbud
  return path.resolve(scriptDir, '..', 'public', 'templates', templateName)
}

const buildRunPropsXml = (baseRunPropsInner = '', formats = {}) => {
  const extras = []
  if (formats.bold) extras.push('<w:b/>')
  if (formats.italic) extras.push('<w:i/>')
  if (formats.underline) extras.push('<w:u w:val="single"/>')
  return `<w:rPr>${extras.join('')}${baseRunPropsInner}</w:rPr>`
}

const parseCssLengthToTwips = (value) => {
  if (value === null || value === undefined) return null
  const normalized = String(value).trim().toLowerCase().replace(',', '.')
  const match = normalized.match(/^(-?\d+(?:\.\d+)?)(cm|mm|pt|px)?$/)
  if (!match) return null
  const amount = Number(match[1])
  if (!Number.isFinite(amount)) return null
  const unit = match[2] || 'px'
  if (unit === 'cm') return Math.round(amount * 567)
  if (unit === 'mm') return Math.round(amount * 56.7)
  if (unit === 'pt') return Math.round(amount * 20)
  return Math.round(amount * 15)
}

const mergeParagraphPropsXml = (baseParagraphPropsXml = '', paragraphOptions = {}) => {
  const hasOverrides = (
    paragraphOptions.firstLineTwips !== undefined ||
    paragraphOptions.leftTwips !== undefined ||
    paragraphOptions.hangingTwips !== undefined ||
    paragraphOptions.justification
  )
  if (!hasOverrides) return baseParagraphPropsXml

  let xml = baseParagraphPropsXml || '<w:pPr></w:pPr>'
  if (paragraphOptions.firstLineTwips !== undefined || paragraphOptions.leftTwips !== undefined || paragraphOptions.hangingTwips !== undefined) {
    xml = xml.replace(/<w:ind\b[^>]*\/>/g, '')
    const attrs = []
    if (paragraphOptions.leftTwips !== undefined && paragraphOptions.leftTwips !== null) attrs.push(`w:left="${paragraphOptions.leftTwips}"`)
    if (paragraphOptions.firstLineTwips !== undefined && paragraphOptions.firstLineTwips !== null) attrs.push(`w:firstLine="${paragraphOptions.firstLineTwips}"`)
    if (paragraphOptions.hangingTwips !== undefined && paragraphOptions.hangingTwips !== null) attrs.push(`w:hanging="${paragraphOptions.hangingTwips}"`)
    if (attrs.length) {
      xml = xml.replace('</w:pPr>', `<w:ind ${attrs.join(' ')}/></w:pPr>`)
    }
  }
  if (paragraphOptions.justification) {
    xml = xml.replace(/<w:jc\b[^>]*\/>/g, '')
    xml = xml.replace('</w:pPr>', `<w:jc w:val="${paragraphOptions.justification}"/></w:pPr>`)
  }
  return xml
}

const paragraphOptionsFromNode = (node, fallback = {}) => {
  const options = { ...fallback }
  if (!node || node.nodeType !== Node.ELEMENT_NODE) return options
  const textIndent = parseCssLengthToTwips(node.style?.textIndent)
  if (textIndent !== null) options.firstLineTwips = textIndent
  const textAlign = (node.style?.textAlign || '').trim().toLowerCase()
  if (textAlign === 'justify') options.justification = 'both'
  else if (textAlign === 'center') options.justification = 'center'
  else if (textAlign === 'right' || textAlign === 'end') options.justification = 'right'
  else if (textAlign === 'left' || textAlign === 'start') options.justification = 'left'
  return options
}

const trimTrailingParagraphNodes = (nodes) => {
  const clones = Array.from(nodes || []).map((node) => node.cloneNode(true))

  const trimNodeList = (list) => {
    for (let index = list.length - 1; index >= 0; index -= 1) {
      const node = list[index]
      if (!node) continue

      if (node.nodeType === Node.TEXT_NODE) {
        const nextText = (node.textContent || '').replace(/[\s\u00A0]+$/g, '')
        node.textContent = nextText
        if (!nextText.length) {
          node.remove()
          continue
        }
        break
      }

      if (node.nodeType !== Node.ELEMENT_NODE) {
        node.remove()
        continue
      }

      const tag = node.tagName.toLowerCase()
      if (tag === 'br') {
        node.remove()
        continue
      }

      trimNodeList(Array.from(node.childNodes || []))
      const remainingText = (node.textContent || '').replace(/[\s\u00A0]+/g, '')
      const hasBreak = typeof node.querySelector === 'function' && !!node.querySelector('br')
      if (!remainingText.length && !hasBreak) {
        node.remove()
        continue
      }
      break
    }
  }

  trimNodeList(clones)
  return clones
}

const buildTextRunsXml = (text = '', baseRunPropsInner = '', formats = {}) => {
  const normalized = String(text).replace(/\r\n/g, '\n').replace(/\r/g, '\n')
  const segments = normalized.split('\n')
  return segments.map((segment, index) => {
    const parts = segment.split('\t')
    const runParts = []
    if (parts.length === 1 && parts[0] === '') {
      runParts.push(`<w:r>${buildRunPropsXml(baseRunPropsInner, formats)}<w:t xml:space="preserve"></w:t></w:r>`)
    } else {
      parts.forEach((part, partIndex) => {
        if (part.length > 0) {
          const preserve = /^\s|\s$| {2,}/.test(part)
          runParts.push(`<w:r>${buildRunPropsXml(baseRunPropsInner, formats)}<w:t${preserve ? ' xml:space="preserve"' : ''}>${xmlEscape(part)}</w:t></w:r>`)
        }
        if (partIndex < parts.length - 1) {
          runParts.push(`<w:r>${buildRunPropsXml(baseRunPropsInner, formats)}<w:tab/></w:r>`)
        }
      })
    }
    if (index < segments.length - 1) {
      runParts.push(`<w:r>${buildRunPropsXml(baseRunPropsInner, formats)}<w:br/></w:r>`)
    }
    return runParts.join('')
  }).join('')
}

const buildRunsFromDomNode = (node, baseRunPropsInner = '', formats = {}) => {
  if (!node) return ''
  if (node.nodeType === Node.TEXT_NODE) {
    const text = node.textContent || ''
    return text ? buildTextRunsXml(text, baseRunPropsInner, formats) : ''
  }
  if (node.nodeType !== Node.ELEMENT_NODE) return ''

  const tag = node.tagName.toLowerCase()
  if (tag === 'br') {
    return `<w:r>${buildRunPropsXml(baseRunPropsInner, formats)}<w:br/></w:r>`
  }

  const nextFormats = { ...formats }
  if (tag === 'b' || tag === 'strong' || Number(node.style?.fontWeight || 400) >= 600) nextFormats.bold = true
  if (tag === 'i' || tag === 'em' || node.style?.fontStyle === 'italic') nextFormats.italic = true
  if (tag === 'u' || (node.style?.textDecoration || '').includes('underline')) nextFormats.underline = true

  return Array.from(node.childNodes || []).map((child) => buildRunsFromDomNode(child, baseRunPropsInner, nextFormats)).join('')
}

const buildParagraphXml = (runsXml, baseParagraphPropsXml = '', baseRunPropsInner = '', paragraphOptions = {}) => {
  const safeRuns = runsXml && runsXml.trim()
    ? runsXml
    : `<w:r>${buildRunPropsXml(baseRunPropsInner)}<w:t xml:space="preserve"></w:t></w:r>`
  return `<w:p>${mergeParagraphPropsXml(baseParagraphPropsXml, paragraphOptions)}${safeRuns}</w:p>`
}

const buildParagraphFromNodes = (nodes, baseParagraphPropsXml = '', baseRunPropsInner = '', prefix = '', paragraphOptions = {}) => {
  const sanitizedNodes = trimTrailingParagraphNodes(nodes)
  const bodyRuns = sanitizedNodes.map((node) => buildRunsFromDomNode(node, baseRunPropsInner)).join('')
  const prefixRuns = prefix ? buildTextRunsXml(prefix, baseRunPropsInner) : ''
  return buildParagraphXml(`${prefixRuns}${bodyRuns}`.trim(), baseParagraphPropsXml, baseRunPropsInner, paragraphOptions)
}

const buildCellParagraphsXml = (cell, baseParagraphPropsXml = '', baseRunPropsInner = '') => {
  const tableParagraphOptions = { firstLineTwips: 0 }
  const directBlocks = Array.from(cell.childNodes || []).filter((node) => (
    node.nodeType === Node.ELEMENT_NODE && ['p', 'div', 'ul', 'ol', 'table'].includes(node.tagName.toLowerCase())
  ))
  if (!directBlocks.length) {
    return buildParagraphFromNodes(cell.childNodes, baseParagraphPropsXml, baseRunPropsInner, '', tableParagraphOptions)
  }
  const fragments = []
  directBlocks.forEach((node) => {
    const tag = node.tagName.toLowerCase()
    if (tag === 'p' || tag === 'div') {
      fragments.push(buildParagraphFromNodes(node.childNodes, baseParagraphPropsXml, baseRunPropsInner, '', tableParagraphOptions))
      return
    }
    if (tag === 'ul' || tag === 'ol') {
      Array.from(node.children || []).forEach((child, index) => {
        const prefix = tag === 'ol' ? `${index + 1}. ` : '• '
        fragments.push(buildParagraphFromNodes(child.childNodes, baseParagraphPropsXml, baseRunPropsInner, prefix, tableParagraphOptions))
      })
    }
  })
  return fragments.join('') || buildParagraphXml('', baseParagraphPropsXml, baseRunPropsInner, tableParagraphOptions)
}

const buildTableXml = (table, baseParagraphPropsXml = '', baseRunPropsInner = '') => {
  const rows = Array.from(table.rows || [])
  if (!rows.length) return ''
  const columnCount = Math.max(
    ...rows.map((row) => Array.from(row.cells || []).reduce((sum, cell) => sum + Math.max(1, Number(cell.colSpan || 1)), 0)),
    1
  )
  const usableWidth = 9000
  const cellWidth = Math.floor(usableWidth / columnCount)
  const gridColsXml = Array.from({ length: columnCount }, () => `<w:gridCol w:w="${cellWidth}"/>`).join('')
  const rowsXml = rows.map((row) => {
    const rowCellsXml = Array.from(row.cells || []).map((cell) => {
      const tag = cell.tagName.toLowerCase()
      const colspan = Math.max(1, Number(cell.colSpan || 1))
      const width = cellWidth * colspan
      const cellBlocks = buildCellParagraphsXml(cell, baseParagraphPropsXml, baseRunPropsInner)
      const shd = tag === 'th' ? '<w:shd w:val="clear" w:color="auto" w:fill="F3F4F6"/>' : ''
      const gridSpan = colspan > 1 ? `<w:gridSpan w:val="${colspan}"/>` : ''
      return `<w:tc><w:tcPr><w:tcW w:w="${width}" w:type="dxa"/>${gridSpan}<w:vAlign w:val="top"/>${shd}</w:tcPr>${cellBlocks}</w:tc>`
    }).join('')
    return `<w:tr>${rowCellsXml}</w:tr>`
  }).join('')
  return `<w:tbl><w:tblPr><w:tblW w:w="0" w:type="auto"/><w:tblLayout w:type="fixed"/><w:tblBorders><w:top w:val="single" w:sz="8" w:space="0" w:color="BFC7D5"/><w:left w:val="single" w:sz="8" w:space="0" w:color="BFC7D5"/><w:bottom w:val="single" w:sz="8" w:space="0" w:color="BFC7D5"/><w:right w:val="single" w:sz="8" w:space="0" w:color="BFC7D5"/><w:insideH w:val="single" w:sz="8" w:space="0" w:color="BFC7D5"/><w:insideV w:val="single" w:sz="8" w:space="0" w:color="BFC7D5"/></w:tblBorders></w:tblPr><w:tblGrid>${gridColsXml}</w:tblGrid>${rowsXml}</w:tbl>`
}

const buildWordBodyXml = (html, baseParagraphPropsXml = '', baseRunPropsInner = '') => {
  const wrapper = document.createElement('div')
  wrapper.innerHTML = DOMPurify.sanitize(html || '', bodySanitizeConfig)
  const blocks = []
  const blockTags = ['p', 'div', 'ul', 'ol', 'table']
  const defaultParagraphOptions = { firstLineTwips: DEFAULT_BODY_FIRST_LINE_TWIPS, justification: 'both' }

  const pushParagraphFromNode = (node, prefix = '', paragraphOptions = defaultParagraphOptions) => {
    blocks.push(buildParagraphFromNodes(node.childNodes || [], baseParagraphPropsXml, baseRunPropsInner, prefix, paragraphOptions))
  }

  const appendBlockNode = (node) => {
    if (!node) return
    if (node.nodeType === Node.TEXT_NODE) {
      if ((node.textContent || '').trim()) {
        blocks.push(buildParagraphXml(buildTextRunsXml(node.textContent || '', baseRunPropsInner), baseParagraphPropsXml, baseRunPropsInner, defaultParagraphOptions))
      }
      return
    }
    if (node.nodeType !== Node.ELEMENT_NODE) return

    const tag = node.tagName.toLowerCase()
    if (tag === 'table') {
      blocks.push(buildTableXml(node, baseParagraphPropsXml, baseRunPropsInner))
      return
    }
    if (tag === 'ul' || tag === 'ol') {
      Array.from(node.children || []).forEach((child, index) => {
        const prefix = tag === 'ol' ? `${index + 1}. ` : '• '
        pushParagraphFromNode(child, prefix, { firstLineTwips: 0 })
      })
      return
    }
    if (tag === 'p') {
      pushParagraphFromNode(node, '', paragraphOptionsFromNode(node, defaultParagraphOptions))
      return
    }
    if (tag === 'div') {
      const hasBlockChildren = Array.from(node.childNodes || []).some((child) => (
        child.nodeType === Node.ELEMENT_NODE && blockTags.includes(child.tagName.toLowerCase())
      ))
      if (!hasBlockChildren) {
        pushParagraphFromNode(node, '', paragraphOptionsFromNode(node, defaultParagraphOptions))
        return
      }
      Array.from(node.childNodes || []).forEach((child) => {
        if (child.nodeType === Node.TEXT_NODE && (child.textContent || '').trim()) {
          blocks.push(buildParagraphXml(buildTextRunsXml(child.textContent || '', baseRunPropsInner), baseParagraphPropsXml, baseRunPropsInner, defaultParagraphOptions))
          return
        }
        appendBlockNode(child)
      })
      return
    }
    blocks.push(buildParagraphFromNodes([node], baseParagraphPropsXml, baseRunPropsInner, '', defaultParagraphOptions))
  }

  Array.from(wrapper.childNodes || []).forEach((node) => appendBlockNode(node))
  if (!blocks.length) {
    blocks.push(buildParagraphXml('', baseParagraphPropsXml, baseRunPropsInner, defaultParagraphOptions))
  }
  return blocks.join('')
}

const injectRichBodyIntoDocxZip = (zip, html) => {
  const xmlPath = 'word/document.xml'
  const xml = zip.file(xmlPath)?.asText()
  if (!xml) return
  const placeholderIndex = xml.indexOf(DOCX_BODY_PLACEHOLDER)
  if (placeholderIndex === -1) return
  const paragraphStartWithAttrs = xml.lastIndexOf('<w:p ', placeholderIndex)
  const paragraphStartBare = xml.lastIndexOf('<w:p>', placeholderIndex)
  const paragraphStart = Math.max(paragraphStartWithAttrs, paragraphStartBare)
  const paragraphEndMarker = xml.indexOf('</w:p>', placeholderIndex)
  if (paragraphStart === -1 || paragraphEndMarker === -1) return
  const paragraphEnd = paragraphEndMarker + '</w:p>'.length
  const placeholderParagraphXml = xml.slice(paragraphStart, paragraphEnd)
  const pPrMatch = placeholderParagraphXml.match(/<w:pPr>[\s\S]*?<\/w:pPr>/)
  const rPrMatch = placeholderParagraphXml.match(/<w:rPr>([\s\S]*?)<\/w:rPr>/)
  const richBodyXml = buildWordBodyXml(html, pPrMatch ? pPrMatch[0] : '', rPrMatch ? rPrMatch[1] : '')
  zip.file(xmlPath, `${xml.slice(0, paragraphStart)}${richBodyXml}${xml.slice(paragraphEnd)}`)
}

const validateDocxDocumentXml = (zip) => {
  const xml = zip.file('word/document.xml')?.asText()
  if (!xml) return false
  const parsed = new DOMParser().parseFromString(xml, 'application/xml')
  return !parsed.querySelector('parsererror')
}

const normalizeFloatingPictureLayers = (zip) => {
  const xmlPath = 'word/document.xml'
  const xml = zip.file(xmlPath)?.asText()
  if (!xml) return
  const nextXml = xml.replace(/<wp:anchor\b[\s\S]*?<\/wp:anchor>/g, (anchorXml) => {
    if (!anchorXml.includes('drawingml/2006/picture')) return anchorXml
    return anchorXml
      .replace(/\sbehindDoc="1"/, ' behindDoc="0"')
      .replace(/\srelativeHeight="\d+"/, ' relativeHeight="251659264"')
  })
  if (nextXml !== xml) zip.file(xmlPath, nextXml)
}

const normalizeInlineHtmlForDocx = (nodes, formats = {}) => {
  return Array.from(nodes || []).map((node) => {
    if (!node) return ''
    if (node.nodeType === Node.TEXT_NODE) {
      return htmlEscape(node.textContent || '')
    }
    if (node.nodeType !== Node.ELEMENT_NODE) return ''
    const tag = node.tagName.toLowerCase()
    if (tag === 'br') return '<br>'

    const nextFormats = { ...formats }
    if (tag === 'b' || tag === 'strong' || Number(node.style?.fontWeight || 400) >= 600) nextFormats.bold = true
    if (tag === 'i' || tag === 'em' || node.style?.fontStyle === 'italic') nextFormats.italic = true
    if (tag === 'u' || (node.style?.textDecoration || '').includes('underline')) nextFormats.underline = true

    let inner = normalizeInlineHtmlForDocx(node.childNodes || [], nextFormats)
    if (!inner) return ''
    if (nextFormats.underline && !formats.underline) inner = `<u>${inner}</u>`
    if (nextFormats.italic && !formats.italic) inner = `<em>${inner}</em>`
    if (nextFormats.bold && !formats.bold) inner = `<strong>${inner}</strong>`
    return inner
  }).join('')
}

const normalizeTableHtmlForDocx = (table) => {
  const rows = Array.from(table.rows || [])
  if (!rows.length) return ''
  const rowsHtml = rows.map((row) => {
    const cellsHtml = Array.from(row.cells || []).map((cell) => {
      const tag = cell.tagName.toLowerCase() === 'th' ? 'th' : 'td'
      const attrs = []
      if (cell.colSpan && Number(cell.colSpan) > 1) attrs.push(`colspan="${Number(cell.colSpan)}"`)
      if (cell.rowSpan && Number(cell.rowSpan) > 1) attrs.push(`rowspan="${Number(cell.rowSpan)}"`)
      const content = normalizeInlineHtmlForDocx(cell.childNodes || []) || '&nbsp;'
      return `<${tag}${attrs.length ? ` ${attrs.join(' ')}` : ''}>${content}</${tag}>`
    }).join('')
    return `<tr>${cellsHtml}</tr>`
  }).join('')
  return `<table>${rowsHtml}</table>`
}

const normalizeHtmlForDocx = (html) => {
  const wrapper = document.createElement('div')
  wrapper.innerHTML = DOMPurify.sanitize(html || '', bodySanitizeConfig)
  const blockTags = ['p', 'div', 'ul', 'ol', 'table']
  const blocks = []

  const pushParagraph = (nodes) => {
    const inline = normalizeInlineHtmlForDocx(nodes || [])
    if (inline.trim()) blocks.push(`<p>${inline}</p>`)
  }

  Array.from(wrapper.childNodes || []).forEach((node) => {
    if (node.nodeType === Node.TEXT_NODE) {
      if ((node.textContent || '').trim()) pushParagraph([node])
      return
    }
    if (node.nodeType !== Node.ELEMENT_NODE) return
    const tag = node.tagName.toLowerCase()
    if (tag === 'table') {
      blocks.push(normalizeTableHtmlForDocx(node))
      return
    }
    if (tag === 'ul' || tag === 'ol') {
      const items = Array.from(node.children || []).map((child) => `<li>${normalizeInlineHtmlForDocx(child.childNodes || []) || '&nbsp;'}</li>`).join('')
      if (items) blocks.push(`<${tag}>${items}</${tag}>`)
      return
    }
    if (tag === 'p') {
      pushParagraph(node.childNodes || [])
      return
    }
    if (tag === 'div') {
      const hasBlockChildren = Array.from(node.childNodes || []).some((child) => (
        child.nodeType === Node.ELEMENT_NODE && blockTags.includes(child.tagName.toLowerCase())
      ))
      if (!hasBlockChildren) {
        pushParagraph(node.childNodes || [])
        return
      }
      Array.from(node.childNodes || []).forEach((child) => {
        if (child.nodeType === Node.TEXT_NODE) {
          if ((child.textContent || '').trim()) pushParagraph([child])
          return
        }
        if (child.nodeType !== Node.ELEMENT_NODE) return
        const childTag = child.tagName.toLowerCase()
        if (childTag === 'table') {
          blocks.push(normalizeTableHtmlForDocx(child))
          return
        }
        if (childTag === 'ul' || childTag === 'ol') {
          const items = Array.from(child.children || []).map((item) => `<li>${normalizeInlineHtmlForDocx(item.childNodes || []) || '&nbsp;'}</li>`).join('')
          if (items) blocks.push(`<${childTag}>${items}</${childTag}>`)
          return
        }
        pushParagraph(child.childNodes || [])
      })
      return
    }
    pushParagraph([node])
  })

  return blocks.join('') || `<p>${htmlEscape(stripHtml(html || ''))}</p>`
}

const plainTextHtmlForDocx = (html) => {
  const text = stripHtml(html || '')
  const paragraphs = text
    .split(/\n{2,}/)
    .map((item) => item.trim())
    .filter(Boolean)
  if (!paragraphs.length) return '<p></p>'
  return paragraphs.map((item) => `<p>${htmlEscape(item).replace(/\n/g, '<br>')}</p>`).join('')
}

const generateDocxBuffer = async (docData) => {
  const templateBuffer = await fs.readFile(resolveTemplatePath(docData))
  const structuredBodyHtml = docData?.editor?.render?.body_html || ''
  const effectiveBodyHtml = structuredBodyHtml || docData.body || ''
  const bodyText = stripHtml(effectiveBodyHtml)
  const bodyLines = [{ text: DOCX_BODY_PLACEHOLDER }]
  const attachmentsText = (docData.attachments_list || '').toString()
  const attachmentsLines = attachmentsText
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line.length > 0)
    .map((line) => ({ text: line }))

  const recipientShortName = docData.recipient_short_name || ''
  const recipientToName = docData.recipient_to_name || ''
  const recipientAppeal = docData.recipient_appeal || ''
  const recipientEio = docData.recipient_eio || DEFAULT_RECIPIENT_EIO
  const recipientSalutation = docData.recipient_salutation || ''
  const recipientSalutationFull = `${recipientSalutation} ${recipientAppeal}`.trim()

  const renderTemplateZip = () => {
    const zip = new PizZip(templateBuffer)
    const doc = new Docxtemplater(zip, {
      paragraphLoop: true,
      linebreaks: true,
      nullGetter: () => ''
    })
    doc.render({
      ...flattenObject(docData),
      ...docData,
      outgoing_number: docData.outgoing_number || '',
      letter_date: formatDateLong(docData.letter_date),
      subject: docData.subject || '',
      body: bodyText,
      body_lines: bodyLines,
      recipient_company_name: docData.recipient_company_name || '',
      recipient_short_name: recipientShortName,
      recipient_to_name: recipientToName,
      recipient_appeal: recipientAppeal,
      recipient_eio: recipientEio,
      recipient_genitive_name: docData.recipient_genitive_name || '',
      recipient_salutation: recipientSalutation,
      recipient_salutation_full: recipientSalutationFull,
      attachments_list: attachmentsText,
      attachments_lines: attachmentsLines
    })
    return doc.getZip()
  }

  const bodyCandidates = [
    normalizeHtmlForDocx(effectiveBodyHtml),
    plainTextHtmlForDocx(effectiveBodyHtml)
  ].filter((value, index, list) => value && list.indexOf(value) === index)

  for (let index = 0; index < bodyCandidates.length; index += 1) {
    const renderedZip = renderTemplateZip()
    injectRichBodyIntoDocxZip(renderedZip, bodyCandidates[index])
    normalizeFloatingPictureLayers(renderedZip)
    if (!validateDocxDocumentXml(renderedZip)) {
      if (index < bodyCandidates.length - 1) continue
      throw new Error('Invalid DOCX XML after all fallbacks')
    }
    return renderedZip.generate({
      type: 'nodebuffer',
      mimeType: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    })
  }

  throw new Error('Failed to build DOCX body')
}

const main = async () => {
  const [, , inputPath, outputPath] = process.argv
  if (!inputPath || !outputPath) {
    console.error('Usage: node render_outgoing_docx.mjs <input.json> <output.docx>')
    process.exit(1)
  }
  const raw = (await fs.readFile(inputPath, 'utf8')).replace(/^\uFEFF/, '')
  const payload = JSON.parse(raw)
  const buffer = await generateDocxBuffer(payload)
  await fs.writeFile(outputPath, buffer)
}

main().catch((error) => {
  console.error(error)
  process.exit(1)
})
