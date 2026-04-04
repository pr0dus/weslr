export default {
  // Structured data routing integration hint
  structuredData: {
    extensions: ['.json', '.yaml', '.yml', '.csv'],
    category: 'structured',
  },
  // File routing map — connects to weslr/file_router.py
  fileRouter: {
    pdf: { module: 'weslr/pdf_context', category: 'pdf' },
    structured: { module: 'weslr/structured_data', category: 'structured' },
    text: { module: 'weslr/file_ingestion', category: 'text' },
  },
  // Backend contract endpoints
  endpoints: {
    conversations: '/api/contract/conversations',
    continuityStatus: '/api/contract/continuity',
    fileRoute: '/api/contract/file-route',
    operatorSummary: '/api/contract/operator/summary',
    operatorVisibility: '/api/contract/operator/visibility',
  },
  // Operator panel visibility contract
  operator: {
    visibility: {
      endpoint: '/api/contract/operator/visibility',
      defaultValue: true, // Show panel by default in dev mode
    },
  },
  // Continuity snapshot endpoint
  continuity: {
    snapshot: '/api/contract/continuity',
    restore: '/api/contract/continuity',
  },
};
