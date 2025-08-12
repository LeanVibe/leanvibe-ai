'use client'

import * as React from 'react'
import { z } from 'zod'
import { useRouter } from 'next/navigation'
import { useCreateInterview, useSubmitInterview } from '@/hooks/use-interviews'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'

const interviewSchema = z.object({
  business_idea: z.string().min(10),
  problem_statement: z.string().min(10),
  target_audience: z.string().min(3),
  value_proposition: z.string().min(10),
  core_features: z.string().min(3), // comma separated
})

export default function NewInterviewPage() {
  const router = useRouter()
  const createInterview = useCreateInterview()
  const submitInterview = useSubmitInterview()

  const [step, setStep] = React.useState(1)
  const [data, setData] = React.useState({
    business_idea: '',
    problem_statement: '',
    target_audience: '',
    value_proposition: '',
    core_features: '',
  })
  const [interviewId, setInterviewId] = React.useState<string | null>(null)

  const next = async () => {
    if (step === 1) setStep(2)
    else if (step === 2) setStep(3)
    else if (step === 3) {
      const parsed = interviewSchema.safeParse(data)
      if (!parsed.success) return
      const payload = {
        business_idea: data.business_idea,
        problem_statement: data.problem_statement,
        target_audience: data.target_audience,
        value_proposition: data.value_proposition,
        core_features: data.core_features.split(',').map(s => s.trim()).filter(Boolean),
      }
      const created = await createInterview.mutateAsync(payload)
      const id = (created as any).id || (created as any).data?.id
      setInterviewId(id)
      await submitInterview.mutateAsync(id)
      router.push('/dashboard')
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <h1 className="text-2xl font-semibold">Founder Interview</h1>
      <Card>
        <CardHeader>
          <CardTitle>Step {step} of 3</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {step === 1 && (
            <>
              <Input label="Business idea" value={data.business_idea} onChange={e => setData({ ...data, business_idea: e.target.value })} />
              <Input label="Problem statement" value={data.problem_statement} onChange={e => setData({ ...data, problem_statement: e.target.value })} />
            </>
          )}
          {step === 2 && (
            <>
              <Input label="Target audience" value={data.target_audience} onChange={e => setData({ ...data, target_audience: e.target.value })} />
              <Input label="Value proposition" value={data.value_proposition} onChange={e => setData({ ...data, value_proposition: e.target.value })} />
            </>
          )}
          {step === 3 && (
            <>
              <Input label="Core features (comma separated)" value={data.core_features} onChange={e => setData({ ...data, core_features: e.target.value })} />
            </>
          )}
          <div className="flex justify-end">
            <Button onClick={next}>{step < 3 ? 'Next' : 'Submit'}</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
