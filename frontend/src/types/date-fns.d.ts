declare module 'date-fns' {
  export function format(date: Date | number, format: string, options?: { locale?: any }): string;
  export function startOfMonth(date: Date | number): Date;
  export function endOfMonth(date: Date | number): Date;
  export function eachDayOfInterval(interval: { start: Date; end: Date }): Date[];
  export function isSameDay(dateLeft: Date | number, dateRight: Date | number): boolean;
  export function addMonths(date: Date | number, amount: number): Date;
  export function subMonths(date: Date | number, amount: number): Date;
  export function isToday(date: Date | number): boolean;
  export function formatDistanceToNow(date: Date | number, options?: { addSuffix?: boolean; locale?: any }): string;
}

declare module 'date-fns/locale' {
  export const th: any;
}
