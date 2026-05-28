const HUNDREDS = ['', 'сто', 'двести', 'триста', 'четыреста', 'пятьсот', 'шестьсот', 'семьсот', 'восемьсот', 'девятьсот']
const TENS = ['', '', 'двадцать', 'тридцать', 'сорок', 'пятьдесят', 'шестьдесят', 'семьдесят', 'восемьдесят', 'девяносто']
const TEENS = ['десять', 'одиннадцать', 'двенадцать', 'тринадцать', 'четырнадцать', 'пятнадцать', 'шестнадцать', 'семнадцать', 'восемнадцать', 'девятнадцать']
const ONES = {
  masculine: ['', 'один', 'два', 'три', 'четыре', 'пять', 'шесть', 'семь', 'восемь', 'девять'],
  feminine: ['', 'одна', 'две', 'три', 'четыре', 'пять', 'шесть', 'семь', 'восемь', 'девять']
}

const SCALES = [
  { forms: ['', '', ''], gender: 'masculine' },
  { forms: ['тысяча', 'тысячи', 'тысяч'], gender: 'feminine' },
  { forms: ['миллион', 'миллиона', 'миллионов'], gender: 'masculine' },
  { forms: ['миллиард', 'миллиарда', 'миллиардов'], gender: 'masculine' },
  { forms: ['триллион', 'триллиона', 'триллионов'], gender: 'masculine' }
]

function pluralize(value, one, few, many) {
  const abs = Math.abs(Number(value) || 0)
  const mod100 = abs % 100
  const mod10 = abs % 10
  if (mod100 >= 11 && mod100 <= 14) return many
  if (mod10 === 1) return one
  if (mod10 >= 2 && mod10 <= 4) return few
  return many
}

function roundMoney(value) {
  return Math.round((Number(value || 0) + Number.EPSILON) * 100) / 100
}

function triadToWords(value, gender) {
  const number = Number(value) || 0
  if (!number) return ''

  const parts = []
  const hundreds = Math.floor(number / 100)
  const tensUnits = number % 100

  if (hundreds) {
    parts.push(HUNDREDS[hundreds])
  }

  if (tensUnits >= 10 && tensUnits <= 19) {
    parts.push(TEENS[tensUnits - 10])
    return parts.join(' ')
  }

  const tens = Math.floor(tensUnits / 10)
  const ones = tensUnits % 10

  if (tens) {
    parts.push(TENS[tens])
  }

  if (ones) {
    parts.push(ONES[gender]?.[ones] || ONES.masculine[ones])
  }

  return parts.join(' ')
}

function integerToWords(value) {
  let number = Math.floor(Math.abs(Number(value) || 0))
  if (!number) return 'ноль'

  const groups = []
  while (number > 0) {
    groups.push(number % 1000)
    number = Math.floor(number / 1000)
  }

  const parts = []
  for (let index = groups.length - 1; index >= 0; index -= 1) {
    const groupValue = groups[index]
    if (!groupValue) continue

    const scale = SCALES[index] || SCALES[0]
    const words = triadToWords(groupValue, scale.gender)
    if (words) {
      parts.push(words)
    }

    if (index > 0) {
      parts.push(pluralize(groupValue, scale.forms[0], scale.forms[1], scale.forms[2]))
    }
  }

  return parts.join(' ').replace(/\s+/g, ' ').trim()
}

function capitalize(text) {
  if (!text) return ''
  return text.charAt(0).toUpperCase() + text.slice(1)
}

export function formatRussianMoneyWords(value, options = {}) {
  const { parenthesized = false } = options
  const numericValue = Number(value || 0)
  const isNegative = numericValue < 0
  let amount = roundMoney(Math.abs(numericValue))
  let rubles = Math.floor(amount)
  let kopecks = Math.round((amount - rubles) * 100)

  if (kopecks === 100) {
    rubles += 1
    kopecks = 0
  }

  const rublesWords = integerToWords(rubles)
  const rublesLabel = pluralize(rubles, 'рубль', 'рубля', 'рублей')
  const kopecksLabel = pluralize(kopecks, 'копейка', 'копейки', 'копеек')
  const kopecksValue = String(kopecks).padStart(2, '0')

  let result = `${rublesWords} ${rublesLabel} ${kopecksValue} ${kopecksLabel}`.replace(/\s+/g, ' ').trim()
  result = capitalize(result)

  if (isNegative) {
    result = `Минус ${result.charAt(0).toLowerCase()}${result.slice(1)}`
  }

  return parenthesized ? `(${result})` : result
}
