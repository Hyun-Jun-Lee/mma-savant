import { toast } from 'sonner'

interface ToastOptions {
  message: string
  description?: string
  duration?: number
}

export function showError({ message, description, duration = 5000 }: ToastOptions) {
  toast.error(message, { description, duration })
}

export function showWarning({ message, description, duration = 5000 }: ToastOptions) {
  toast.warning(message, { description, duration })
}

export function showSuccess({ message, description, duration = 3000 }: ToastOptions) {
  toast.success(message, { description, duration })
}
