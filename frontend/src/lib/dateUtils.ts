// Format datetime for display (Bangkok timezone)
export function formatSessionTime(dateString: string): string {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return date.toLocaleString('th-TH', {
    timeZone: 'Asia/Bangkok',
    hour: '2-digit',
    minute: '2-digit',
    day: 'numeric',
    month: 'short',
    year: 'numeric'
  });
}

// Format time range
export function formatSessionRange(start: string, end?: string): string {
  const startTime = formatSessionTime(start);
  if (!end) return startTime;
  const endTime = formatSessionTime(end);
  return `${startTime} - ${endTime}`;
}

// Format date only
export function formatSessionDate(dateString: string): string {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return date.toLocaleDateString('th-TH', {
    timeZone: 'Asia/Bangkok',
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
}

// Format time only
export function formatSessionTimeOnly(dateString: string): string {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return date.toLocaleTimeString('th-TH', {
    timeZone: 'Asia/Bangkok',
    hour: '2-digit',
    minute: '2-digit'
  });
}

// Format time range for session display (HH:mm - HH:mm or just HH:mm)
export function formatTimeRange(start: string, end?: string): string {
  const startTime = formatSessionTimeOnly(start);
  if (!end) return startTime;
  const endTime = formatSessionTimeOnly(end);
  return `${startTime} - ${endTime}`;
}
