export const formatDate = (dateString: string | null | undefined): string => {
  if (!dateString) return '-';
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch (error) {
    return '-';
  }
};

export const formatNumber = (num: number | string | null | undefined): string => {
  if (num === null || num === undefined || num === '-') return '-';
  return Number(num).toLocaleString('en-US');
};

