import { Node, mergeAttributes } from '@tiptap/core'

export default Node.create({
  name: 'fieldChip',
  group: 'inline',
  inline: true,
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
        tag: 'span[data-field-chip="true"]',
      },
    ]
  },

  renderHTML({ HTMLAttributes }) {
    const label = HTMLAttributes.label || HTMLAttributes.key || 'Поле'
    return [
      'span',
      mergeAttributes(HTMLAttributes, {
        'data-field-chip': 'true',
        'data-field-key': HTMLAttributes.key || '',
        class: 'structured-field-chip',
        contenteditable: 'false',
      }),
      `{{ ${label} }}`,
    ]
  },

  renderText({ node }) {
    return `{{ ${node.attrs?.key || ''} }}`
  },

  addCommands() {
    return {
      insertFieldChip:
        (attrs) =>
        ({ commands }) =>
          commands.insertContent({
            type: this.name,
            attrs,
          }),
    }
  },
})
