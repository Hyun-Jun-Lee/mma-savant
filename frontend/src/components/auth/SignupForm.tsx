"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { AuthApiService } from "@/services/authApi"
import { Eye, EyeOff, Loader2, Check, X } from "lucide-react"

interface SignupFormProps {
  onSuccess?: () => void
  onLoginClick?: () => void
}

interface PasswordStrength {
  hasLowercase: boolean
  hasUppercase: boolean
  hasNumber: boolean
  hasSpecial: boolean
  hasMinLength: boolean
}

export function SignupForm({ onSuccess, onLoginClick }: SignupFormProps) {
  const router = useRouter()
  const [isLoading, setIsLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    password: "",
    confirmPassword: "",
  })

  const checkPasswordStrength = (password: string): PasswordStrength => {
    return {
      hasLowercase: /[a-z]/.test(password),
      hasUppercase: /[A-Z]/.test(password),
      hasNumber: /\d/.test(password),
      hasSpecial: /[!@#$%^&*(),.?":{}|<>]/.test(password),
      hasMinLength: password.length >= 8,
    }
  }

  const getComplexityCount = (strength: PasswordStrength): number => {
    let count = 0
    if (strength.hasLowercase) count++
    if (strength.hasUppercase) count++
    if (strength.hasNumber) count++
    if (strength.hasSpecial) count++
    return count
  }

  const passwordStrength = checkPasswordStrength(formData.password)
  const complexityCount = getComplexityCount(passwordStrength)
  const isPasswordValid = passwordStrength.hasMinLength && complexityCount >= 3
  const doPasswordsMatch = formData.password === formData.confirmPassword && formData.confirmPassword !== ""

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
    setError(null)
  }

  const validateForm = (): string | null => {
    if (!formData.username || formData.username.length < 3) {
      return "사용자명은 3자 이상이어야 합니다."
    }
    if (!/^[a-zA-Z0-9_]+$/.test(formData.username)) {
      return "사용자명은 영문, 숫자, 언더스코어만 사용할 수 있습니다."
    }
    if (!isPasswordValid) {
      return "비밀번호는 8자 이상이며, 소문자/대문자/숫자/특수문자 중 3가지 이상을 포함해야 합니다."
    }
    if (!doPasswordsMatch) {
      return "비밀번호가 일치하지 않습니다."
    }
    return null
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    const validationError = validateForm()
    if (validationError) {
      setError(validationError)
      return
    }

    setIsLoading(true)

    try {
      await AuthApiService.signup({
        username: formData.username,
        email: formData.email || undefined,
        password: formData.password,
      })

      if (onSuccess) {
        onSuccess()
      } else {
        router.push("/chat")
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "회원가입에 실패했습니다.")
    } finally {
      setIsLoading(false)
    }
  }

  const StrengthIndicator = ({ met, label }: { met: boolean; label: string }) => (
    <div className={`flex items-center gap-1.5 text-xs ${met ? "text-green-400" : "text-zinc-500"}`}>
      {met ? <Check className="h-3 w-3" /> : <X className="h-3 w-3" />}
      <span>{label}</span>
    </div>
  )

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div className="p-3 text-sm text-red-500 bg-red-500/10 border border-red-500/20 rounded-lg">
          {error}
        </div>
      )}

      <div className="space-y-2">
        <Label htmlFor="username" className="text-zinc-300">
          사용자명 <span className="text-red-500">*</span>
        </Label>
        <Input
          id="username"
          name="username"
          type="text"
          placeholder="영문, 숫자, 언더스코어 (3자 이상)"
          value={formData.username}
          onChange={handleChange}
          required
          disabled={isLoading}
          className="bg-white/5 border-white/10 text-white placeholder:text-zinc-500"
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="email" className="text-zinc-300">
          이메일 <span className="text-zinc-500">(선택)</span>
        </Label>
        <Input
          id="email"
          name="email"
          type="email"
          placeholder="example@email.com"
          value={formData.email}
          onChange={handleChange}
          disabled={isLoading}
          className="bg-white/5 border-white/10 text-white placeholder:text-zinc-500"
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="password" className="text-zinc-300">
          비밀번호 <span className="text-red-500">*</span>
        </Label>
        <div className="relative">
          <Input
            id="password"
            name="password"
            type={showPassword ? "text" : "password"}
            placeholder="8자 이상, 복잡도 조건 충족"
            value={formData.password}
            onChange={handleChange}
            required
            disabled={isLoading}
            className="bg-white/5 border-white/10 text-white placeholder:text-zinc-500 pr-10"
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-white"
          >
            {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
        </div>

        {formData.password && (
          <div className="mt-2 p-3 bg-white/5 border border-white/10 rounded-lg space-y-2">
            <div className="text-xs text-zinc-400 mb-2">
              비밀번호 조건 (3가지 이상 충족 필요):
            </div>
            <div className="grid grid-cols-2 gap-2">
              <StrengthIndicator met={passwordStrength.hasMinLength} label="8자 이상" />
              <StrengthIndicator met={passwordStrength.hasLowercase} label="소문자" />
              <StrengthIndicator met={passwordStrength.hasUppercase} label="대문자" />
              <StrengthIndicator met={passwordStrength.hasNumber} label="숫자" />
              <StrengthIndicator met={passwordStrength.hasSpecial} label="특수문자" />
            </div>
            <div className={`text-xs mt-2 ${isPasswordValid ? "text-green-400" : "text-amber-400"}`}>
              {isPasswordValid
                ? "✓ 비밀번호 조건을 충족합니다."
                : `현재 ${complexityCount}/3 조건 충족`}
            </div>
          </div>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="confirmPassword" className="text-zinc-300">
          비밀번호 확인 <span className="text-red-500">*</span>
        </Label>
        <div className="relative">
          <Input
            id="confirmPassword"
            name="confirmPassword"
            type={showConfirmPassword ? "text" : "password"}
            placeholder="비밀번호를 다시 입력하세요"
            value={formData.confirmPassword}
            onChange={handleChange}
            required
            disabled={isLoading}
            className="bg-white/5 border-white/10 text-white placeholder:text-zinc-500 pr-10"
          />
          <button
            type="button"
            onClick={() => setShowConfirmPassword(!showConfirmPassword)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-white"
          >
            {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
        </div>
        {formData.confirmPassword && (
          <div className={`text-xs ${doPasswordsMatch ? "text-green-400" : "text-red-400"}`}>
            {doPasswordsMatch ? "✓ 비밀번호가 일치합니다." : "✗ 비밀번호가 일치하지 않습니다."}
          </div>
        )}
      </div>

      <Button
        type="submit"
        disabled={isLoading || !isPasswordValid || !doPasswordsMatch}
        className="w-full bg-red-600 hover:bg-red-700 text-white disabled:opacity-50"
      >
        {isLoading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            회원가입 중...
          </>
        ) : (
          "회원가입"
        )}
      </Button>

      {onLoginClick && (
        <p className="text-center text-sm text-zinc-400">
          이미 계정이 있으신가요?{" "}
          <button
            type="button"
            onClick={onLoginClick}
            className="text-red-500 hover:text-red-400 underline"
          >
            로그인
          </button>
        </p>
      )}
    </form>
  )
}
