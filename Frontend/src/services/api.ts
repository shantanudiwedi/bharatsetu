import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL
  || (import.meta.env.DEV ? 'http://127.0.0.1:8000/api' : '/api');

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export interface BidRecord {
  id: string;
  vendorName: string;
  vendor_id_code: string;
  category: string;
  bidAmount: string;
  submittedAt: string;
  riskLevel: 'low' | 'medium' | 'high';
  risk_score: number;
  compliance_score: number;
  status: 'draft' | 'processing' | 'pending_review' | 'approved' | 'rejected' | 'flagged';
  aiConfidence: number;
  aiRecommendation: string;
  aiSummary: string;
  documents: {
    id: string;
    name: string;
    document_type?: string;
    status: 'verified' | 'failed' | 'pending';
    source: string;
    detail: string;
  }[];
  audit_trail: {
    id?: string;
    source: string;
    label: string;
    vendor?: string;
    status: 'pass' | 'fail' | 'checking';
    timestamp: string;
    action?: string;
  }[];
  officer?: string;
  tender_title?: string;
  requirements?: {
    document_type: string;
    is_mandatory: boolean;
    description?: string;
  }[];
}

export interface DocumentRecord {
  id: string;
  bid_id: string;
  bid_reference: string;
  tender_id: string;
  tender_title: string;
  filename: string;
  document_type: string;
  upload_timestamp: string;
  document_status: string;
  verification_status: string;
  verification_result: string;
  extracted_fields_status: string;
  detail?: string;
  source?: string;
  file_available: boolean;
}

export interface DashboardMetrics {
  pending_review_count: number;
  approved_today_count: number;
  avg_verification_time: string;
  flagged_cases_count: number;
  total_bids_count: number;
  high_risk_count: number;
  compliance_rate_percent: number;
  risk_distribution: Record<string, number>;
  verification_status_distribution: Record<string, number>;
}

export const loginApi = async (email: string, password: string) => {
  const res = await api.post('/auth/login', { email, password });
  return res.data;
};

export const registerApi = async (data: {
  email: string;
  password: string;
  full_name: string;
  company_name: string;
  gstin?: string;
  pan?: string;
  cin?: string;
  udyam?: string;
  contact_phone?: string;
  address?: string;
}) => {
  const res = await api.post('/auth/register', data);
  return res.data;
};

export const fetchDashboardMetrics = async (): Promise<DashboardMetrics> => {
  const res = await api.get('/dashboard/metrics');
  return res.data;
};

export const fetchBids = async (params?: { search?: string; status_filter?: string; risk_filter?: string }): Promise<BidRecord[]> => {
  const res = await api.get('/bids', { params });
  return res.data;
};

export const fetchDocuments = async (params?: { search?: string }): Promise<DocumentRecord[]> => {
  const res = await api.get('/bids/documents', { params });
  return res.data;
};

export const fetchAuditEvents = async () => {
  const res = await api.get('/audit');
  return res.data;
};

export const approveBidApi = async (bidId: string, reason?: string) => {
  const res = await api.post(`/bids/${bidId}/approve`, { action: 'APPROVE', reason });
  return res.data;
};

export const rejectBidApi = async (bidId: string, reason: string) => {
  const res = await api.post(`/bids/${bidId}/reject`, { action: 'REJECT', reason });
  return res.data;
};

export const escalateBidApi = async (bidId: string, reason: string) => {
  const res = await api.post(`/bids/${bidId}/escalate`, { action: 'ESCALATE', reason });
  return res.data;
};

export const uploadBidDocument = async (bidId: string, file: File, documentType?: string) => {
  const formData = new FormData();
  formData.append('file', file);
  if (documentType) {
    formData.append('document_type', documentType);
  }
  const res = await api.post(`/bids/${bidId}/documents`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return res.data;
};

export const viewDocumentApi = async (docId: string) => {
  // Open the tab during the click handler so browser popup blockers do not
  // reject the preview after the API request completes.
  const previewWindow = window.open('', '_blank');
  try {
    const res = await api.get(`/bids/documents/${docId}/view`, { responseType: 'blob' });
    const contentType = (res.headers['content-type'] as string) || 'application/pdf';
    const blob = new Blob([res.data], { type: contentType });
    const url = window.URL.createObjectURL(blob);
    if (previewWindow) {
      previewWindow.location.href = url;
    } else {
      const link = document.createElement('a');
      link.href = url;
      link.target = '_blank';
      link.rel = 'noopener';
      link.click();
    }
    setTimeout(() => window.URL.revokeObjectURL(url), 15000);
  } catch (error: any) {
    previewWindow?.close();
    console.error("View Document Error:", error?.response?.data || error);
    throw error;
  }
};

export const downloadDocumentApi = async (docId: string, filename?: string) => {
  try {
    const res = await api.get(`/bids/documents/${docId}/view`, { responseType: 'blob' });
    const contentType = (res.headers['content-type'] as string) || 'application/pdf';
    const blob = new Blob([res.data], { type: contentType });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename || 'document.pdf';
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    }, 1000);
  } catch (error: any) {
    console.error("Download Document Error:", error?.response?.data || error);
    throw error;
  }
};

export const downloadComplianceReportApi = async (bidId: string) => {
  const res = await api.get(`/reports/bids/${bidId}`, { responseType: 'blob' });
  const contentType = String(res.headers['content-type'] || '').toLowerCase();
  const firstBytes = new Uint8Array(await res.data.slice(0, 5).arrayBuffer());
  const pdfSignature = String.fromCharCode(...firstBytes) === '%PDF-';
  if (!contentType.includes('application/pdf') || !pdfSignature) {
    throw new Error('The compliance report response was not a valid PDF.');
  }
  const blob = new Blob([res.data], { type: 'application/pdf' });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `BharatSetu_Compliance_Report_${bidId}.pdf`;
  document.body.appendChild(link);
  link.click();
  setTimeout(() => {
    window.URL.revokeObjectURL(url);
    document.body.removeChild(link);
  }, 1000);
};

export const triggerBidVerification = async (bidId: string) => {
  const res = await api.post(`/bids/${bidId}/verify`);
  return res.data;
};

export const fetchTenders = async () => {
  const res = await api.get('/tenders');
  return res.data;
};

export const createTenderApi = async (tenderData: any) => {
  const res = await api.post('/tenders', tenderData);
  return res.data;
};

export const updateTenderDeadlineApi = async (tenderId: string, bidDeadline: string) => {
  const res = await api.patch(`/tenders/${tenderId}/deadline`, { bid_deadline: bidDeadline });
  return res.data;
};

export const createBidApi = async (bidData: any) => {
  const res = await api.post('/bids', bidData);
  return res.data;
};

export const fetchVendors = async () => {
  const res = await api.get('/vendors');
  return res.data;
};

// --- Notifications ---
export const fetchNotifications = async () => {
  const res = await api.get('/notifications');
  return res.data;
};

export const fetchUnreadNotificationCount = async () => {
  const res = await api.get('/notifications/unread-count');
  return res.data;
};

export const markNotificationRead = async (id: string) => {
  const res = await api.post(`/notifications/${id}/read`);
  return res.data;
};

export const markAllNotificationsRead = async () => {
  const res = await api.post('/notifications/read-all');
  return res.data;
};

// --- Support ---
export const submitSupportTicket = async (subject: string, description: string) => {
  const res = await api.post('/support', { subject, description });
  return res.data;
};
