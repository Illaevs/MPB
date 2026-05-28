const variant = (import.meta.env.VITE_APP_VARIANT || 'default').trim().toLowerCase()

export const isTestPortalVariant = variant === 'testportal'

export const appBrandPrimary = import.meta.env.VITE_APP_BRAND_NAME || 'Nexus'
export const appBrandSecondary = import.meta.env.VITE_APP_BRAND_SUFFIX || 'tech'
export const appSystemName = import.meta.env.VITE_APP_SYSTEM_NAME || 'Enterprise система управления'
export const appCrmName = import.meta.env.VITE_APP_CRM_NAME || 'Enterprise система управления'

const defaultOurCompanies = [
  { key: 'normbud', label: 'НОРМБУД', name: 'НОРМБУД' },
  { key: 'bayer', label: 'БАЙЕР', name: 'БАЙЕР' },
  { key: 'morozov', label: 'ИП Морозов', name: 'ИП Морозов' }
]

const testPortalOurCompanies = [
  { key: 'normbud', label: 'Nexus Beta', name: 'Nexus Beta' },
  { key: 'bayer', label: 'Nexus Alpha', name: 'Nexus Alpha' },
  { key: 'morozov', label: 'Nexus Solo', name: 'Nexus Solo' }
]

export const staticOurCompanies = isTestPortalVariant ? testPortalOurCompanies : defaultOurCompanies

const defaultPreviewProfiles = {
  bayer: {
    key: 'bayer',
    logo: '/templates/_extracted_preview/outgoing_bayer_image2.png',
    signature: '/templates/_extracted_preview/outgoing_bayer_image1.png',
    infoLines: [
      'Общество с ограниченной ответственностью «БАЙЕР»',
      '(ООО «БАЙЕР»)',
      'Эл. почта: info@byer.ru',
      'Тел. +7 (495) 128-11-77'
    ],
    footerLines: [
      '127434, г. Москва, вн. тер. г. муниципальный округ Тимирязевский, ш. Дмитровское, д. 7 к. 2, помещ. 5А/1',
      'ИНН 7722685412, КПП 771301001, ОГРН 1097746256211'
    ],
    signerTitle: 'Генеральный директор',
    signerName: 'О.А. Морозов'
  },
  morozov: {
    key: 'morozov',
    logo: '',
    signature: '/templates/_extracted_preview/outgoing_morozov_image1.png',
    infoLines: [
      'Индивидуальный предприниматель Морозов Олег Артурович',
      'ОГРНИП 318774600197203',
      '129226, г. Москва, пр-т Мира, д. 179а, кв. 27',
      'Эл. почта: morozov@proriski.ru',
      'Тел. +7 (903) 160-18-01'
    ],
    footerLines: [],
    signerTitle: 'С уважением, Руководитель',
    signerName: 'О.А. Морозов'
  },
  normbud: {
    key: 'normbud',
    logo: '/templates/_extracted_preview/outgoing_normbud_image2.png',
    signature: '/templates/_extracted_preview/outgoing_normbud_image1.png',
    infoLines: [
      'Общество с ограниченной ответственностью «НОРМБУД»',
      '(ООО «НОРМБУД»)',
      '129226, г. Москва, вн. тер. г. муниципальный округ Ростокино, ул. Сельскохозяйственная, д. 4 стр. 16',
      'ИНН 7733316255, КПП 771701001, ОГРН 1177746139636',
      'e-mail: info@normbud.ru'
    ],
    footerLines: [],
    signerTitle: 'Генеральный директор',
    signerName: 'С.В. Воронин'
  }
}

const testPortalPreviewProfiles = {
  bayer: {
    key: 'bayer',
    logo: '/templates/_extracted_preview/outgoing_bayer_image2.png',
    signature: '/templates/_extracted_preview/outgoing_bayer_image1.png',
    infoLines: [
      'Общество с ограниченной ответственностью «НЕКСУС АЛЬФА»',
      '(ООО «НЕКСУС АЛЬФА»)',
      'Эл. почта: alpha@nexus.test',
      'Тел. +7 (495) 000-10-10'
    ],
    footerLines: [
      'г. Москва, Тестовый проезд, д. 10',
      'ИНН 7700100010, КПП 770001001, ОГРН 1267700001010'
    ],
    signerTitle: 'Генеральный директор',
    signerName: 'Тест Тестов'
  },
  morozov: {
    key: 'morozov',
    logo: '',
    signature: '/templates/_extracted_preview/outgoing_morozov_image1.png',
    infoLines: [
      'Индивидуальный предприниматель Нексус Соло',
      'ОГРНИП 326770000303030',
      'г. Москва, Тестовый проезд, д. 30',
      'Эл. почта: solo@nexus.test',
      'Тел. +7 (495) 000-30-30'
    ],
    footerLines: [],
    signerTitle: 'Руководитель',
    signerName: 'Н. Соло'
  },
  normbud: {
    key: 'normbud',
    logo: '/templates/_extracted_preview/outgoing_normbud_image2.png',
    signature: '/templates/_extracted_preview/outgoing_normbud_image1.png',
    infoLines: [
      'Общество с ограниченной ответственностью «НЕКСУС БЕТА»',
      '(ООО «НЕКСУС БЕТА»)',
      'г. Москва, Тестовый проезд, д. 20',
      'ИНН 7700200020, КПП 770002001, ОГРН 1267700002020',
      'e-mail: beta@nexus.test'
    ],
    footerLines: [],
    signerTitle: 'Генеральный директор',
    signerName: 'Б. Тестова'
  }
}

export const previewCompanyProfiles = isTestPortalVariant ? testPortalPreviewProfiles : defaultPreviewProfiles
