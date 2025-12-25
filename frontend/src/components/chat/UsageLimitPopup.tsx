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

export function UsageLimitPopup() {
  const { usageLimit, showUsageLimitPopup, setShowUsageLimitPopup } = useChatStore()

  if (!usageLimit) return null

  return (
    <Dialog open={showUsageLimitPopup} onOpenChange={setShowUsageLimitPopup}>
      <DialogContent className="sm:max-w-md bg-zinc-900 border-zinc-800">
        <DialogHeader className="text-center sm:text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-amber-500/20">
            <AlertTriangle className="h-6 w-6 text-amber-500" />
          </div>
          <DialogTitle className="text-xl text-white">
            일일 사용량 초과
          </DialogTitle>
          <DialogDescription className="text-zinc-400 mt-2">
            {usageLimit.error || "오늘의 사용량 한도에 도달했습니다."}
          </DialogDescription>
        </DialogHeader>

        <div className="mt-4 rounded-lg bg-zinc-800/50 p-4">
          <div className="flex justify-between items-center mb-2">
            <span className="text-zinc-400 text-sm">현재 사용량</span>
            <span className="text-white font-medium">
              {usageLimit.dailyRequests} / {usageLimit.dailyLimit}회
            </span>
          </div>
          <div className="w-full bg-zinc-700 rounded-full h-2">
            <div
              className="bg-amber-500 h-2 rounded-full transition-all"
              style={{ width: `${Math.min((usageLimit.dailyRequests / usageLimit.dailyLimit) * 100, 100)}%` }}
            />
          </div>
        </div>

        <p className="text-center text-zinc-500 text-sm mt-2">
          내일 자정(KST) 이후에 다시 이용해 주세요.
        </p>

        <DialogFooter className="mt-4">
          <Button
            onClick={() => setShowUsageLimitPopup(false)}
            className="w-full bg-zinc-700 hover:bg-zinc-600 text-white"
          >
            확인
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
