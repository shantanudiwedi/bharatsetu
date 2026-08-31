export type DocStatus = 'verified' | 'failed' | 'pending';
export type RiskLevel = 'low' | 'medium' | 'high';
export type VerificationStatus = 'pending_review' | 'approved' | 'rejected' | 'flagged';

export interface DocCheck {
  name: string;
  status: DocStatus;
  source: string;
  detail: string;
}

export interface AuditEntry {
  source: string;
  label: string;
  status: 'pass' | 'fail' | 'checking';
  timestamp: string;
}

export interface VerificationRecord {
  id: string;
  vendorName: string;
  vendorId: string;
  category: string;
  bidAmount: string;
  submittedAt: string;
  riskLevel: RiskLevel;
  status: VerificationStatus;
  aiConfidence: number;
  aiRecommendation: string;
  aiSummary: string;
  documents: DocCheck[];
  auditTrail: AuditEntry[];
  officer?: string;
}

export const records: VerificationRecord[] = [
  {
    id: 'GEM-2026-04827',
    vendorName: 'Shree Lakshmi Industries Pvt Ltd',
    vendorId: 'UDYAM-MH-29-0048291',
    category: 'Industrial Machinery',
    bidAmount: '₹ 48,27,500',
    submittedAt: '2026-08-30 09:42 AM',
    riskLevel: 'high',
    status: 'flagged',
    aiConfidence: 87,
    aiRecommendation: 'Flag for manual review. GST registration shows address mismatch with Udyam certificate. EPFO establishment code could not be cross-verified.',
    aiSummary: '2 of 4 documents failed automated verification. Address on GST certificate (Pune) does not match Udyam registered address (Nagpur). Recommend officer request updated GST proof before approval.',
    documents: [
      { name: 'Udyam', status: 'verified', source: 'Udyam Portal (MSME)', detail: 'Registration valid. Classification: Manufacturing.' },
      { name: 'GST', status: 'failed', source: 'GST Network API', detail: 'Address mismatch: GST lists Pune, Udyam lists Nagpur.' },
      { name: 'PAN', status: 'verified', source: 'NSDL PAN Database', detail: 'PAN AABCDE1234F matches entity name.' },
      { name: 'EPFO', status: 'failed', source: 'EPFO Portal', detail: 'Establishment code not found for this vendor.' },
    ],
    auditTrail: [
      { source: 'Udyam Portal', label: 'MSME registration check', status: 'pass', timestamp: '09:42:14' },
      { source: 'GST Network', label: 'GSTIN validity + address', status: 'fail', timestamp: '09:42:18' },
      { source: 'NSDL', label: 'PAN-to-entity match', status: 'pass', timestamp: '09:42:21' },
      { source: 'EPFO Portal', label: 'Establishment code lookup', status: 'fail', timestamp: '09:42:26' },
      { source: 'AI Engine', label: 'Risk scoring + summary', status: 'pass', timestamp: '09:42:29' },
    ],
  },
  {
    id: 'GEM-2026-04826',
    vendorName: 'Bharat Tech Solutions LLP',
    vendorId: 'UDYAM-DL-09-0037112',
    category: 'IT Hardware & Networking',
    bidAmount: '₹ 12,40,000',
    submittedAt: '2026-08-30 09:28 AM',
    riskLevel: 'low',
    status: 'pending_review',
    aiConfidence: 96,
    aiRecommendation: 'Approve. All 4 documents verified successfully. Vendor has consistent procurement history across 14 prior GeM contracts with no compliance issues.',
    aiSummary: 'Clean profile. GST, PAN, Udyam, and EPFO all match. Prior contract performance rated satisfactory. No risk indicators detected.',
    documents: [
      { name: 'Udyam', status: 'verified', source: 'Udyam Portal (MSME)', detail: 'Valid. Classification: Service Enterprise.' },
      { name: 'GST', status: 'verified', source: 'GST Network API', detail: 'Active GSTIN. Address consistent with Udyam.' },
      { name: 'PAN', status: 'verified', source: 'NSDL PAN Database', detail: 'PAN matches LLP registration records.' },
      { name: 'EPFO', status: 'verified', source: 'EPFO Portal', detail: 'Establishment code active. 38 employees enrolled.' },
    ],
    auditTrail: [
      { source: 'Udyam Portal', label: 'MSME registration check', status: 'pass', timestamp: '09:28:10' },
      { source: 'GST Network', label: 'GSTIN validity + address', status: 'pass', timestamp: '09:28:13' },
      { source: 'NSDL', label: 'PAN-to-entity match', status: 'pass', timestamp: '09:28:15' },
      { source: 'EPFO Portal', label: 'Establishment code lookup', status: 'pass', timestamp: '09:28:18' },
      { source: 'AI Engine', label: 'Risk scoring + summary', status: 'pass', timestamp: '09:28:21' },
    ],
  },
  {
    id: 'GEM-2026-04825',
    vendorName: 'Green Earth Agro Supplies Co.',
    vendorId: 'UDYAM-KA-30-0091245',
    category: 'Agricultural Supplies',
    bidAmount: '₹ 3,85,200',
    submittedAt: '2026-08-30 08:55 AM',
    riskLevel: 'medium',
    status: 'pending_review',
    aiConfidence: 74,
    aiRecommendation: 'Review with caution. EPFO compliance pending — establishment code returned inactive status. Udyam classification changed in last 90 days.',
    aiSummary: '3 of 4 documents verified. EPFO establishment code marked inactive since June 2026. Vendor may have reduced workforce. Officer should confirm current operational capacity.',
    documents: [
      { name: 'Udyam', status: 'verified', source: 'Udyam Portal (MSME)', detail: 'Valid. Reclassified from Trading to Manufacturing (Jul 2026).' },
      { name: 'GST', status: 'verified', source: 'GST Network API', detail: 'Active. Address matches Udyam.' },
      { name: 'PAN', status: 'verified', source: 'NSDL PAN Database', detail: 'PAN matches entity name.' },
      { name: 'EPFO', status: 'pending', source: 'EPFO Portal', detail: 'Establishment code inactive since Jun 2026.' },
    ],
    auditTrail: [
      { source: 'Udyam Portal', label: 'MSME registration check', status: 'pass', timestamp: '08:55:02' },
      { source: 'GST Network', label: 'GSTIN validity + address', status: 'pass', timestamp: '08:55:06' },
      { source: 'NSDL', label: 'PAN-to-entity match', status: 'pass', timestamp: '08:55:09' },
      { source: 'EPFO Portal', label: 'Establishment code lookup', status: 'checking', timestamp: '08:55:12' },
    ],
  },
  {
    id: 'GEM-2026-04824',
    vendorName: 'National Steel Fabricators Unit',
    vendorId: 'UDYAM-GJ-19-0062387',
    category: 'Steel & Metal Works',
    bidAmount: '₹ 87,60,000',
    submittedAt: '2026-08-30 08:30 AM',
    riskLevel: 'high',
    status: 'flagged',
    aiConfidence: 81,
    aiRecommendation: 'Flag for manual review. PAN verification returned a name mismatch — registered entity name differs from bid submission name by 2 tokens. Possible shell entity.',
    aiSummary: 'PAN name mismatch detected: registered as "National Steel Fabricators" but bid submitted under "National Steel Fabricators Unit". GST and Udyam valid. Officer must confirm legal entity identity.',
    documents: [
      { name: 'Udyam', status: 'verified', source: 'Udyam Portal (MSME)', detail: 'Valid. Classification: Manufacturing.' },
      { name: 'GST', status: 'verified', source: 'GST Network API', detail: 'Active GSTIN. Address consistent.' },
      { name: 'PAN', status: 'failed', source: 'NSDL PAN Database', detail: 'Name mismatch: registered vs. bid name differ.' },
      { name: 'EPFO', status: 'verified', source: 'EPFO Portal', detail: 'Active. 124 employees enrolled.' },
    ],
    auditTrail: [
      { source: 'Udyam Portal', label: 'MSME registration check', status: 'pass', timestamp: '08:30:05' },
      { source: 'GST Network', label: 'GSTIN validity + address', status: 'pass', timestamp: '08:30:08' },
      { source: 'NSDL', label: 'PAN-to-entity match', status: 'fail', timestamp: '08:30:11' },
      { source: 'EPFO Portal', label: 'Establishment code lookup', status: 'pass', timestamp: '08:30:14' },
      { source: 'AI Engine', label: 'Risk scoring + summary', status: 'pass', timestamp: '08:30:17' },
    ],
  },
  {
    id: 'GEM-2026-04823',
    vendorName: 'MediCare Instruments Ltd',
    vendorId: 'UDYAM-TN-33-0014560',
    category: 'Medical Equipment',
    bidAmount: '₹ 22,15,800',
    submittedAt: '2026-08-30 08:12 AM',
    riskLevel: 'low',
    status: 'approved',
    aiConfidence: 98,
    aiRecommendation: 'Approved. All documents verified. Vendor holds valid CDSCO registration (cross-checked). 22 prior GeM contracts with 100% delivery rate.',
    aiSummary: 'Exemplary compliance profile. All 4 core documents verified. Additional CDSCO medical device license confirmed. No risk indicators.',
    documents: [
      { name: 'Udyam', status: 'verified', source: 'Udyam Portal (MSME)', detail: 'Valid. Classification: Manufacturing.' },
      { name: 'GST', status: 'verified', source: 'GST Network API', detail: 'Active. Address consistent.' },
      { name: 'PAN', status: 'verified', source: 'NSDL PAN Database', detail: 'PAN matches entity name.' },
      { name: 'EPFO', status: 'verified', source: 'EPFO Portal', detail: 'Active. 67 employees enrolled.' },
    ],
    auditTrail: [
      { source: 'Udyam Portal', label: 'MSME registration check', status: 'pass', timestamp: '08:12:03' },
      { source: 'GST Network', label: 'GSTIN validity + address', status: 'pass', timestamp: '08:12:06' },
      { source: 'NSDL', label: 'PAN-to-entity match', status: 'pass', timestamp: '08:12:09' },
      { source: 'EPFO Portal', label: 'Establishment code lookup', status: 'pass', timestamp: '08:12:12' },
      { source: 'CDSCO', label: 'Medical device license', status: 'pass', timestamp: '08:12:15' },
      { source: 'AI Engine', label: 'Risk scoring + summary', status: 'pass', timestamp: '08:12:18' },
    ],
    officer: 'R. Krishnan',
  },
  {
    id: 'GEM-2026-04822',
    vendorName: 'Vidya Educational Supplies Co.',
    vendorId: 'UDYAM-RJ-14-0078901',
    category: 'Educational Materials',
    bidAmount: '₹ 6,42,300',
    submittedAt: '2026-08-30 07:48 AM',
    riskLevel: 'medium',
    status: 'rejected',
    aiConfidence: 79,
    aiRecommendation: 'Reject. GST registration cancelled as of July 2026. Vendor is not eligible to bid on current GeM tenders per procurement guidelines.',
    aiSummary: 'GST registration status: Cancelled. Vendor cannot participate in tenders requiring active GSTIN. Udyam and PAN valid but GST failure is disqualifying.',
    documents: [
      { name: 'Udyam', status: 'verified', source: 'Udyam Portal (MSME)', detail: 'Valid. Classification: Trading.' },
      { name: 'GST', status: 'failed', source: 'GST Network API', detail: 'GSTIN cancelled effective Jul 2026.' },
      { name: 'PAN', status: 'verified', source: 'NSDL PAN Database', detail: 'PAN matches entity name.' },
      { name: 'EPFO', status: 'verified', source: 'EPFO Portal', detail: 'Active. 12 employees enrolled.' },
    ],
    auditTrail: [
      { source: 'Udyam Portal', label: 'MSME registration check', status: 'pass', timestamp: '07:48:04' },
      { source: 'GST Network', label: 'GSTIN validity + address', status: 'fail', timestamp: '07:48:07' },
      { source: 'NSDL', label: 'PAN-to-entity match', status: 'pass', timestamp: '07:48:10' },
      { source: 'EPFO Portal', label: 'Establishment code lookup', status: 'pass', timestamp: '07:48:13' },
      { source: 'AI Engine', label: 'Risk scoring + summary', status: 'pass', timestamp: '07:48:16' },
    ],
    officer: 'S. Meena',
  },
];

export const liveAuditFeed = [
  { id: 1, source: 'GST Network', action: 'GSTIN validity check', vendor: 'Shree Lakshmi Industries', status: 'fail', time: '09:42:18' },
  { id: 2, source: 'EPFO Portal', action: 'Establishment code lookup', vendor: 'Shree Lakshmi Industries', status: 'fail', time: '09:42:26' },
  { id: 3, source: 'AI Engine', action: 'Risk score computed: 87', vendor: 'Shree Lakshmi Industries', status: 'pass', time: '09:42:29' },
  { id: 4, source: 'Udyam Portal', action: 'MSME registration check', vendor: 'Bharat Tech Solutions', status: 'pass', time: '09:28:10' },
  { id: 5, source: 'GST Network', action: 'GSTIN validity check', vendor: 'Bharat Tech Solutions', status: 'pass', time: '09:28:13' },
  { id: 6, source: 'AI Engine', action: 'Risk score computed: 96', vendor: 'Bharat Tech Solutions', status: 'pass', time: '09:28:21' },
  { id: 7, source: 'NSDL', action: 'PAN-to-entity match', vendor: 'National Steel Fabricators', status: 'fail', time: '08:30:11' },
  { id: 8, source: 'EPFO Portal', action: 'Establishment code lookup', vendor: 'Green Earth Agro', status: 'checking', time: '08:55:12' },
  { id: 9, source: 'CDSCO', action: 'Medical device license', vendor: 'MediCare Instruments', status: 'pass', time: '08:12:15' },
  { id: 10, source: 'GST Network', action: 'GSTIN cancelled flag', vendor: 'Vidya Educational Supplies', status: 'fail', time: '07:48:07' },
];
