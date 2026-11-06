import { z } from 'zod';

// Pure functions: no file access, network, rendering, telemetry or credentials.
const samples = z.array(z.number().int().min(0).max(255)).min(1).max(256);
const codepoints = z.array(z.number().int().min(0).max(0x10ffff)
  .refine(n => n < 0xd800 || n > 0xdfff, 'Use Unicode scalar values, not surrogate halves.')).max(4096);
const compareInput = z.object({
  channel: z.enum(['alpha8', 'rgb8']),
  reference: samples.describe('Original 8-bit samples, in matching order; RGB means interleaved R,G,B.'),
  decoded: samples.describe('Samples from decoded output, at the same positions and times.'),
  tolerance: z.number().int().min(0).max(255).describe('The caller-selected maximum absolute sample error; no delivery standard is assumed.'),
}).strict().superRefine((v, c) => {
  if (v.reference.length !== v.decoded.length) c.addIssue({code:'custom', message:'Sample lengths must match.'});
  if (v.channel === 'rgb8' && v.reference.length % 3 !== 0) c.addIssue({code:'custom', message:'RGB sample length must be a multiple of three.'});
});
const fontInput = z.object({
  required: codepoints.describe('Unicode scalar values actually needed by the text.'),
  covered: codepoints.describe('The inspected cmap coverage of the registered candidate font or explicit fallback set.'),
}).strict();

export function compareSamples(raw: unknown) {
  const v = compareInput.parse(raw);
  const errors = v.reference.map((n, i) => Math.abs(n - v.decoded[i]!));
  const maxError = Math.max(...errors);
  return {
    status: maxError <= v.tolerance ? 'within_supplied_tolerance' : 'outside_supplied_tolerance',
    max_error: maxError, tolerance: v.tolerance, sample_count: errors.length,
    evidence: 'Arithmetic on caller-supplied samples; this tool did not read, render or decode media.',
    limitation: v.channel === 'alpha8'
      ? 'Does not establish RGB fidelity, higher-bit alpha precision, editor compatibility or whole-file correctness.'
      : 'Does not establish the cause, colour standard, visual acceptability, or whole-file correctness. Compare matching frame coordinates.',
    next_check: v.channel === 'alpha8'
      ? 'Check alpha exists before encoding and survives decoding; an opaque source cannot gain a useful mask through codec selection.'
      : 'Separate RGB/YUV conversion and range errors from metadata or player display differences. Do not assume retagging repairs wrong stored samples.',
    public_lookup_terms: v.channel === 'alpha8'
      ? 'FFmpeg ProRes 4444 transparent export alpha verification'
      : 'FFmpeg RGB to YUV BT709 color matrix conversion versus metadata tagging limited full range',
  };
}

export function fontCoverage(raw: unknown) {
  const v = fontInput.parse(raw), covered = new Set(v.covered);
  const missing = [...new Set(v.required)].filter(n => !covered.has(n)).sort((a,b) => a-b);
  return {
    status: missing.length ? 'missing_from_supplied_coverage' : 'covered_by_supplied_set',
    missing: missing.map(n => 'U+' + n.toString(16).toUpperCase().padStart(4, '0')),
    evidence: 'Set comparison on caller-supplied cmap data; no font file was read.',
    limitation: 'Coverage does not prove shaping, language-specific glyph forms, correct fallback selection, registration or successful rendering.',
    next_check: 'Use Kinetograph registerFont before layout and doctor plus a rendered still. Keep explicit font versions and licences; OS fallback is not assumed.',
    primary_reference: 'https://kinetograph.dev/docs/guides/agents/',
  };
}

export const tools = [
  {name:'compare_samples', description:'Check supplied 8-bit alpha or RGB export samples against an explicit tolerance. Diagnose a transparency or colour delivery check without reading files or calling a service.', input:compareInput, run:compareSamples},
  {name:'font_coverage', description:'Find required Unicode characters absent from supplied font cmap coverage before rendering. Does not claim shaping or operating-system fallback support.', input:fontInput, run:fontCoverage},
];
