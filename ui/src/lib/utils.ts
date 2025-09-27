import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'
import { format, parseISO, parse } from 'date-fns'

export const cn = (...inputs: ClassValue[]) => {
  return twMerge(clsx(inputs))
}

export const formatDate = (isoDateString: string) => {
  try {
    const date = parseISO(isoDateString)
    return format(date, 'EEEE, MMM d, yyyy')
  } catch {
    return isoDateString
  }
}

export const formatTime = (isoTimeString: string) => {
  try {
    // Parse time string into a date object for formatting
    const parsed = parse(isoTimeString, 'HH:mm:ss', new Date())
    return format(parsed, 'h:mm a')
  } catch {
    return isoTimeString
  }
}

export const formatDateTime = (
  isoDateTimeString: string,
  formatString = "MMM d, yyyy 'at' h:mm a"
) => {
  try {
    const dateTime = parseISO(isoDateTimeString)
    return format(dateTime, formatString)
  } catch {
    return isoDateTimeString
  }
}

export const formatOptionalTime = (isoTimeString: string | null | undefined) => {
  if (!isoTimeString) {
    return 'N/A'
  }
  return formatTime(isoTimeString)
}

export const convertTo24Hour = (time12h: string) => {
  try {
    const parsed = parse(time12h, 'h:mm a', new Date())
    return format(parsed, 'HH:mm:ss')
  } catch {
    return time12h
  }
}
