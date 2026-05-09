const config = {
  // Product mode contract: first public UX target is read-only demo mode.
  productMode: 'public_demo_readonly',

  features: {
    chat: true,
    onboarding: false,
    memoryWrites: false,
    fileUpload: false,
    operatorPanel: false,
    proposalReview: false,
    deploymentControls: false,
    billing: false,
    organizationAdmin: false,
    showReadOnlyBanner: true,
    showLimitationsFooter: true,
    showExamplePrompts: true,
  },

  publicDemo: {
    readOnly: true,
    label: 'Read-only WESLR demo',
    subtitle:
      'This demo can explain WESLR and show selected safe workflows. It does not write memory, upload files, execute actions, or expose operator controls.',
  },

  // Structured data routing integration hint.
  // Disabled in public_demo_readonly mode by features.fileUpload=false.
  structuredData: {
    extensions: ['.json', '.yaml', '.yml', '.csv'],
    category: 'structured',
  },

  // File routing map — connects to weslr/file_router.py when enabled in non-public modes.
  fileRouter: {
    pdf: { module: 'weslr/pdf_context', category: 'pdf' },
    structured: { module: 'weslr/structured_data', category: 'structured' },
    text: { module: 'weslr/file_ingestion', category: 'text' },
  },

  // Backend contract endpoints.
  endpoints: {
    conversations: '/api/contract/conversations',
    continuityStatus: '/api/contract/continuity',
    fileRoute: '/api/contract/file-route',
    operatorSummary: '/api/contract/operator/summary',
    operatorVisibility: '/api/contract/operator/visibility',
  },

  // Operator panel visibility contract.
  // Public demo must never expose this panel by default.
  operator: {
    visibility: {
      endpoint: '/api/contract/operator/visibility',
      defaultValue: false,
    },
  },

  // Continuity snapshot endpoint.
  continuity: {
    snapshot: '/api/contract/continuity',
    restore: '/api/contract/continuity',
  },
};

export default config;
