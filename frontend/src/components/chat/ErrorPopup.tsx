"use client"

import { useChatStore } from "@/store/chatStore"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { AlertTriangle } from "lucide-react"

export function ErrorPopup() {
  const { errorInfo, showErrorPopup, setShowErrorPopup, setErrorInfo } = useChatStore()

  if (!errorInfo) return null

  const handleClose = () => {
    setShowErrorPopup(false)
    setErrorInfo(null)
  }

  return (
    <Dialog open={showErrorPopup} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md bg-zinc-900 border-zinc-800">
        <DialogHeader className="text-center sm:text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-red-500/20">
            <AlertTriangle className="h-6 w-6 text-red-500" />
          </div>
          <DialogTitle className="text-xl text-white">
            오류가 발생했습니다
          </DialogTitle>
          <DialogDescription className="text-zinc-400 mt-2">
            {errorInfo.message}
          </DialogDescription>
        </DialogHeader>

        <p className="text-center text-zinc-500 text-sm mt-2">
          잠시 후 다시 시도해 주세요.
        </p>

        <DialogFooter className="mt-4">
          <Button
            onClick={handleClose}
            className="w-full bg-zinc-700 hover:bg-zinc-600 text-white"
          >
            확인
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
