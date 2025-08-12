'use client'

import * as React from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { AuthGuard } from '@/components/auth/auth-guard'
import { useAuthStore } from '@/stores/auth-store'
import { useToast } from '@/hooks/use-toast'
import { Eye, EyeOff, Mail, Lock, User, Building2, Github, Chrome } from 'lucide-react'

const registerSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  password: z.string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
    .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
    .regex(/[0-9]/, 'Password must contain at least one number'),
  confirmPassword: z.string(),
  organizationName: z.string().min(2, 'Organization name must be at least 2 characters').optional(),
  agreeToTerms: z.boolean().refine(val => val === true, 'You must agree to the terms of service'),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
})

type RegisterFormData = z.infer<typeof registerSchema>

export default function RegisterPage() {
  const [showPassword, setShowPassword] = React.useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = React.useState(false)
  const { register: registerUser, isLoading, error, clearError } = useAuthStore()
  const { toast } = useToast()

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
  })

  const password = watch('password')

  React.useEffect(() => {
    if (error) {
      toast({
        variant: 'destructive',
        title: 'Registration Failed',
        description: error,
      })
      clearError()
    }
  }, [error, toast, clearError])

  const onSubmit = async (data: RegisterFormData) => {
    try {
      await registerUser({
        email: data.email,
        password: data.password,
        organization_name: data.organizationName,
      })
      
      toast({
        variant: 'success',
        title: 'Welcome to LeanVibe!',
        description: 'Your account has been created successfully.',
      })
    } catch (error) {
      // Error is handled by the auth store and useEffect above
    }
  }

  const handleSSOLogin = (provider: 'google' | 'microsoft') => {
    toast({
      title: 'SSO Integration',
      description: `${provider} SSO will be available soon. Please use email registration for now.`,
    })
  }

  const getPasswordStrength = () => {
    if (!password) return { strength: 0, text: '' }
    
    let score = 0
    if (password.length >= 8) score++
    if (/[A-Z]/.test(password)) score++
    if (/[a-z]/.test(password)) score++
    if (/[0-9]/.test(password)) score++
    if (/[^A-Za-z0-9]/.test(password)) score++

    const strengths = [
      { strength: 0, text: 'Very Weak', color: 'bg-red-500' },
      { strength: 1, text: 'Weak', color: 'bg-red-400' },
      { strength: 2, text: 'Fair', color: 'bg-yellow-500' },
      { strength: 3, text: 'Good', color: 'bg-blue-500' },
      { strength: 4, text: 'Strong', color: 'bg-green-500' },
      { strength: 5, text: 'Very Strong', color: 'bg-green-600' },
    ]

    return strengths[score]
  }

  const passwordStrength = getPasswordStrength()

  return (
    <AuthGuard requireAuth={false}>
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-purple-50 dark:from-gray-900 dark:to-gray-800 p-4">
        <div className="w-full max-w-md">
          {/* Logo and Header */}
          <div className="text-center mb-8">
            <div className="mx-auto h-12 w-12 rounded-lg bg-gradient-to-r from-blue-600 to-purple-600 mb-4" />
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Join LeanVibe
            </h1>
            <p className="text-gray-600 dark:text-gray-300 mt-2">
              Start building MVPs with autonomous AI development
            </p>
          </div>

          <Card>
            <CardHeader className="space-y-1">
              <CardTitle className="text-2xl text-center">Create account</CardTitle>
              <CardDescription className="text-center">
                Enter your information to get started
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* SSO Buttons */}
              <div className="grid grid-cols-2 gap-3">
                <Button 
                  variant="outline" 
                  onClick={() => handleSSOLogin('google')}
                  disabled={isLoading}
                >
                  <Chrome className="h-4 w-4 mr-2" />
                  Google
                </Button>
                <Button 
                  variant="outline" 
                  onClick={() => handleSSOLogin('microsoft')}
                  disabled={isLoading}
                >
                  <Github className="h-4 w-4 mr-2" />
                  Microsoft
                </Button>
              </div>

              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <span className="w-full border-t" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-background px-2 text-muted-foreground">
                    Or continue with email
                  </span>
                </div>
              </div>

              {/* Registration Form */}
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                <Input
                  {...register('email')}
                  type="email"
                  label="Email"
                  placeholder="Enter your email"
                  error={errors.email?.message}
                  icon={<Mail className="h-4 w-4" />}
                  disabled={isLoading}
                />

                <Input
                  {...register('organizationName')}
                  type="text"
                  label="Organization Name (Optional)"
                  placeholder="Your company or project name"
                  error={errors.organizationName?.message}
                  icon={<Building2 className="h-4 w-4" />}
                  disabled={isLoading}
                />

                <div>
                  <div className="relative">
                    <Input
                      {...register('password')}
                      type={showPassword ? 'text' : 'password'}
                      label="Password"
                      placeholder="Create a strong password"
                      error={errors.password?.message}
                      icon={<Lock className="h-4 w-4" />}
                      disabled={isLoading}
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="absolute right-2 top-8 h-6 w-6"
                      onClick={() => setShowPassword(!showPassword)}
                    >
                      {showPassword ? (
                        <EyeOff className="h-4 w-4" />
                      ) : (
                        <Eye className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                  
                  {/* Password Strength Indicator */}
                  {password && (
                    <div className="mt-2 space-y-1">
                      <div className="flex justify-between text-xs">
                        <span>Password strength</span>
                        <span className={passwordStrength.strength >= 3 ? 'text-green-600' : 'text-red-600'}>
                          {passwordStrength.text}
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-1">
                        <div
                          className={`h-1 rounded-full transition-all ${'color' in passwordStrength ? passwordStrength.color : 'bg-gray-300'}`}
                          style={{ width: `${(passwordStrength.strength / 5) * 100}%` }}
                        />
                      </div>
                    </div>
                  )}
                </div>

                <div className="relative">
                  <Input
                    {...register('confirmPassword')}
                    type={showConfirmPassword ? 'text' : 'password'}
                    label="Confirm Password"
                    placeholder="Confirm your password"
                    error={errors.confirmPassword?.message}
                    icon={<Lock className="h-4 w-4" />}
                    disabled={isLoading}
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="absolute right-2 top-8 h-6 w-6"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  >
                    {showConfirmPassword ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </Button>
                </div>

                <div className="flex items-start space-x-2">
                  <input
                    {...register('agreeToTerms')}
                    type="checkbox"
                    id="agreeToTerms"
                    className="mt-1 rounded border-gray-300"
                  />
                  <label htmlFor="agreeToTerms" className="text-sm text-gray-600 dark:text-gray-300">
                    I agree to the{' '}
                    <Link href="/terms" className="text-blue-600 hover:text-blue-500">
                      Terms of Service
                    </Link>{' '}
                    and{' '}
                    <Link href="/privacy" className="text-blue-600 hover:text-blue-500">
                      Privacy Policy
                    </Link>
                  </label>
                </div>
                {errors.agreeToTerms && (
                  <p className="text-xs text-destructive">{errors.agreeToTerms.message}</p>
                )}

                <Button
                  type="submit"
                  className="w-full"
                  disabled={isLoading || isSubmitting}
                  loading={isLoading || isSubmitting}
                >
                  Create account
                </Button>
              </form>

              <div className="text-center text-sm">
                <span className="text-gray-600 dark:text-gray-300">
                  Already have an account?{' '}
                </span>
                <Link
                  href="/login"
                  className="text-blue-600 hover:text-blue-500 dark:text-blue-400 font-medium"
                >
                  Sign in
                </Link>
              </div>
            </CardContent>
          </Card>

          {/* Footer */}
          <div className="text-center mt-8 text-sm text-gray-500">
            <p>
              Protected by enterprise-grade security and privacy controls
            </p>
          </div>
        </div>
      </div>
    </AuthGuard>
  )
}