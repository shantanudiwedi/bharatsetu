export const formatINR = (value: number | string | null | undefined): string => {
  const normalized = typeof value === 'string'
    ? value.replace(/^(?:₹|Rs\.?)\s*/i, '').replace(/,/g, '').trim()
    : value;
  const numeric = Number(normalized ?? 0);
  if (!Number.isFinite(numeric)) return '₹0';
  if (numeric <= 0) return '₹0';

  const abs = Math.abs(numeric);
  const formatter = new Intl.NumberFormat('en-IN', {
    maximumFractionDigits: 0,
  });

  const formatted = formatter.format(abs);
  return `₹${formatted}`;
};
