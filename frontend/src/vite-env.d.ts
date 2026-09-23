/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_PMS_USERNAME?: string
  readonly VITE_PMS_PASSWORD?: string
  readonly VITE_DEDGE_USERNAME?: string
  readonly VITE_DEDGE_PASSWORD?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
