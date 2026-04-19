import { z } from 'zod'

// ─── Paper ───────────────────────────────────────────────────────────────────

export const PaperSchema = z.object({
  pmid: z.string(),
  pmc_id: z.string().nullable(),
  title: z.string(),
  authors: z.array(z.string()),
  journal: z.string().nullable(),
  year: z.number().nullable(),
  abstract: z.string().nullable(),
  full_text: z.string().nullable(),
  doi: z.string().nullable(),
  url: z.string().nullable(),
  abbreviations: z.record(z.string()),
})

export const AbbreviationPaperRefSchema = z.object({
  paper_index: z.number(),
  pmid: z.string(),
  paper_title: z.string(),
})

export const AbbreviationMeaningSchema = z.object({
  full_form: z.string(),
  papers: z.array(AbbreviationPaperRefSchema),
})

export const AbbreviationBankSchema = z.record(z.array(AbbreviationMeaningSchema))

// ─── SSE event payloads ───────────────────────────────────────────────────────

export const SSEKeywordsDataSchema = z.object({
  keywords: z.array(z.string()),
})

export const SSEPapersDataSchema = z.object({
  count: z.number(),
  papers: z.array(
    z.object({
      pmid: z.string(),
      title: z.string(),
      authors: z.array(z.string()),
      year: z.number().nullable(),
    })
  ),
})

export const SSEAnswerDataSchema = z.object({
  chunk: z.string(),
})

export const SSECompleteDataSchema = z.object({
  papers: z.array(
    z.object({
      pmid: z.string(),
      pmc_id: z.string().nullable(),
      title: z.string(),
      authors: z.array(z.string()),
      journal: z.string().nullable(),
      year: z.number().nullable(),
      abstract: z.string().nullable(),
      doi: z.string().nullable(),
      url: z.string().nullable(),
      index: z.number(),
      citation: z.string(),
    })
  ),
  abbreviation_bank: AbbreviationBankSchema,
})

export const SSEErrorDataSchema = z.object({
  error: z.string(),
})

// ─── Health check ─────────────────────────────────────────────────────────────

export const HealthCheckSchema = z.object({
  status: z.string(),
  version: z.string(),
  timestamp: z.string().optional(),
})

// ─── Inferred types (use these instead of the raw API types where runtime
//     validation is needed) ───────────────────────────────────────────────────

export type ValidatedPaper = z.infer<typeof PaperSchema>
export type ValidatedHealthCheck = z.infer<typeof HealthCheckSchema>