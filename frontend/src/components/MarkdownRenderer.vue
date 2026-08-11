<template>
  <div class="markdown-renderer" @click="handleClick">
    <MdPreview 
      :model-value="content" 
      :theme="theme"
      :preview-theme="previewTheme"
      :code-theme="codeTheme"
      :show-code-row-number="true"
      :no-katex="false"
      :no-mermaid="true"
      :no-highlight="false"
    />
  </div>
</template>

<script setup>
import { MdPreview } from 'md-editor-v3'
import 'md-editor-v3/lib/preview.css'
import 'md-editor-v3/lib/style.css'

const props = defineProps({
  content: {
    type: String,
    default: ''
  },
  theme: {
    type: String,
    default: 'light'
  },
  previewTheme: {
    type: String,
    default: 'github'
  },
  codeTheme: {
    type: String,
    default: 'github'
  }
})

const emit = defineEmits(['link-click'])

const handleClick = (e) => {
  const link = e.target.closest('a')
  if (link) {
    const href = link.getAttribute('href')
    if (href && href.endsWith('.md')) {
      e.preventDefault()
      const fileName = href.split('/').pop().replace('.md', '')
      emit('link-click', fileName)
    }
  }
}
</script>

<style>
.markdown-renderer {
  width: 100%;
  overflow-wrap: break-word;
}

.markdown-renderer .md-editor,
.markdown-renderer .md-editor-preview,
.markdown-renderer .md-preview {
  background: transparent !important;
  padding: 0 !important;
  margin: 0 !important;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.markdown-renderer .md-editor-preview > *,
.markdown-renderer .md-preview > * {
  margin-left: 0 !important;
  margin-right: 0 !important;
}

.markdown-renderer .md-editor-preview > *:first-child,
.markdown-renderer .md-preview > *:first-child {
  margin-top: 0 !important;
}

.markdown-renderer .md-editor-preview > *:last-child,
.markdown-renderer .md-preview > *:last-child {
  margin-bottom: 0 !important;
}

.markdown-renderer .md-preview .paragraph {
  margin: 0.5em 0;
  line-height: 1.6;
}

.markdown-renderer .md-preview h1,
.markdown-renderer .md-preview h2,
.markdown-renderer .md-preview h3,
.markdown-renderer .md-preview h4,
.markdown-renderer .md-preview h5,
.markdown-renderer .md-preview h6 {
  margin: 0.8em 0 0.4em 0;
  font-weight: 600;
  line-height: 1.3;
}

.markdown-renderer .md-preview h1 { font-size: 1.25em; }
.markdown-renderer .md-preview h2 { font-size: 1.2em; }
.markdown-renderer .md-preview h3 { font-size: 1.15em; }
.markdown-renderer .md-preview h4 { font-size: 1em; }

.markdown-renderer .md-preview code {
  background: rgba(0, 0, 0, 0.06);
  padding: 0.2em 0.4em;
  border-radius: 4px;
  font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, monospace;
  font-size: 0.9em;
}

.markdown-renderer .md-preview pre {
  margin: 0.8em 0;
  border-radius: 8px;
  overflow-x: auto;
  overflow-y: hidden;
  max-width: 100%;
}

.markdown-renderer .md-preview pre code {
  background: transparent;
  padding: 0;
  display: block;
  overflow-x: auto;
  font-size: 0.85em;
  line-height: 1.5;
}

.markdown-renderer .md-preview blockquote {
  margin: 0.8em 0;
  padding: 0.5em 1em;
  border-left: 4px solid #ddd;
  background: rgba(0, 0, 0, 0.02);
  color: #666;
}

.markdown-renderer .md-preview ul,
.markdown-renderer .md-preview ol {
  margin: 0.5em 0;
  padding-left: 1.5em;
}

.markdown-renderer .md-preview li {
  margin: 0.3em 0;
}

.markdown-renderer .md-preview table {
  margin: 0.8em 0;
  border-collapse: collapse;
  width: 100%;
  display: block;
  overflow-x: auto;
  max-width: 100%;
}

.markdown-renderer .md-preview th,
.markdown-renderer .md-preview td {
  border: 1px solid #ddd;
  padding: 0.5em 0.8em;
  text-align: left;
}

.markdown-renderer .md-preview th {
  background: rgba(0, 0, 0, 0.03);
  font-weight: 600;
}

.markdown-renderer .md-preview a {
  color: #1890ff;
  text-decoration: none;
}

.markdown-renderer .md-preview a:hover {
  text-decoration: underline;
}

.markdown-renderer .md-preview img {
  max-width: 100%;
  border-radius: 4px;
}

.markdown-renderer .md-preview hr {
  margin: 1em 0;
  border: none;
  border-top: 1px solid #eee;
}

.markdown-renderer .md-preview .katex-block {
  margin: 0.8em 0;
  overflow-x: auto;
  overflow-y: hidden;
  text-align: center;
  max-width: 100%;
  display: block;
}

.markdown-renderer .md-preview .katex-block .katex {
  display: inline-block;
  text-align: left;
}

.markdown-renderer .md-preview .katex-display {
  margin: 0.8em 0;
  overflow-x: auto;
  overflow-y: hidden;
  max-width: 100%;
  display: block;
}

.markdown-renderer .md-preview .katex-display > .katex {
  display: inline-block;
  white-space: nowrap;
}

.markdown-renderer .md-preview p > .katex-display {
  overflow-x: auto;
  overflow-y: hidden;
  max-width: 100%;
}

.markdown-renderer .md-preview .katex-inline {
  font-size: 1em;
}

.markdown-renderer .md-preview .katex {
  font-size: 1.1em;
}

.markdown-renderer .md-preview .code-action {
  display: none !important;
}

.markdown-renderer .md-preview .code-header {
  display: none !important;
}
</style>
