import { Node, mergeAttributes } from '@tiptap/core'

export default Node.create({
  name: 'templateBlock',
  group: 'block',
  atom: true,
  selectable: true,

  addAttributes() {
    return {
      key: {
        default: '',
      },
      label: {
        default: '',
      },
    }
  },

  parseHTML() {
    return [
      {
        tag: 'div[data-template-block="true"]',
      },
    ]
  },

  renderHTML({ HTMLAttributes }) {
    const label = HTMLAttributes.label || HTMLAttributes.key || 'Шаблонный блок'
    return [
      'div',
      mergeAttributes(HTMLAttributes, {
        'data-template-block': 'true',
        'data-template-key': HTMLAttributes.key || '',
        class: 'structured-template-block',
        contenteditable: 'false',
      }),
      `Шаблон: ${label}`,
    ]
  },

  renderText({ node }) {
    return `[${node.attrs?.label || node.attrs?.key || 'Шаблонный блок'}]`
  },

  addCommands() {
    return {
      insertTemplateBlock:
        (attrs) =>
        ({ commands }) =>
          commands.insertContent({
            type: this.name,
            attrs,
          }),
    }
  },
})
