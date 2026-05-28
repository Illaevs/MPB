/**
 * Detects if text content looks like corrupted/garbled encoding.
 * Used to filter out unreadable email bodies.
 */
export function looksGibberish(text) {
  if (!text) return true
  const stripped = text.trim()
  if (!stripped) return true
  // Binary file signatures — definitely gibberish
  if (/%PDF-|PK\x03\x04/.test(stripped)) return true
  // MIME headers are NOT gibberish — they need decoding, not rejection
  // If text contains HTML tags, it's structured content
  if (/<\/?(html|body|head|div|p|table|br|span|ul|ol|li|blockquote|a|td|tr|th|img|h[1-6])\b/i.test(stripped)) return false
  // Short text is almost never gibberish
  if (stripped.length < 20) return false

  const allowed = (stripped.match(/[A-Za-zА-Яа-яЁё0-9\s.,;:!?'"()\[\]{}<>/@#$%^&*+=_\-—–«»№…\u00C0-\u024F\u0370-\u03FF\u4E00-\u9FFF\u3040-\u30FF]/g) || []).length
  const allowedRatio = allowed / stripped.length
  const control = (stripped.match(/[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/g) || []).length // exclude \t \n \r
  const nonPrintable = (stripped.match(/[^\x09\x0A\x0D\x20-\x7E\u00A0-\u024F\u0370-\u03FF\u0400-\u04FF\u4E00-\u9FFF\u3040-\u30FF]/g) || []).length
  const replacement = (stripped.match(/\uFFFD/g) || []).length

  if (control > 2 && stripped.length > 24) return true
  if (replacement > 0 && replacement / stripped.length > 0.03) return true
  if (nonPrintable / stripped.length > 0.1) return true
  if (stripped.length > 200 && allowedRatio < 0.6) return true
  if (stripped.length > 80 && allowedRatio < 0.5) return true
  if (stripped.length > 40 && allowedRatio < 0.4) return true

  const tokens = stripped.split(/\s+/).filter(Boolean)
  const spaces = (stripped.match(/\s/g) || []).length
  const maxToken = tokens.length ? Math.max(...tokens.map(t => t.length)) : 0
  if (stripped.length > 80 && maxToken / stripped.length > 0.9) return true
  if (maxToken > 200 && spaces < 4) return true

  const letters = (stripped.match(/[A-Za-zА-Яа-яЁё]/g) || []).length
  const digits = (stripped.match(/[0-9]/g) || []).length
  const vowels = 'aeiouyAEIOUYаеёиоуыэюяАЕЁИОУЫЭЮЯ'
  const vowelCount = (stripped.match(new RegExp(`[${vowels}]`, 'g')) || []).length

  if (spaces <= 1 && stripped.length > 40) {
    if ((letters + digits) / stripped.length < 0.4) return true
    if (letters && letters > 20 && vowelCount / Math.max(letters, 1) < 0.2) return true
  }

  const compact = stripped.replace(/\s+/g, '')
  if (compact.length > 160 && /^[A-Za-z0-9+/=]+$/.test(compact)) return true

  return false
}

/**
 * Detect and fix "mojibake" — when windows-1251 or KOI8-R bytes
 * were incorrectly decoded as UTF-8 (or latin1), producing garbled text.
 * Converts each JS char back to its byte value and re-decodes.
 */
export function fixMojibake(text) {
  if (!text || text.length < 8) return text

  // Quick check: if text already has clean Cyrillic, don't touch it
  const cyrCount = (text.match(/[А-Яа-яЁё]/g) || []).length
  if (cyrCount / text.length > 0.15) return text

  // Detect patterns typical for win-1251 bytes misread as latin1/UTF-8
  // Win-1251 Cyrillic uppercase: 0xC0-0xDF → latin1: À-ß
  // Win-1251 Cyrillic lowercase: 0xE0-0xFF → latin1: à-ÿ
  // KOI8-R Cyrillic: 0xC0-0xFF → similar latin1 range
  const latin1Cyrillic = (text.match(/[\u00C0-\u00FF]/g) || []).length
  const hasMultibyteMojibake = /[\u0400-\u04FF].*[\u00C0-\u00FF]|[\u00C0-\u00FF].*[\u0400-\u04FF]/.test(text)

  // Pattern 1: mostly latin1 high bytes (win-1251 interpreted as latin1)
  if (latin1Cyrillic > 4 && latin1Cyrillic / text.length > 0.1) {
    const bytes = new Uint8Array(text.length)
    let allSingleByte = true
    for (let i = 0; i < text.length; i++) {
      const code = text.charCodeAt(i)
      if (code > 0xFF) { allSingleByte = false; break }
      bytes[i] = code
    }
    if (allSingleByte) {
      const result = decodeWithFallback(bytes, 'windows-1251')
      if (!looksGibberish(result)) {
        const newCyr = (result.match(/[А-Яа-яЁё]/g) || []).length
        if (newCyr > cyrCount) return result
      }
    }
  }

  // Pattern 2a: UTF-8 double-encoding via latin1 — chars all <= 0xFF
  // Produces sequences like пÑÐ¸Ð²ÐµÑ (привет) — 2-byte UTF-8 of Cyrillic chars
  const utf8DoublePat = /[\u0400-\u04FF][\u0080-\u00BF]|[\u00C0-\u00DF][\u0080-\u00BF]/
  if (utf8DoublePat.test(text) || hasMultibyteMojibake) {
    try {
      // Try to extract raw bytes assuming each char <= 0xFF
      const bytes = []
      let ok = true
      for (let i = 0; i < text.length; i++) {
        const code = text.charCodeAt(i)
        if (code > 0xFF) { ok = false; break }
        bytes.push(code)
      }
      if (ok && bytes.length > 0) {
        const arr = Uint8Array.from(bytes)
        // Try UTF-8 decode of those bytes (un-doing the latin1 interpretation)
        try {
          const utf8Result = new TextDecoder('utf-8', { fatal: true }).decode(arr)
          const newCyr = (utf8Result.match(/[А-Яа-яЁё]/g) || []).length
          if (newCyr > cyrCount && !looksGibberish(utf8Result)) return utf8Result
        } catch { /* not valid UTF-8 bytes, try win-1251 */ }
        const win1251Result = decodeWithFallback(arr, 'windows-1251')
        if (!looksGibberish(win1251Result)) {
          const newCyr2 = (win1251Result.match(/[А-Яа-яЁё]/g) || []).length
          if (newCyr2 > cyrCount) return win1251Result
        }
      }
    } catch { /* ignore */ }
  }

  // Pattern 2b: UTF-8 double-encoding via windows-1251 — chars > 0xFF
  // When UTF-8 bytes are decoded as windows-1251, each 2-byte UTF-8 Cyrillic char
  // becomes 2 win-1251 chars: e.g. D0 9F (П in UTF-8) → Р (0xD0→U+0420) + џ (0x9F→U+045F)
  // Signature: text has many Р (U+0420) or С (U+0421) chars — these come from UTF-8 lead bytes 0xD0/0xD1
  // which are the lead bytes for all Cyrillic chars in UTF-8
  const countR = (text.match(/Р/g) || []).length
  const countS = (text.match(/С/g) || []).length
  if ((countR + countS) > text.length * 0.15 && (countR + countS) >= 4) {
    try {
      // Encode text back to windows-1251 bytes, then decode those bytes as UTF-8
      // We need a win-1251 encoding table (JS TextEncoder only supports UTF-8)
      const win1251Bytes = encodeToWin1251(text)
      if (win1251Bytes) {
        try {
          const utf8Result = new TextDecoder('utf-8', { fatal: true }).decode(win1251Bytes)
          // Compare by Cyrillic ratio (recovered text is shorter, so raw count comparison fails)
          const newCyrRatio = (utf8Result.match(/[А-Яа-яЁё]/g) || []).length / Math.max(utf8Result.length, 1)
          const oldCyrRatio = cyrCount / Math.max(text.length, 1)
          if (newCyrRatio > oldCyrRatio && !looksGibberish(utf8Result)) return utf8Result
        } catch { /* not valid UTF-8 after re-encoding */ }
      }
    } catch { /* ignore */ }
  }

  // Pattern 3: 7-bit stripped CP1251 (8th bit lost in SMTP transit)
  // CP1251 Cyrillic bytes had their high bit stripped during 7-bit SMTP transit:
  //   а-п (0xE0-0xEF) → 0x30-0x3F = digits 0-9 and :;<=>?
  //   р-я (0xF0-0xFF) → 0x40-0x4F = @A-O
  //   Р-Я (0xD0-0xDF) → 0x20-0x2F = space and !"#$%&'()*+,-./
  //   А-П (0xC0-0xCF) → 0x10-0x1F = control chars (LOST)
  // Detection: text has almost no real Cyrillic, but lots of mixed digit-symbol sequences
  if (cyrCount < text.length * 0.05) {
    // Count chars in 0x30-0x4F range (would be lowercase а-я if +0xB0)
    const potentialCyrLower = (text.match(/[0-9:;<=>?@A-O]/g) || []).length
    const spaces = (text.match(/\s/g) || []).length
    const totalNonSpace = text.length - spaces
    if (potentialCyrLower > 8 && totalNonSpace > 0 && potentialCyrLower / totalNonSpace > 0.4) {
      // Heuristic: normal text shouldn't have sequences like ";53" ">1@07><" "A2O70BLAO"
      const suspiciousSeqs = text.match(/[0-9:;<=>?@A-O]{3,}/g) || []
      if (suspiciousSeqs.length >= 2) {
        // Recovery: each byte originally had 0xB0 subtracted during transit
        // 0x30-0x4F (+0xB0) → 0xE0-0xFF = lowercase а-я in CP1251
        // 0x21-0x2F (+0xB0) → 0xD1-0xDF = uppercase С-Я in CP1251
        // 0x10-0x1F (+0xB0) → 0xC0-0xCF = uppercase А-П (control chars, usually lost)
        // 0x20 = space (ambiguous with Р=0xD0, keep as space)
        const bytes = []
        for (let i = 0; i < text.length; i++) {
          const code = text.charCodeAt(i)
          const next = i < text.length - 1 ? text.charCodeAt(i + 1) : -1
          const prev = i > 0 ? text.charCodeAt(i - 1) : -1
          const nShifted = (next >= 0x30 && next <= 0x4F)
          const pShifted = (prev >= 0x30 && prev <= 0x4F)
          const atWordStart = (prev === 0x20 || prev === 0x0A || prev === 0x0D || prev === -1) && nShifted

          if (code >= 0x30 && code <= 0x4F) {
            // Main range: digits/symbols → lowercase а-я, @A-O → uppercase/lowercase
            if (code >= 0x41 && code <= 0x4F) {
              // Could be Latin A-O or shifted Cyrillic
              const nextLatin = (next >= 0x50 && next <= 0x7A)
              const prevLatin = (prev >= 0x50 && prev <= 0x7A)
              if (nextLatin || prevLatin) {
                bytes.push(code) // keep as Latin
                continue
              }
            }
            if (code === 0x3F) {
              // ? → п OR question mark
              const atEnd = (next === -1 || next === 0x20 || next === 0x0A || next === 0x0D)
              const prevIsShiftable = (prev >= 0x30 && prev <= 0x4F)
              const longWord = prevIsShiftable && i >= 2 && (text.charCodeAt(i - 2) >= 0x30 && text.charCodeAt(i - 2) <= 0x4F)
              if (atEnd && longWord) {
                bytes.push(code) // real question mark
                continue
              }
            }
            bytes.push(code + 0xB0)
          } else if (code === 0x20) {
            bytes.push(code) // Always keep spaces
          } else if (code >= 0x21 && code <= 0x2F) {
            // Ambiguous: punctuation or uppercase Р-Я
            if (code === 0x2C) {
              // , → Ь or comma. Keep as comma always (very common punct)
              bytes.push(code)
            } else if (code === 0x2E) {
              // . → Ю or period
              if (next === -1 || next === 0x20 || next === 0x0A || next === 0x0D) bytes.push(code)
              else if (pShifted && nShifted) bytes.push(code + 0xB0)
              else bytes.push(code)
            } else if (code === 0x21) {
              // ! → С or exclamation
              if ((next === -1 || next === 0x20 || next === 0x0A || next === 0x0D) && !atWordStart) bytes.push(code)
              else if (pShifted || nShifted || atWordStart) bytes.push(code + 0xB0)
              else bytes.push(code)
            } else if (code === 0x2D) {
              // - → Э or dash
              if ((prev === 0x20 || prev === -1) && (next === 0x20 || next === -1)) bytes.push(code)
              else if (pShifted && nShifted) bytes.push(code + 0xB0)
              else bytes.push(code)
            } else {
              // Other punct: shift if between shifted chars or at word start
              if ((pShifted && nShifted) || atWordStart) bytes.push(code + 0xB0)
              else bytes.push(code)
            }
          } else if (code >= 0x10 && code <= 0x1F) {
            // Control chars: could be shifted uppercase А-П
            bytes.push(code + 0xB0)
          } else {
            bytes.push(code > 0xFF ? 0x20 : code)
          }
        }
        try {
          const recovered = new TextDecoder('windows-1251', { fatal: false }).decode(Uint8Array.from(bytes))
          const newCyr = (recovered.match(/[А-Яа-яЁё]/g) || []).length
          if (newCyr > cyrCount + 5) {
            return recovered
          }
        } catch { /* ignore */ }
      }
    }
  }

  // Pattern 4: 7-bit masked CP1251 (byte & 0x7F)
  // CP1251 uppercase 0xC0-0xDF -> 0x40-0x5F (@ to _)
  // CP1251 lowercase 0xE0-0xFF -> 0x60-0x7F (` to DEL)
  if (cyrCount < text.length * 0.05) {
    let asciiHi = 0
    let nonSpace = 0
    for (let i = 0; i < text.length; i++) {
      const code = text.charCodeAt(i)
      if (code !== 0x20 && code !== 0x0A && code !== 0x0D && code !== 0x09) nonSpace++
      if (code >= 0x40 && code <= 0x7F) asciiHi++
    }
    if (asciiHi > 8 && nonSpace > 0 && asciiHi / nonSpace > 0.35) {
      const suspicious = text.match(/[\x40-\x7F]{4,}/g) || []
      if (suspicious.length >= 2) {
        const protectedMask = new Array(text.length).fill(false)
        const urlRe = /https?:\/\/[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]+/g
        const emailRe = /[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/g
        let match
        while ((match = urlRe.exec(text))) {
          for (let i = match.index; i < match.index + match[0].length; i++) protectedMask[i] = true
        }
        while ((match = emailRe.exec(text))) {
          for (let i = match.index; i < match.index + match[0].length; i++) protectedMask[i] = true
        }
        const bytes = new Uint8Array(text.length)
        for (let i = 0; i < text.length; i++) {
          const code = text.charCodeAt(i)
          if (code > 0xFF) {
            bytes[i] = 0x20
            continue
          }
          if (protectedMask[i]) {
            bytes[i] = code
            continue
          }
          if (code >= 0x40 && code <= 0x7F) {
            bytes[i] = code + 0x80
          } else {
            bytes[i] = code
          }
        }
        try {
          const recovered = new TextDecoder('windows-1251', { fatal: false }).decode(bytes)
          const newCyr = (recovered.match(/[А-Яа-яЁё]/g) || []).length
          if (newCyr > cyrCount + 5 && !looksGibberish(recovered)) return recovered
        } catch { /* ignore */ }
      }
    }
  }

  return text
}

/**
 * Format plain text with `>` quoted lines into simple HTML with styled blockquotes.
 * Also preserves line breaks and basic structure.
 */
export function formatPlainTextToHtml(text) {
  if (!text) return ''
  const lines = text.split(/\r?\n/)
  const result = []
  let inQuote = false
  let quoteLines = []

  const flushQuote = () => {
    if (quoteLines.length) {
      const inner = quoteLines.map(l => escapeHtml(l)).join('<br>')
      result.push(`<blockquote class="quoted-text">${inner}</blockquote>`)
      quoteLines = []
    }
    inQuote = false
  }

  for (const line of lines) {
    const isQuoted = /^>+\s?/.test(line)
    if (isQuoted) {
      if (!inQuote) inQuote = true
      // Strip leading > and spaces
      quoteLines.push(line.replace(/^>+\s?/, ''))
    } else {
      if (inQuote) flushQuote()
      // Detect separator lines (--- or ___ or === or * * *)
      if (/^[-_=*]{3,}\s*$/.test(line.trim())) {
        result.push('<hr>')
      } else {
        result.push(escapeHtml(line) + '<br>')
      }
    }
  }
  if (inQuote) flushQuote()
  return result.join('\n')
}

function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function detectCharset(contentType, raw) {
  const ct = contentType || ''
  const header = raw || ''
  const re = /charset\s*=\s*["']?([^;"'\s]+)/i
  const ctMatch = ct.match(re)
  if (ctMatch) return ctMatch[1].toLowerCase()
  const rawMatch = header.match(re)
  if (rawMatch) return rawMatch[1].toLowerCase()
  return ''
}

function decodeBytes(bytes, charset) {
  try {
    return new TextDecoder(charset, { fatal: false }).decode(bytes)
  } catch {
    return new TextDecoder('utf-8', { fatal: false }).decode(bytes)
  }
}

function decodeWithFallback(bytes, preferred) {
  const candidates = [preferred, 'utf-8', 'windows-1251', 'koi8-r', 'iso-8859-1'].filter(Boolean)
  const seen = new Set()
  for (const enc of candidates) {
    if (seen.has(enc)) continue
    seen.add(enc)
    const decoded = decodeBytes(bytes, enc)
    if (!looksGibberish(decoded)) return decoded
  }
  return decodeBytes(bytes, preferred || 'utf-8')
}

/**
 * Encode a JS string to windows-1251 bytes.
 * Returns Uint8Array or null if a char can't be mapped.
 */
function encodeToWin1251(text) {
  // Build reverse mapping: Unicode codepoint → win-1251 byte
  // We decode all 256 byte values through win-1251 to build the table
  if (!encodeToWin1251._table) {
    const table = new Map()
    const singleBytes = new Uint8Array(1)
    for (let b = 0; b < 256; b++) {
      singleBytes[0] = b
      try {
        const ch = new TextDecoder('windows-1251', { fatal: true }).decode(singleBytes)
        if (ch.length === 1) {
          table.set(ch.charCodeAt(0), b)
        }
      } catch { /* unmappable byte */ }
    }
    encodeToWin1251._table = table
  }
  const table = encodeToWin1251._table
  const bytes = []
  for (let i = 0; i < text.length; i++) {
    const code = text.charCodeAt(i)
    if (code < 0x80) {
      bytes.push(code)
    } else {
      const b = table.get(code)
      if (b === undefined) return null // can't encode this char
      bytes.push(b)
    }
  }
  return Uint8Array.from(bytes)
}

function decodeBase64Block(block, charset) {
  try {
    const bytes = Uint8Array.from(atob(block), c => c.charCodeAt(0))
    return decodeWithFallback(bytes, charset)
  } catch {
    return ''
  }
}

function decodeQuotedPrintable(raw, charset) {
  if (!raw) return ''
  const cleaned = raw.replace(/=\r?\n/g, '')
  const bytes = []
  for (let i = 0; i < cleaned.length; i++) {
    const ch = cleaned[i]
    if (ch === '=' && i + 2 < cleaned.length) {
      const hex = cleaned.slice(i + 1, i + 3)
      if (/^[0-9A-Fa-f]{2}$/.test(hex)) {
        bytes.push(parseInt(hex, 16))
        i += 2
        continue
      }
    }
    bytes.push(cleaned.charCodeAt(i) & 0xff)
  }
  return decodeWithFallback(Uint8Array.from(bytes), charset)
}

function extractLongestBase64Block(text) {
  const lines = text.split(/\r?\n/)
  const blocks = []
  let current = []
  for (const rawLine of lines) {
    const line = rawLine.trim()
    if (line.length >= 16 && /^[A-Za-z0-9+/=]+$/.test(line)) {
      current.push(line)
    } else if (current.length) {
      blocks.push(current.join(''))
      current = []
    }
  }
  if (current.length) blocks.push(current.join(''))
  if (!blocks.length) return ''
  return blocks.reduce((a, b) => (b.length > a.length ? b : a), '')
}

function tryDecodeBase64Body(raw, charset) {
  if (!raw) return ''
  if (!/content-transfer-encoding:\s*base64/i.test(raw) && raw.length < 200) return ''
  const block = extractLongestBase64Block(raw)
  if (!block || block.length < 200) return ''
  const decoded = decodeBase64Block(block, charset)
  if (!decoded) return ''
  if (looksGibberish(decoded)) return ''
  return decoded
}

function tryDecodeQuotedPrintableBody(raw, charset) {
  if (!raw) return ''
  const hasMarker = /content-transfer-encoding:\s*quoted-printable/i.test(raw)
  const looksQP = /=([0-9A-Fa-f]{2})/.test(raw)
  if (!hasMarker && !looksQP) return ''
  const decoded = decodeQuotedPrintable(raw, charset)
  if (!decoded) return ''
  if (looksGibberish(decoded)) return ''
  return decoded
}

function extractHtmlSegment(body) {
  const htmlMatch = body.match(/<!doctype[\s\S]*<\/html>/i) || body.match(/<html[\s\S]*<\/html>/i)
  if (htmlMatch) return htmlMatch[0]
  const bodyMatch = body.match(/<body[\s\S]*<\/body>/i)
  if (bodyMatch) return bodyMatch[0]
  return ''
}

/**
 * Normalize raw email body HTML: strip doctype/html/head/body wrappers,
 * detect double-escaped HTML, clean up null chars.
 */
export function normalizeEmailBody(rawBody, contentType) {
  let body = (rawBody || '').replace(/\u0000/g, '')
  const ct = (contentType || 'text/plain').toLowerCase()
  const charset = detectCharset(ct, body)
  const decoded = tryDecodeBase64Body(body, charset)
  if (decoded) body = decoded
  else {
    const qpDecoded = tryDecodeQuotedPrintableBody(body, charset)
    if (qpDecoded) body = qpDecoded
  }
  const htmlMarker = /<\/?(html|body|head|div|p|table|br|span|meta|style)\b/i
  let isHtml = ct.includes('html') || htmlMarker.test(body) || /<!doctype/i.test(body)
  const extractedHtml = extractHtmlSegment(body)
  if (extractedHtml) {
    body = extractedHtml
    isHtml = true
  }

  if (isHtml) {
    body = body.replace(/<style[\s\S]*?<\/style>/gi, '')
  }

  if (!isHtml && /&lt;\/?(html|body|head|div|p|table|br|span)/i.test(body)) {
    const parsed = new DOMParser().parseFromString(body, 'text/html')
    const unescaped = parsed.documentElement.textContent || ''
    if (/<\/?(html|body|head|div|p|table|br|span)\b/i.test(unescaped) || /<!doctype/i.test(unescaped)) {
      body = unescaped
      isHtml = true
    }
  }

  const cleaned = body
    .replace(/<!doctype[^>]*>/gi, '')
    .replace(/<meta[^>]*>/gi, '')
    .replace(/<\/?html[^>]*>/gi, '')
    .replace(/<\/?head[^>]*>/gi, '')
    .replace(/<\/?body[^>]*>/gi, '')
    .trim()

  const html = isHtml ? cleaned : ''
  const text = !isHtml ? body : ''

  // For HTML: don't reject based on stripped text — HTML emails with tables/images
  // may have very little visible text. Trust the HTML structure.
  // Only reject if the HTML itself is truly empty after stripping.
  let finalHtml = html
  if (html) {
    const strippedHtml = html.replace(/<[^>]+>/g, '').replace(/&nbsp;/gi, ' ').replace(/\s+/g, ' ').trim()
    // Only reject if completely empty (no text at all)
    if (!strippedHtml) finalHtml = ''
  }

  // Try to fix mojibake on text bodies
  let finalText = text
  if (text) {
    const fixed = fixMojibake(text)
    finalText = fixed
  }
  const badText = finalText && looksGibberish(finalText)

  // Also try mojibake fix on HTML text content (sometimes HTML body has garbled text nodes)
  if (finalHtml) {
    const textContent = finalHtml.replace(/<[^>]+>/g, '').replace(/&nbsp;/gi, ' ').trim()
    if (textContent && looksGibberish(textContent)) {
      const fixedHtml = fixMojibake(textContent)
      if (fixedHtml !== textContent && !looksGibberish(fixedHtml)) {
        // The HTML had garbled text — return as plain text instead
        return { body_html: '', body_text: fixedHtml }
      }
      // If visible text is unreadable, do not render the HTML as a valid email body.
      return { body_html: '', body_text: '' }
    }
  }

  return {
    body_html: finalHtml,
    body_text: badText ? '' : finalText
  }
}
